# _plots_configuration.py
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
Module containing functions used to set up the different plots of the UI.


Functions
-------
_setup_temperature_plot(temperature_graph, timestamps, temperatures):
    Set up the temperature plot.
_setup_humidity_plot(humidity_graph, timestamps, humidities):
    Set up the humidity plot.
_setup_pressure_plot(pressure_graph, timestamps, pressures):
    Set up the pressure plot.
"""

# pip
import numpy as np
import matplotlib as mpl


def setup_temperature_plot(temperature_graph, timestamps, temperatures,
                           timestamps_sensor, temperatures_sensor):
    """
    Set up the temperature plot.

    Parameters
    ----------
        temperature_graph : mplwidget object
            The figure to be configured.
        timestamps : list
            X values: timestamps stored in ISO 8601 format.
        temperatures : list
            Y values: temperature values.

    Returns
    -------
        temperature_graph : mplwidget object
    """
    temperature_graph.canvas.ax.clear()

    temperature_graph.canvas.ax.plot_date(
        np.array(timestamps, dtype='datetime64'), temperatures, '-')
    temperature_graph.canvas.ax.plot_date(
        np.array(timestamps_sensor, dtype='datetime64'), temperatures_sensor, '-')

    temperature_graph.canvas.ax.xaxis.set_major_locator(mpl.dates.DayLocator())
    temperature_graph.canvas.ax.xaxis.set_major_formatter(mpl.dates.DateFormatter('%d'))
    temperature_graph.canvas.ax.xaxis.set_minor_locator(mpl.dates.HourLocator(range(0, 24, 6)))

    temperature_graph.canvas.ax.yaxis.set_major_locator(mpl.ticker.MultipleLocator(1))
    temperature_graph.canvas.ax.yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter('%d °C'))
    temperature_graph.canvas.ax.yaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.25))

    temperature_graph.canvas.ax.grid(
        b=True, which='major', color='#666666', linestyle='-', alpha=0.5)
    temperature_graph.canvas.ax.grid(
        b=True, which='minor', color='#999999', linestyle='-', alpha=0.2)

    temperature_graph.canvas.ax.margins(0, 0.05)
    temperature_graph.canvas.fig.canvas.fig.subplots_adjust(
        left=1.5/16.0, right=1-0.3/16.0, bottom=0.6/8.0, top=1-0.3/8.0)

    return temperature_graph


def setup_humidity_plot(humidity_graph, timestamps, humidities,
                        timestamps_sensor, humidities_sensor):
    """
    Set up the humidity plot.

    Parameters
    ----------
        humidity_graph : mplwidget object
            The figure to be configured.
        timestamps : list
            X values: timestamps stored in ISO 8601 format.
        humidities : list
            Y values: humidity values.

    Returns
    -------
        humidity_graph : mplwidget object
    """
    humidity_graph.canvas.ax.clear()

    humidity_graph.canvas.ax.plot_date(np.array(timestamps, dtype='datetime64'), humidities, '-')
    humidity_graph.canvas.ax.plot_date(
        np.array(timestamps_sensor, dtype='datetime64'), humidities_sensor, '-')

    humidity_graph.canvas.ax.xaxis.set_major_locator(mpl.dates.DayLocator())
    humidity_graph.canvas.ax.xaxis.set_major_formatter(mpl.dates.DateFormatter('%d'))
    humidity_graph.canvas.ax.xaxis.set_minor_locator(mpl.dates.HourLocator(range(0, 24, 6)))

    humidity_graph.canvas.ax.yaxis.set_major_locator(mpl.ticker.MultipleLocator(10))
    humidity_graph.canvas.ax.yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter('%d%%'))
    humidity_graph.canvas.ax.yaxis.set_minor_locator(mpl.ticker.MultipleLocator(2.5))

    humidity_graph.canvas.ax.grid(
        b=True, which='major', color='#666666', linestyle='-', alpha=0.5)
    humidity_graph.canvas.ax.grid(
        b=True, which='minor', color='#999999', linestyle='-', alpha=0.2)

    humidity_graph.canvas.ax.margins(0, 0.05)
    humidity_graph.canvas.fig.subplots_adjust(
        left=1.3/16.0, right=1-0.3/16.0, bottom=1/8.0, top=1-0.5/8.0)

    return humidity_graph


def setup_pressure_plot(pressure_graph, timestamps, pressures):
    """
    Set up the pressure plot.

    Parameters
    ----------
        pressure_graph : mplwidget object
            The figure to be configured.
        timestamps : list
            X values: timestamps stored in ISO 8601 format.
        pressures : list
            Y values: pressure values.

    Returns
    -------
        humidity_graph : mplwidget object
    """
    pressure_graph.canvas.ax.clear()

    pressure_graph.canvas.ax.plot_date(np.array(timestamps, dtype='datetime64'), pressures, '-')

    pressure_graph.canvas.ax.xaxis.set_major_locator(mpl.dates.DayLocator())
    pressure_graph.canvas.ax.xaxis.set_major_formatter(mpl.dates.DateFormatter('%d'))
    pressure_graph.canvas.ax.xaxis.set_minor_locator(mpl.dates.HourLocator(range(0, 24, 12)))

    pressure_graph.canvas.ax.yaxis.set_major_locator(mpl.ticker.MultipleLocator(2))
    pressure_graph.canvas.ax.yaxis.set_minor_locator(mpl.ticker.MultipleLocator(1))

    pressure_graph.canvas.ax.axhline(1013.25, color='b')  # 1 atm

    pressure_graph.canvas.ax.grid(
        b=True, which='major', color='#666666', linestyle='-', alpha=0.5)
    pressure_graph.canvas.ax.grid(
        b=True, which='minor', color='#999999', linestyle='-', alpha=0.2)

    pressure_graph.canvas.ax.margins(0, 0.05)
    pressure_graph.canvas.fig.canvas.fig.subplots_adjust(
        left=2.3/16.0, right=1-0.3/16.0, bottom=1/8.0, top=1-0.5/8.0)

    return pressure_graph
