# _aemet_forecast_manager.py
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
"""Module container for the AemetForecastManager class."""

# stdlib
import datetime


class _AemetForecastManager():
    """
    The _AemetForecastManager class provides methods to convert raw 
    forecast data into structures which facilitate the work of updating 
    the GUI's labels. These structures, as well as other useful data are
    stored as attributes.   

    ...

    Attributes
    ----------
    days : list
        List containing label names and its corresponding values for
        each day that can be used to update the 'days' part or the
        forecast GUI.
    today : list
        List containing label names and its corresponding values that 
        can be used to update the 'today' part or the forecast GUI. Its
        structure is similar to 'days'.
    hours : list
        List containing label names and its corresponding values for
        each hour that can be used to update the 'hours' part or the
        forecast GUI.
    hours_moving_index : int
        Value used by the GUI to slice the hours list depending on the 
        desired range to be represented on screen.

    Methods
    -------
    update_daily_forecasts(input_json):
        Builds the 'days' and 'today' lists fron the raw input_json.
    update_hourly_forecasts(input_json):
        Builds the 'hour' list fron the raw input_json.
    reset_hour_index():
        Resets hours_moving_index to the current hour position.
    move_hour_index(delta):
        Moves hours_moving_index delta positions only if the resulting
        position is valid.
    """

    def __init__(self):
        """
        Constructs all the necessary attributes for the
        _AemetForecastManager object.
        """
        self.today = list()
        self.days = list()
        self.hours = list()
        self._populate_today_list()
        self._populate_days_list()
        self._populate_hours_list()
        self.hours_moving_index = 0

        # The index that should be used as hours_moving_index to show the current hours as the
        # first item in the hours GUI part.
        self._current_hour_index = 0
        # This index is used to ensure that the GUI will show the correct day after 00:00.
        self._current_day_index = 0
        # The input json typically has several entries that represent diferent periods of the
        # current day (for example, the third element usually represents 00:00 to 06:00). This
        # index contains the appropriate value for the current time.
        self._current_period_index = self._get_period_index()

        self._daily_last_updated = datetime.datetime(2000, 1, 1)
        self._hourly_last_updated = datetime.datetime(2000, 1, 1)

    def update_daily_forecasts(self, input_json):
        """
        Build the 'days' and 'today' lists fron the raw input_json.

        Parameters
        ----------
            input_json : dict
                Dictionary containing the JSON response from AEMET's
                 API.

        Returns
        -------
            updated : bool
                If today or days have been modified it will return true.
                Otherwise, it will return false.
        """
        raw_forecast = input_json
        timestamp = datetime.datetime.fromisoformat(raw_forecast['elaborado'])
        new_period_index = self._get_period_index()

        if (timestamp > self._daily_last_updated) or (new_period_index != self._current_period_index):
            self._current_period_index = new_period_index
            self._update_current_day_index(raw_forecast)
            # [icon, day label, min. temp., max. temp., wind direction, wind speed,
            #   chance of precipitation, current weather, min. thermal sensation,
            #   max. thermal sensation, uvMax, min. relative humidity, max. relative humidity]
            today_data = [
                raw_forecast['prediccion']['dia'][self._current_day_index]
                ['estadoCielo'][self._current_period_index]['value'],
                self._get_weekday_label(
                    raw_forecast['prediccion']['dia'][self._current_day_index]["fecha"],
                    'today'),
                str(raw_forecast['prediccion']['dia'][self._current_day_index]
                    ['temperatura']['minima']) + "°",
                str(raw_forecast['prediccion']['dia'][self._current_day_index]
                    ['temperatura']['maxima']) + "°",
                self._get_wind_direction_label(
                    raw_forecast['prediccion']['dia'][self._current_day_index]
                    ['viento'][self._current_period_index]['direccion']),
                str(raw_forecast['prediccion']['dia'][self._current_day_index]
                    ['viento'][self._current_period_index]['velocidad']) + " km/h",
                str(raw_forecast['prediccion']['dia'][self._current_day_index]
                    ['probPrecipitacion'][self._current_period_index]['value']) + "%",
                raw_forecast['prediccion']['dia'][self._current_day_index]
                ['estadoCielo'][self._current_period_index]['descripcion'],
                str(raw_forecast['prediccion']['dia'][self._current_day_index]
                    ['sensTermica']['minima']) + "°/"
                + str(raw_forecast['prediccion']['dia'][self._current_day_index]
                      ['sensTermica']['maxima']) + "°",
                raw_forecast['prediccion']['dia'][self._current_day_index]['uvMax'],
                str(raw_forecast['prediccion']['dia'][self._current_day_index]
                    ['humedadRelativa']['minima']) + "%/"
                + str(raw_forecast['prediccion']['dia'][self._current_day_index]
                      ['humedadRelativa']['maxima']) + "%"
            ]
            self._populate_today_list(today_data)

            day_data = list()
            # [[icon, day label, min. temp., max. temp., wind direction, wind speed,
            #   chance of precipitation],...]
            for i in range(1, 6):
                temp_data = [
                    raw_forecast['prediccion']['dia'][self._current_day_index + i]
                    ['estadoCielo'][0]['value'],
                    self._get_weekday_label(
                        raw_forecast['prediccion']['dia'][self._current_day_index + i]["fecha"],
                        'day'),
                    str(raw_forecast['prediccion']['dia'][self._current_day_index + i]
                        ['temperatura']['minima']) + "°",
                    str(raw_forecast['prediccion']['dia'][self._current_day_index + i]
                        ['temperatura']['maxima']) + "°",
                    self._get_wind_direction_label(
                        raw_forecast['prediccion']['dia'][self._current_day_index + i]
                        ['viento'][0]['direccion']),
                    raw_forecast['prediccion']['dia'][self._current_day_index + i]
                    ['viento'][0]['velocidad'],
                    str(raw_forecast['prediccion']['dia'][self._current_day_index + i]
                        ['probPrecipitacion'][0]['value']) + "%"
                ]
                day_data.append(temp_data)
            self._populate_days_list(day_data)

            updated = True
            self._daily_last_updated = timestamp
        else:
            updated = False

        return updated

    def update_hourly_forecasts(self, input_json):
        """
        Build the 'hours' list fron the raw input_json.

        Parameters
        ----------
            input_json : dict
                Dictionary containing the JSON response from AEMET's
                 API.

        Returns
        -------
            updated : bool
                If hours has been modified it will return true.
                Otherwise, it will return false.
        """
        raw_forecast = input_json
        timestamp = datetime.datetime.fromisoformat(raw_forecast['elaborado'])

        if timestamp > self._hourly_last_updated:
            hour_data = list()
            # [[icon, day label, hour label, temperature, humidity,
            # wind direction, wind speed, expected precipitation],...]
            for day in range(0, len(raw_forecast['prediccion']['dia'])):
                for hour in range(0, len(raw_forecast['prediccion']['dia'][day]['estadoCielo'])):
                    temp_data = [
                        raw_forecast['prediccion']['dia'][day]
                        ['estadoCielo'][hour]['value'],
                        self._get_weekday_label(
                            raw_forecast['prediccion']['dia'][day]["fecha"], 'hour'),
                        raw_forecast['prediccion']['dia'][day]
                        ['estadoCielo'][hour]['periodo'],
                        raw_forecast['prediccion']['dia'][day]
                        ['temperatura'][hour]['value'] + "°",
                        raw_forecast['prediccion']['dia'][day]
                        ['humedadRelativa'][hour]['value'] + "%",
                        self._get_wind_direction_label(
                            raw_forecast['prediccion']['dia'][day]
                            ['vientoAndRachaMax'][2*hour]['direccion'][0]),
                        raw_forecast['prediccion']['dia'][day]
                        ['vientoAndRachaMax'][2 * hour]['velocidad'][0],
                        raw_forecast['prediccion']['dia'][day]
                        ['precipitacion'][hour]['value']
                    ]
                    # If 'expected precipitation' is 0, do not show
                    # anything.
                    if temp_data[-1] == '0':
                        temp_data[-1] = ""
                    hour_data.append(temp_data)
            self._populate_hours_list(hour_data)

            _ = self.reset_hour_index()

            updated = True
            self._hourly_last_updated = timestamp
        elif self._update_current_hour_index():
            _ = self.reset_hour_index()
            updated = True
        else:
            updated = False

        return updated

    def reset_hour_index(self):
        """
        Reset hours_moving_index to the current hour position, if
        necessary.

        Returns
        -------
            moved : bool
                If hours_moving_index has been modified it will 
                return true. Otherwise, it will return false.
        """
        self._update_current_hour_index()
        if self.hours_moving_index != self._current_hour_index:
            self.hours_moving_index = self._current_hour_index
            moved = True
        else:
            moved = False
        return moved

    def move_hour_index(self, delta):
        """
        Move hours_moving_index delta positions only if the resulting
        position is valid.

        Parameters
        ----------
            delta : int
                Usually +1 or -1.

        Returns
        -------
            updated : bool
                If the index has been moved delta positions it will 
                return true. Otherwise, it will return false.
        """
        if self._current_hour_index <= self.hours_moving_index + delta < len(self.hours) - 12:
            self.hours_moving_index = self.hours_moving_index + delta
            moved = True
        else:
            moved = False
        return moved

    def _populate_today_list(self, values=None):
        # Generate a GUI friendly data structure from preformatted data
        # from the update_daily_forecasts method. If there is no input,
        # it will fill the structure with placeholders.
        if values is None:
            values = ["11", "lunes, 01 de enero", "20°", "20°", "↙",
                      "0 km/h", "0%", "Despejado", "20°/20°", "0", "0%/100%"]
        objectNames = ["icon_d0", "weekday_d0", "min_temp_d0", "max_temp_d0", "direction_d0",
                       "magnitude_d0", "pp_v_d0", "description_d0", "st_v_d0", "uv_v_d0", "h_v_d0"]
        temp_today = list()
        for objectName, value in zip(objectNames, values):
            temp_today.append([objectName, value])
        self.today = list()
        self.today.append(temp_today)

    def _populate_days_list(self, values=None):
        # Generate a GUI friendly data structure from preformatted data
        # from the update_daily_forecasts method. If there is no input,
        # it will fill the structure with placeholders.
        if values is None:
            values = ["11", "lunes", "20°", "20°", "↙", "0 km/h", "0%"]
        objectNames = ["icon_d", "weekday_d", "min_temp_d",
                       "max_temp_d", "direction_d", "magnitude_d", "pp_v_d"]
        self.days = list()
        for i in range(0, 5):
            temp_day = list()
            for objectName, value in zip(objectNames, values[i]):
                temp_day.append([objectName + str(i+1), value])
            self.days.append(temp_day)

    def _populate_hours_list(self, values=None):
        # Generate a GUI friendly data structure from preformatted data
        # from the update_hourly_forecasts method. If there is no input,
        # it will fill the structure with placeholders.
        if values is None:
            single_values = ["11", "lunes", "00", "20°", "20%", "↙", "0", ""]
            values = list()
            for i in range(0, 12):
                values.append(single_values)
        objectNames = ["icon_", "weekday_", "hour_", "temperature_",
                       "humidity_", "direction_", "magnitude_", "rain_"]
        self.hours = list()
        for i in range(0, len(values)):
            temp_hour = list()
            for objectName, value in zip(objectNames, values[i]):
                temp_hour.append([objectName, value])
            self.hours.append(temp_hour)

    def _get_period_index(self):
        # Determine the correcponding period index based on the current
        # time.
        hour = datetime.datetime.now().hour
        if 0 <= hour < 6:
            index = 3
        elif 6 <= hour < 12:
            index = 4
        elif 12 <= hour < 18:
            index = 5
        else:
            index = 6
        return index

    def _update_current_day_index(self, raw_forecast):
        # Find the appropriate index for today's data.
        index = 0
        current_day = datetime.datetime.now().day
        found = False
        while not found:
            if datetime.datetime.fromisoformat(raw_forecast['prediccion']['dia'][index]['fecha']
                                               ).day == current_day:
                found = True
            else:
                index = index + 1
        if self._current_day_index != index:
            self._current_day_index = index

    def _update_current_hour_index(self):
        # Find the appropriate index for the current hour's data.
        index = 0
        current_hour = datetime.datetime.now().hour
        found = False
        while not found:
            if int(self.hours[index][2][1]) == current_hour:
                found = True
            else:
                index = index + 1
        if self._current_hour_index == index:
            updated = False
        else:
            updated = True
            self._current_hour_index = index
        return updated

    def _get_weekday_label(self, day, mode):
        # Get the appropriate label and format it according to the place
        # where it's going to be displayed in the GUI.
        date = datetime.datetime.fromisoformat(day)
        day = date.day
        weekday_index = date.weekday()
        month_index = date.month

        weekday = {
            0: "lunes",
            1: "martes",
            2: "miércoles",
            3: "jueves",
            4: "viernes",
            5: "sábado",
            6: "domingo"
        }[weekday_index]

        month = {
            1: "enero",
            2: "febrero",
            3: "marzo",
            4: "abril",
            5: "mayo",
            6: "junio",
            7: "julio",
            8: "agosto",
            9: "septiembre",
            10: "octubre",
            11: "noviembre",
            12: "diciembre"
        }[month_index]

        if mode == 'today':
            label = weekday + ", " + str(day) + " de " + str(month)
        elif mode == 'hour':
            label = weekday[0:3] + "."
        else:
            label = weekday
        return label

    def _get_wind_direction_label(self, direction):
        label = {
            '': "",
            'C': "",
            'N': "↓",
            'NE': "↙",
            'E': "←",
            'SE': "↖",
            'S': "↑",
            'SO': "↗",
            'O': "→",
            'NO': "↘"
        }[direction]
        return label