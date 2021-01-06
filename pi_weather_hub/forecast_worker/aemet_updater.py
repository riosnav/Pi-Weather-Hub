# aemet_updater.py
# Copyright (C) 2020  Francisco de los Ríos Navarrete
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program. If not, see
# <https://www.gnu.org/licenses/>.
"""Module container for the AemetUpdater class."""

# stdlib
import datetime
import math
import os
import time
import sys

# pip
import requests

# module parameters
from forecast_worker._aemet_api_key import AEMET_API_KEY
MUNICIPIO_ID = "29067"
RADAR_ID = "ml"
MAX_RADAR_FILES = 12
UPDATE_PERIOD = 10*60


class AemetUpdater():
    """
    The AemetUpdater object is a multiprocessing oriented class which
    will periodically fetch and store weather data from AEMET using
    AEMET's API.

    AemetUpdater will store forecast data inside a shared dictionary
    and radar images inside a folder (./resources).

    ...

    Attributes
    ----------
    forecast : multiprocessing.Manager().Dict()
        Regional and national weather forecasts from AEMET API json.
    forecast_ready : multiprocessing.Manager().Event()
        Event used to signal that forecast data has been fetched
        successfully.
    forecast_lock : multiprocessing.Manager().Lock()
        Lock used to prevent coordination issues.
    radar_ready : multiprocessing.Manager().Event()
        Event used to signal that new radar data that has been fetched
        successfully.
    radar_lock : multiprocessing.Manager().Lock()
        Lock used to prevent coordination issues.

    Methods
    -------
    run():
        Fetches and updates data periodically.
    """

    def __init__(self, aemet_shared):
        """
        Construct all the necessary attributes for the AemetUpdater 
        object.

        Parameters
        ----------
            aemet_shared : object
                Manager object containing the shared variables.
        """
        self.forecast = aemet_shared.forecast
        self.forecast_ready = aemet_shared.forecast_ready
        self.forecast_lock = aemet_shared.forecast_lock
        self.radar_ready = aemet_shared.radar_ready
        self.radar_lock = aemet_shared.radar_lock

    def run(self):
        """Fetch and update data periodically."""
        self._add_requests_cipherset()
        self._update_forecast()
        self._update_radar_files()
        self.radar_ready.set()

        while True:
            self._update_forecast()
            self._update_radar_files()
            time.sleep(UPDATE_PERIOD)

    def _add_requests_cipherset(self):
        # Add alternive cipher set to prevent 'dh key too small' error.
        # Source:
        # https://www.codesd.com/item/python-requests-exceptions-sslerror-key-dh-too-small.html
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += "HIGH:!DH:!aNULL"
        try:
            requests.packages.urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST += "HIGH:!DH:!aNULL"
        except AttributeError:
            # no pyopenssl support used / needed / available
            pass

    def _update_forecast(self):
        # Fetch forecast data. If the request is successfull it will update the shared dictionary.
        with self.forecast_lock:
            temp_daily = self._aemet_request(
                "https://opendata.aemet.es/opendata/api/prediccion/especifica/municipio/diaria/"
                + MUNICIPIO_ID)
            temp_hourly = self._aemet_request(
                "https://opendata.aemet.es/opendata/api/prediccion/especifica/municipio/horaria/"
                + MUNICIPIO_ID)

            if (temp_daily is not None):
                self.forecast['daily'] = temp_daily.json()[0]
            if (temp_hourly is not None):
                self.forecast['hourly'] = temp_hourly.json()[0]
            if (temp_daily is not None) or (temp_hourly is not None):
                self.forecast_ready.set()

    def _update_radar_files(self):
        # Manage radar data updates.
        with self.radar_lock:
            file_saved = self._radar_files_manager(
                "https://opendata.aemet.es/opendata/api/red/radar/regional/" + RADAR_ID,
                "./shared_resources/_regional_radar", self._file_timestamp(),
                MAX_RADAR_FILES, False)
            if file_saved:
                _ = self._radar_files_manager(
                    "https://opendata.aemet.es/opendata/api/red/radar/nacional",
                    "./shared_resources/_national_radar", self._file_timestamp(),
                    MAX_RADAR_FILES, True)
                self.radar_ready.set()

    def _aemet_request(self, url):
        # Request to AEMET'S API.
        # Based on:
        # https://opendata.aemet.es/centrodedescargas/ejemProgramas
        querystring = {"api_key": AEMET_API_KEY}
        headers = {
            'cache-control': "no-cache"
        }
        try:
            response = requests.get(url, headers=headers, params=querystring)
            if response.status_code == 200:
                response_dict = response.json()
                data = requests.get(response_dict['datos'], headers=headers, params=querystring)
                if data.status_code == 200:
                    output = data
                else:
                    output = None
            else:
                output = None
        except (requests.exceptions.ConnectionError, KeyError, requests.exceptions.ChunkedEncodingError) as e:
            print(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S - "), end='', flush=True)
            print(e, file=sys.stderr, flush=True)
            output = None
        finally:
            return output

    def _file_timestamp(self):
        # Calculate radar timestamp. Using regional radar as reference (20 minutes delay).
        timestamp_rounded = datetime.datetime.now().replace(
            minute=math.floor(datetime.datetime.now().minute/10)*10)
        timestamp_str = (timestamp_rounded - datetime.timedelta(minutes=20)). \
            strftime("%Y-%m-%d %H-%M")
        return timestamp_str

    def _radar_files_manager(self, url, resource_path, filename, max_files, do_not_check_duplicate):
        # Save and remove radar image file as necessary.
        data = self._aemet_request(url)
        file_saved = False

        if data is not None:
            files = sorted([(resource_path + "/" + i) for i in os.listdir(resource_path)])

            if len(files) == 0:
                with open(resource_path + "/" + filename + ".gif", 'wb') as f:
                    f.write(data.content)
                file_saved = True
            else:
                # Checks if the recently fetched data is the same or not
                # than the latest image.
                with open(files[-1], 'rb') as f:
                    not_updated = (f.read() == data.content)

                if ((not not_updated) or do_not_check_duplicate):
                    if len(files) >= max_files:
                        os.remove(files[0])

                    with open(resource_path + "/" + filename + ".gif", 'wb') as f:
                        f.write(data.content)
                    file_saved = True
                else:
                    file_saved = False

        return file_saved
