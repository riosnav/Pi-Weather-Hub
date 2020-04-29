# sensor_updater.py
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
"""Module container for the SensorUpdater class."""

# stdlib
import csv
import datetime
import time

# pip
import board
import busio
import adafruit_sht31d
import numpy as np

# MODULE_VARIABLES
CSV_PATH = "./measurements_workers/measurements_resources/local_measurements.csv"
UPDATE_PERIOD = 10*60


class SensorUpdater():
    """
    The SensorUpdater object is a multiprocessing oriented class which
    will periodically measure and store ambient temperature and relative
    humidity from a Adafruit SHT31-D sensor.

    ...

    Attributes
    ----------
    sensor_variables : multiprocessing.Manager().Dict()
        Formatted data fetched from the sensor.
    sensor_stadistics : multiprocessing.Manager().Dict()
        Various stadistic values (current, max. and min. temperature
        and humidity values in last 24 hours).
    sensor_ready : multiprocessing.Manager().Event()
        Event used to signal that data that has been fetched
        successfully.
    sensor_lock : multiprocessing.Manager().Lock()
        Lock used to prevent coordination issues.

    Methods
    -------
    run():
        Fetches and updates data periodically.
    """

    def __init__(self, sensor_shared):
        """
        Construct all the necessary attributes for the SensorUpdater 
        object.

        Parameters
        ----------
            sensor_shared : object
                Manager object containing the shared variables.
        """
        self.sensor_variables = sensor_shared.sensor_variables
        self.sensor_stadistics = sensor_shared.sensor_stadistics
        self.sensor_ready = sensor_shared.sensor_ready
        self.sensor_lock = sensor_shared.sensor_lock

    def run(self):
        """Fetch and update data periodically."""
        while True:
            previous_sensor_data = self._read_csv(CSV_PATH)
            current_reading = self._read_sensor()
            sensor_data = self._combine_and_filter_data(current_reading, previous_sensor_data)
            self._save_data_to_csv(CSV_PATH, sensor_data)

            np_sensor_data = np.array(sensor_data).T
            with self.sensor_lock:
                self.sensor_variables['Timestamp'] = np_sensor_data[0, :].tolist()
                self.sensor_variables['Temperature'] = np_sensor_data[1, :].astype(float).tolist()
                self.sensor_variables['Humidity'] = np_sensor_data[2, :].astype(float).tolist()
                self._process_stadistics()
                self.sensor_ready.set()
            time.sleep(UPDATE_PERIOD)

    def _read_csv(self, path):
        try:
            with open(path, newline="") as f:
                reader = csv.reader(f)
                sensor_data = list(reader)
        except FileNotFoundError:
            sensor_data = list()
        return sensor_data

    def _save_data_to_csv(self, path, data):
        with open(path, 'w+', newline="") as f:
            writer = csv.writer(f)
            writer.writerows(data)

    def _read_sensor(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        sensor = adafruit_sht31d.SHT31D(i2c)

        current_time = datetime.datetime.now().replace(microsecond=0).isoformat()
        current_temp = round(sensor.temperature, 1)
        current_hum = round(sensor.relative_humidity, 1)
        return [current_time, current_temp, current_hum]

    def _combine_and_filter_data(self, current_reading, previous_sensor_data):
        # Add the new reading at the top of the previous list. All
        # values older than 7 days are deleted.
        temp_sensor_data = previous_sensor_data
        temp_sensor_data.insert(0, current_reading)

        dates = np.array([entry[0] for entry in temp_sensor_data], dtype='datetime64')
        last_7days = dates[dates > dates[0] - np.timedelta64(7, 'D')]

        return temp_sensor_data[0:len(last_7days)]

    def _process_stadistics(self):
        # Generate useful data from the values.
        self.sensor_stadistics['Current temperature'] = self.sensor_variables['Temperature'][0]
        self.sensor_stadistics['Current humidity'] = self.sensor_variables['Humidity'][0]

        dates = np.array(self.sensor_variables['Timestamp'], dtype='datetime64')
        last_24h = dates[dates > dates[0] - np.timedelta64(1, 'D')]

        np_temperature = np.array(self.sensor_variables['Temperature'])
        self.sensor_stadistics['Max temperature'] = np.amax(np_temperature[0:len(last_24h)])
        self.sensor_stadistics['Min temperature'] = np.amin(np_temperature[0:len(last_24h)])

        np_humidity = np.array(self.sensor_variables['Humidity'])
        self.sensor_stadistics['Max humidity'] = np.amax(np_humidity[0:len(last_24h)])
        self.sensor_stadistics['Min humidity'] = np.amin(np_humidity[0:len(last_24h)])
