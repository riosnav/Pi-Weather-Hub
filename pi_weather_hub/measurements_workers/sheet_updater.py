# sheet_updater.py
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
"""Module container for the SheetUpdater class."""

# stdlib
import datetime
import time
from socket import timeout, gaierror
import sys

# pip installed
from httplib2 import ServerNotFoundError
from googleapiclient.errors import HttpError
import numpy as np

# app modules
from measurements_workers.measurements_modules.google_sheets_api_request import google_sheets_api_request
from measurements_workers._spreadsheet_id import SPREADSHEET_ID, RANGE_NAME

SPREADSHEET_ID = "1rAtGo0rC1WpK227XKsNmNyOnRssKjW2a5ER7zkIy2vg"
RANGE_NAME = "Procesamiento!A2:D"
UPDATE_PERIOD = 5*60

class SheetUpdater():
    """
    The SheetUpdater object is a multiprocessing oriented class which
    will periodically fetch and store weather data from a Google Sheets
    spreadsheet.

    The desired range consist of a series of rows with 4 columns,
    containing data (temperature, humidity, pressure) roughly from the
    last 7 days in 15 minutes intervals. A typical example would be:
    1/20/2020 0:01:01, 20.5, 50.8, 1013.25

    ...

    Attributes
    ----------
    sheet_variables : multiprocessing.Manager().Dict()
        Formatted data fetched from the sheet.
    sheet_stadistics : multiprocessing.Manager().Dict()
        Various stadistic values (current, max. and min. temperature,
        humidity and pressure values in last 24 hours).
    sheet_ready : multiprocessing.Manager().Event()
        Event used to signal that data that has been fetched
        successfully.
    sheet_lock : multiprocessing.Manager().Lock()
        Lock used to prevent coordination issues.

    Methods
    -------
    run():
        Fetches and updates data periodically.
    """

    def __init__(self, sheet_shared):
        """
        Construct all the necessary attributes for the SheetUpdater 
        object.

        Parameters
        ----------
            sheet_shared : object
                Manager object containing the shared variables.
        """
        self.sheet_variables = sheet_shared.sheet_variables
        self.sheet_stadistics = sheet_shared.sheet_stadistics
        self.sheet_ready = sheet_shared.sheet_ready
        self.sheet_lock = sheet_shared.sheet_lock

    def run(self):
        """Fetch and update data periodically."""
        while True:
            with self.sheet_lock:
                try:
                    values = google_sheets_api_request(SPREADSHEET_ID, RANGE_NAME)
                    self._store_values(values)
                    self._process_stadistics()
                except (ServerNotFoundError, HttpError, timeout, gaierror) as e:
                    print(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S - "),
                          end='', flush=True)
                    print(e, file=sys.stderr, flush=True)
                    pass
                self.sheet_ready.set()
            time.sleep(UPDATE_PERIOD)

    def _store_values(self, values):
        # Format the fetched values and store them in the shared variables.
        for i, date in enumerate(values[0]):
            values[0][i] = datetime.datetime.strptime(date, "%m/%d/%Y %H:%M:%S").isoformat()
        self.sheet_variables['Timestamp'] = values[0]
        self.sheet_variables['Temperature'] = np.array(values[1], dtype='float64').tolist()
        self.sheet_variables['Humidity'] = np.array(values[2], dtype='float64').tolist()
        self.sheet_variables['Pressure'] = np.divide(
            np.array(values[3], dtype='float64'), 100).tolist()

    def _process_stadistics(self):
        # Generate useful data from the values.
        self.sheet_stadistics['Current temperature'] = self.sheet_variables['Temperature'][0]
        self.sheet_stadistics['Current humidity'] = self.sheet_variables['Humidity'][0]
        self.sheet_stadistics['Current pressure'] = self.sheet_variables['Pressure'][0]

        dates = np.array(self.sheet_variables['Timestamp'], dtype='datetime64')
        last_24h = dates[dates > dates[0] - np.timedelta64(1, 'D')]

        np_temperature = np.array(self.sheet_variables['Temperature'])
        self.sheet_stadistics['Max temperature'] = np.amax(np_temperature[0:len(last_24h)])
        self.sheet_stadistics['Min temperature'] = np.amin(np_temperature[0:len(last_24h)])

        np_humidity = np.array(self.sheet_variables['Humidity'])
        self.sheet_stadistics['Max humidity'] = np.amax(np_humidity[0:len(last_24h)])
        self.sheet_stadistics['Min humidity'] = np.amin(np_humidity[0:len(last_24h)])