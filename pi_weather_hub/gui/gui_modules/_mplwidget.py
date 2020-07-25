# _mplwidget.py
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

"""Matplotlib widget"""
# The code below was written based on StackOverflow user
# launchpadmcquack's contribution:
# Source: https://stackoverflow.com/a/44029435/8512412

# pip
import matplotlib as mpl
import matplotlib.backends.backend_qt5agg as mpl_backend_qt5agg
import matplotlib.figure as mpl_figure
from PyQt5 import QtWidgets

# AGG renderer with QT5 user interface
mpl.use('QT5Agg')

class MplCanvas(mpl_backend_qt5agg.FigureCanvasQTAgg):
    """Matplotlib QT canvas"""
    def __init__(self):
        self.fig = mpl_figure.Figure()
        self.ax = self.fig.add_subplot(111)
        
        mpl_backend_qt5agg.FigureCanvasQTAgg.__init__(self, self.fig)
        mpl_backend_qt5agg.FigureCanvasQTAgg.setSizePolicy(
            self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        mpl_backend_qt5agg.FigureCanvasQTAgg.updateGeometry(self)

class MplWidget(QtWidgets.QWidget):
    """Matplotlib Widget"""
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.canvas = MplCanvas()

        self.vbl = QtWidgets.QVBoxLayout()
        self.vbl.addWidget(self.canvas)

        self.vbl.setContentsMargins(0, 0, 0, 0) # Fix margins

        self.setLayout(self.vbl)