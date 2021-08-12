"""
Widget containing plot and labels.
"""

from datetime import datetime
from pyqtgraph import PlotWidget, PlotCurveItem, mkPen, mkBrush, InfiniteLine
import numpy as np
from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot
from PyQt5.QtWidgets import QVBoxLayout, QWidget

from .custompyqtgraph import CustomAxisItem, CustomDateAxisItem, CustomViewBox
from cycleTracks.util import floatToHourMinSec


class StatPlot(PlotWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        
        self.style = {'mean':{'colour':"#024aeb",
                               'symbol':'o'},
                      'median':{'colour':"#cf0202",
                                  'symbol':'o'}}
        self.plot()
        # self.plotSpread()
        
    @property
    def data(self):
        return self.parent.data
        
    def plot(self):
        dataObjs = self.data.splitMonths(returnType='CycleData')
        
        col = 'Avg. speed (km/h)'
        means = []
        medians = []
        for _, monthData in dataObjs:
            means.append(np.mean(monthData[col]))
            medians.append(np.median(monthData[col]))
            
        styleDict = self.style['mean']
        style = self._makeScatterStyle(**styleDict)
        self.dataItem = self.plotItem.scatterPlot(means, **style)
        
        styleDict = self.style['median']
        style = self._makeScatterStyle(**styleDict)
        self.dataItem = self.plotItem.scatterPlot(medians, **style)
        
        
    def plotSpread(self, monthIdx=-1):
        data = self.data.splitMonths(returnType='CycleData')[monthIdx][1]
        col = 'Avg. speed (km/h)'
        values = data[col]
        mean = np.mean(values)
        std = np.std(values)
        spread = (values - mean)/std
        
        # styleDict = self.style['mean']
        # style = self._makeScatterStyle(**styleDict)
        # self.dataItem = self.plotItem.scatterPlot([mean], **style)
        
        styleDict = {'colour':"#19b536", 'symbol':"x"}
        style = self._makeScatterStyle(**styleDict)
        self.dataItem = self.plotItem.scatterPlot(spread, **style)
        
        
    @staticmethod
    def _makeScatterStyle(colour, symbol):
        """ Make style for series with no line but with symbols. """
        pen = mkPen(colour)
        brush = mkBrush(colour)
        d = {'symbol':symbol, 'symbolPen':pen, 'symbolBrush':brush}
        return d