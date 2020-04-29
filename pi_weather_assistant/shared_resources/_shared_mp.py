# shared_mp.py
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
"""This module contains shared classes use for communication between
processes."""


class _AemetShared():
    def __init__(self, manager):
        self.radar_ready = manager.Event()
        self.radar_lock = manager.Lock()
        self.forecast = manager.dict()
        self.forecast_ready = manager.Event()
        self.forecast_lock = manager.Lock()


class _SensorShared():
    def __init__(self, manager):
        self.sensor_variables = manager.dict()
        self.sensor_variables["Temperature"] = [0.0]
        self.sensor_variables["Humidity"] = [0.0]
        self.sensor_variables["Timestamp"] = ['2020-01-01T00:00:01']

        self.sensor_stadistics = manager.dict()
        self.sensor_stadistics["Current temperature"] = 0.0
        self.sensor_stadistics["Max temperature"] = 0.0
        self.sensor_stadistics["Min temperature"] = 0.0
        self.sensor_stadistics["Current humidity"] = 0.0
        self.sensor_stadistics["Max humidity"] = 0.0
        self.sensor_stadistics["Min humidity"] = 0.0

        self.sensor_lock = manager.Lock()
        self.sensor_ready = manager.Event()


class _SheetShared():
    def __init__(self, manager):
        self.sheet_variables = manager.dict()
        self.sheet_variables["Temperature"] = [0.0]
        self.sheet_variables["Humidity"] = [0.0]
        self.sheet_variables["Timestamp"] = ['2020-01-01T00:00:01']
        self.sheet_variables["Pressure"] = [1013.25]

        self.sheet_stadistics = manager.dict()
        self.sheet_stadistics["Current temperature"] = 0.0
        self.sheet_stadistics["Max temperature"] = 0.0
        self.sheet_stadistics["Min temperature"] = 0.0
        self.sheet_stadistics["Current humidity"] = 0.0
        self.sheet_stadistics["Max humidity"] = 0.0
        self.sheet_stadistics["Min humidity"] = 0.0
        self.sheet_stadistics["Current pressure"] = 1013.25

        self.sheet_ready = manager.Event()
        self.sheet_lock = manager.Lock()
