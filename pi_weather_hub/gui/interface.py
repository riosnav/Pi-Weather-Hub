# interface.py
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
"""This module contains the PyQt5 Ui class """

# stdlib
import datetime
import os
import threading
import time

# pip
import matplotlib as mpl
from PyQt5 import QtCore, QtGui, QtWidgets, uic

# app modules
from gui.gui_modules import _plots_configuration
from gui.gui_modules._aemet_forecast_manager import _AemetForecastManager
from gui.gui_modules import _mplwidget
from gui.gui_resources import interface_rc


class _WorkerSignals(QtCore.QObject):
    activate_clock_signal = QtCore.pyqtSignal()
    update_forecast_days_ui = QtCore.pyqtSignal(list)
    update_forecast_hours_ui = QtCore.pyqtSignal(list)
    update_radar_ui = QtCore.pyqtSignal(tuple)


class Ui(QtWidgets.QMainWindow):
    """
    The Ui object is this app's PyQt5 main GUI class.
    """
    def __init__(self, aemet_shared, sensor_shared, sheet_shared):
        """
        Parameters
        ----------
            aemet_shared : object
                Manager object containing the shared variables.
            sensor_shared : object
                Manager object containing the shared variables.
            sheet_shared : object
                Manager object containing the shared variables.
        """
        super(Ui, self).__init__()

        self.running = True
        uic.loadUi('./gui/gui_resources/interface.ui', self)

        # signals used to update gui elements from inside.
        self.signals = _WorkerSignals()
        self.signals.update_forecast_hours_ui.connect(self.update_hours_forecast_labels)
        self.signals.update_forecast_days_ui.connect(self.update_days_forecast_labels)
        self.signals.update_radar_ui.connect(self.radar_ui_updater)

        # signals triggered while interacting with the gui.
        self.b_next.clicked.connect(self.on_click_b_next)
        self.b_previous.clicked.connect(self.on_click_b_previous)
        self.tabWidget.currentChanged.connect(self.reset_hourly_forecast)
        self.b_animation.clicked.connect(self.on_click_radar_animation)
        self.b_current.clicked.connect(self.on_click_radar_current)
        # hiddent exit method
        self.forecast_times_clicked = 0
        self.exit_counter_initial_time = time.time()
        self.tabWidget.tabBarClicked[int].connect(self.hidden_exit_counter)

        # clock.
        self.clock_timer = QtCore.QTimer()
        self.clock_timer.timeout.connect(self.update_clock)
        self.signals.activate_clock_signal.connect(self.activate_clock)
        self.oclock_updated = False

        # parallel workers.
        self.aemet_shared = aemet_shared
        self.aemet_forecast = _AemetForecastManager()
        self.forecast_updater = threading.Thread(target=self.forecast_update_handler, args=())
        self.forecast_updater.start()
        self.radar_updater = threading.Thread(target=self.radar_update_handler, args=())
        self.radar_updater.start()
        self.sheet_shared = sheet_shared
        self.sensor_shared = sensor_shared
        self.plots_updater = threading.Thread(target=self.plots_update_handler, args=())
        self.plots_updater.start()

        self.showFullScreen()

    def closeEvent(self, event):
        # End threads safely when GUI is closed.
        self.running = False

        self.aemet_shared.forecast_ready.set()
        self.aemet_shared.radar_ready.set()
        self.sensor_shared.sensor_ready.set()
        self.sheet_shared.sheet_ready.set()

        event.accept()

    def forecast_update_handler(self):
        self.aemet_shared.forecast_ready.wait()
        self.aemet_shared.forecast_ready.clear()

        self.signals.activate_clock_signal.emit()
        self.b_next.setEnabled(True)
        self.b_previous.setEnabled(True)

        while self.running:
            with self.aemet_shared.forecast_lock:
                # if the forecast has been updated, update the labels.
                if self.aemet_forecast.update_daily_forecasts(
                        self.aemet_shared.forecast['daily']):
                    self.signals.update_forecast_days_ui.emit(self.aemet_forecast.today)
                    self.signals.update_forecast_days_ui.emit(self.aemet_forecast.days)
                if self.aemet_forecast.update_hourly_forecasts(
                        self.aemet_shared.forecast['hourly']):
                    index = self.aemet_forecast.hours_moving_index
                    self.signals.update_forecast_hours_ui.emit(
                        self.aemet_forecast.hours[index:index+12])
                self.aemet_shared.forecast_ready.clear()
            self.aemet_shared.forecast_ready.wait()

    def radar_update_handler(self):
        self.radar_state = "current"

        self.aemet_shared.radar_ready.wait()
        self.aemet_shared.radar_ready.clear()

        self.b_animation.setEnabled(True)
        self.b_current.setEnabled(True)

        while self.running:
            index = 0
            iterations = 0
            with self.aemet_shared.radar_lock:
                files_national = sorted([("./shared_resources/_national_radar" + "/" + i)
                                         for i in os.listdir(
                                         "./shared_resources/_national_radar")])
                files_regional = sorted([("./shared_resources/_regional_radar" + "/" + i)
                                         for i in os.listdir(
                                         "./shared_resources/_regional_radar")])
                radar_timestamps = [i.rsplit(' ', 1)[1].rsplit('.', 1)[0].replace("-", ":")
                                    for i in files_regional]

                # animate radar images in sequence, if necesassary.
                while((self.running)
                        and (self.radar_state == "animated")
                        and (self.tabWidget.currentIndex() == 1)
                        and (iterations < 5)):
                    self.signals.update_radar_ui.emit(
                        (files_regional[index],
                         files_national[index],
                         radar_timestamps[index]))

                    index = index + 1
                    if index >= len(files_regional):
                        iterations = iterations + 1
                        index = 0

                    loop = QtCore.QEventLoop()
                    QtCore.QTimer.singleShot(500, loop.quit)
                    loop.exec_()

                if iterations >= 5:
                    self.b_current.toggle()
                    self.b_animation.toggle()
                    self.radar_state = "current"

                self.signals.update_radar_ui.emit(
                    (files_regional[-1],
                     files_national[-1],
                     radar_timestamps[-1]))
                self.aemet_shared.radar_ready.clear()
            self.aemet_shared.radar_ready.wait()

    def plots_update_handler(self):
        self.sheet_shared.sheet_ready.wait()
        self.sensor_shared.sensor_ready.wait()
        self.sheet_shared.sheet_ready.clear()

        while self.running:
            with self.sheet_shared.sheet_lock:
                with self.sensor_shared.sensor_lock:
                    self._update_measurements_labels()

                    self.temperature_graph = _plots_configuration.setup_temperature_plot(
                        self.temperature_graph,
                        self.sheet_shared.sheet_variables['Timestamp'],
                        self.sheet_shared.sheet_variables['Temperature'],
                        self.sensor_shared.sensor_variables['Timestamp'],
                        self.sensor_shared.sensor_variables['Temperature'])
                    self.temperature_graph.canvas.draw()

                    self.humidity_graph = _plots_configuration.setup_humidity_plot(
                        self.humidity_graph,
                        self.sheet_shared.sheet_variables['Timestamp'],
                        self.sheet_shared.sheet_variables['Humidity'],
                        self.sensor_shared.sensor_variables['Timestamp'],
                        self.sensor_shared.sensor_variables['Humidity'])
                    self.humidity_graph.canvas.draw()

                    self.pressure_graph = _plots_configuration.setup_pressure_plot(
                        self.pressure_graph,
                        self.sheet_shared.sheet_variables['Timestamp'],
                        self.sheet_shared.sheet_variables['Pressure'])
                    self.pressure_graph.canvas.draw()

                    self.sheet_shared.sheet_ready.clear()
            self.sheet_shared.sheet_ready.wait()

    def _update_measurements_labels(self):
        self.exterior_temp.setText(
            ("%0.1f" % self.sheet_shared.sheet_stadistics['Current temperature']) + " °C")
        self.exterior_humidity.setText(
            ("%0.1f" % self.sheet_shared.sheet_stadistics['Current humidity']) + "%")
        self.pressure.setText(
            ("%0.2f" % self.sheet_shared.sheet_stadistics['Current pressure']) + " hPa")

        self.interior_temp.setText(
            ("%0.1f" % self.sensor_shared.sensor_stadistics['Current temperature']) + " °C")
        self.interior_humidity.setText(
            ("%0.1f" % self.sensor_shared.sensor_stadistics['Current humidity']) + "%")

        self.exterior_max_temp.setText(
            ("%0.1f" % self.sheet_shared.sheet_stadistics['Max temperature']) + " °C")
        self.exterior_min_temp.setText(
            ("%0.1f" % self.sheet_shared.sheet_stadistics['Min temperature']) + " °C")
        self.exterior_max_hum.setText((
            "%0.1f" % self.sheet_shared.sheet_stadistics['Max humidity']) + "%")
        self.exterior_min_hum.setText(
            ("%0.1f" % self.sheet_shared.sheet_stadistics['Min humidity']) + "%")

        self.interior_max_temp.setText(
            ("%0.1f" % self.sensor_shared.sensor_stadistics['Max temperature']) + " °C")
        self.interior_min_temp.setText(
            ("%0.1f" % self.sensor_shared.sensor_stadistics['Min temperature']) + " °C")
        self.interior_max_hum.setText((
            "%0.1f" % self.sensor_shared.sensor_stadistics['Max humidity']) + "%")
        self.interior_min_hum.setText(
            ("%0.1f" % self.sensor_shared.sensor_stadistics['Min humidity']) + "%")

    def hidden_exit_counter(self, int):
        # hiddent exit method
        if int == 0:
            exit_counter_current_time = time.time()
            if exit_counter_current_time < self.exit_counter_initial_time + 2:
                self.forecast_times_clicked = self.forecast_times_clicked + 1
            else:
                self.forecast_times_clicked = 0
            self.exit_counter_initial_time = exit_counter_current_time
            
            if self.forecast_times_clicked > 4:
                self.close()

    @QtCore.pyqtSlot()
    def activate_clock(self):
        self.clock_timer.start(1000)

    @QtCore.pyqtSlot()
    def update_clock(self):
        current_time = datetime.datetime.now()
        self.hour_d0.setText(datetime.datetime.strftime(current_time, "%H:%M"))

        if ((current_time.minute == 0) and (not self.oclock_updated)):
            with self.aemet_shared.forecast_lock:
                self.aemet_shared.forecast_ready.set()
            self.oclock_updated = True
        if self.oclock_updated:
            self.oclock_updated = False

    @QtCore.pyqtSlot()
    def on_click_b_next(self):
        moved = self.aemet_forecast.move_hour_index(1)
        if moved:
            self.move_forecast_hours()

    @QtCore.pyqtSlot()
    def on_click_b_previous(self):
        moved = self.aemet_forecast.move_hour_index(-1)
        if moved:
            self.move_forecast_hours()

    def move_forecast_hours(self):
        index = self.aemet_forecast.hours_moving_index
        with self.aemet_shared.forecast_lock:
            self.update_hours_forecast_labels(self.aemet_forecast.hours[index:index+12])

    @QtCore.pyqtSlot()
    def on_click_radar_current(self):
        if self.b_animation.isChecked():
            self.b_animation.toggle()
            self.radar_state = "current"
            self.aemet_shared.radar_ready.set()
        else:
            self.b_current.toggle()
            self.radar_state = "current"

    @QtCore.pyqtSlot()
    def on_click_radar_animation(self):
        if self.b_current.isChecked():
            self.b_current.toggle()
            self.radar_state = "animated"
            self.aemet_shared.radar_ready.set()
        else:
            self.b_animation.toggle()
            self.radar_state = "animated"

    @QtCore.pyqtSlot(list)
    def update_days_forecast_labels(self, labels):
        for item in range(0, len(labels)):
            getattr(self, labels[item][0][0]).setPixmap(
                QtGui.QPixmap(":/weather/images/" + str(labels[item][0][1]) + ".png"))
            for label in range(1, len(labels[item])):
                getattr(self, labels[item][label][0]).setText(
                    str(labels[item][label][1]))

    @QtCore.pyqtSlot(list)
    def update_hours_forecast_labels(self, labels):
        for item in range(0, len(labels)):
            getattr(self, labels[item][0][0] + str(item + 1)).setPixmap(
                QtGui.QPixmap(":/weather/images/" + str(labels[item][0][1]) + ".png"))
            for label in range(1, len(labels[item])):
                getattr(self, labels[item][label][0] + str(item+1)).setText(
                    str(labels[item][label][1]))

    @QtCore.pyqtSlot()
    def reset_hourly_forecast(self):
        if (self.tabWidget.currentIndex() == 1) or (self.tabWidget.currentIndex() == 2):
            moved = self.aemet_forecast.reset_hour_index()
            if moved:
                self.move_forecast_hours()

    @QtCore.pyqtSlot(tuple)
    def radar_ui_updater(self, data):
        self.regional_radar.setPixmap(QtGui.QPixmap(data[0]))
        self.national_radar.setPixmap(QtGui.QPixmap(data[1]))
        self.timestamp.setText(data[2])