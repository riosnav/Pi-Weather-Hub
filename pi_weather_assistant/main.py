# main.py
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
"""
Pi Weather Hub

This is the main file of the Pi Weather Hub app. Here all shared
variables are created and the different processes are started.

More information about this app can be found in the README file.
"""
# Setting MEASUREMENTS_INTEGRATION_ACTIVATED to False will allow you to run this app if you don't
# have the sensor or the Google Sheet used in the Measurements tab.
MEASUREMENTS_INTEGRATION_ACTIVATED = True

# stdlib
import multiprocessing as mp
import os
import sys
import time

# pip
from PyQt5 import QtWidgets

# app modules
from gui.interface import Ui
from forecast_worker.aemet_updater import AemetUpdater
from shared_resources._shared_mp import _AemetShared, _SensorShared, _SheetShared

if MEASUREMENTS_INTEGRATION_ACTIVATED:
    from measurements_workers.sensor_updater import SensorUpdater
    from measurements_workers.sheet_updater import SheetUpdater


# MODULE_VARIABLES

if __name__ == '__main__':
    # Set main.py directory as current working directory
    os.chdir(os.path.dirname((os.path.abspath(sys.argv[0]))))

    try:
        os.makedirs("./shared_resources/_national_radar")
        os.makedirs("./shared_resources/_regional_radar")
    except FileExistsError:
        pass

    # Multiprocess set up
    mp.set_start_method('spawn')
    manager = mp.Manager()

    # AEMET's API process
    aemet_shared = _AemetShared(manager)
    aemet_updater = AemetUpdater(aemet_shared)
    p_aemet = mp.Process(target=aemet_updater.run)
    p_aemet.start()

    # Measurements tab related processes
    sensor_shared = _SensorShared(manager)
    sheet_shared = _SheetShared(manager)

    if MEASUREMENTS_INTEGRATION_ACTIVATED:
        sensor_updater = SensorUpdater(sensor_shared)
        p_sensor = mp.Process(target=sensor_updater.run)
        p_sensor.start()

        sheet_updater = SheetUpdater(sheet_shared)
        p_sheets = mp.Process(target=sheet_updater.run)
        p_sheets.start()

    # GUI
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("fusion")
    window = Ui(aemet_shared, sensor_shared, sheet_shared)
    app.exec_()

    # Killing processes safely when GUI is closed
    with aemet_shared.forecast_lock:
        with aemet_shared.radar_lock:
            p_aemet.kill()

    if MEASUREMENTS_INTEGRATION_ACTIVATED:
        with sensor_shared.sensor_lock:
            p_sensor.kill()

        with sheet_shared.sheet_lock:
            p_sheets.kill()
