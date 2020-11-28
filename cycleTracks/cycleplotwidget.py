#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subclass of pyqtgraph.PlotWidget.
"""

from datetime import datetime
from pyqtgraph import (PlotWidget, DateAxisItem, PlotCurveItem, ViewBox, mkPen, 
                       mkBrush)
import numpy as np
from PyQt5.QtCore import pyqtSlot as Slot


class CycleData:
    
    def __init__(self, df):
        self.df = df
        
    @staticmethod
    def _timeToSecs(t):
        msg = ''
        # don't actually need the datetime objects returned by strptime, but 
        # this is probably the easist way to check the format
        try:
            datetime.strptime(t, "%H:%M:%S")
            hr, mins, sec = [int(s) for s in t.split(':')]
        except ValueError:
            try:
                datetime.strptime(t, "%M:%S")
                mins, sec = [int(s) for s in t.split(':')]
                hr = 0
            except ValueError:
                msg = f"Could not format time '{t}'"
        if msg:
            raise ValueError(msg)
        
        total = sec + (60*mins) + (60*60*hr)
        return total
    
    @staticmethod
    def _convertSecs(t, mode='hour'):
        valid = ['mins', 'hour']
        if mode not in valid:
            msg = f"Mode '{mode}' not in valid modes: {valid}"
            raise ValueError(msg)
        m = t / 60
        if mode == 'mins':
            return m
        h = m / 60
        if mode == 'hour':
            return h
        
    @property
    def distance(self):
        return np.array(self.df['Distance (km)'])
    
    @property
    def time(self):
        time = [self._timeToSecs(t) for t in self.df['Time']]
        time = np.array([self._convertSecs(s) for s in time])
        return time
    
    @property
    def dateTimestamps(self):
        return [dt.timestamp() for dt in self.datetimes]

    @property
    def datetimes(self):
        return [datetime.strptime(d, "%Y-%m-%d") for d in self.df['Date']]
    

class CyclePlotWidget(PlotWidget):
    def __init__(self, df):
        super().__init__(axisItems={'bottom': DateAxisItem()})
        
        self.data = CycleData(df)
        
        self.style = {'speed':{'colour':"#024aeb"},
                      'odometer':{'colour':"#178a00"}}
        
        self._initRightAxis('Total distance', self.style['odometer']['colour'])
        
        style = self._makeScatterStyle(self.style['speed']['colour'])
        speed = self.data.distance/self.data.time
        self.plotItem.plot(self.data.dateTimestamps, speed, **style)
        
        
        # self.plotItem.showGrid(x=True, y=True)
        self.plotItem.setLabels(left='Avg. speed, (km/h)', bottom='Date')
        
        style = self._makeFillStyle(self.style['odometer']['colour'])
        odo = self._getMonthlyOdometer()
        curve = PlotCurveItem(self.data.dateTimestamps, odo, **style)
        self.vb2.addItem(curve)
        
        # style = self._makeStyle("#cf0202")
        # self.plotItem.plot(date, self.df['Distance (km)'], **style)
        # # style = self._makeStyle("#19b536")
        # # self.plotItem.plot(date, self.df['Time'], **style)
        # style = self._makeStyle("#ff9100")
        # self.plotItem.plot(date, self.df['Calories'], **style)
        
        self.plotItem.getAxis('left').setGrid(255)
        self.plotItem.getAxis('bottom').setGrid(255)
        
        # bug workaround - we don't need units/SI prefix on dates
        # this has been fixed in the pyqtgraph source, so won't be necessary
        # once this makes its way into the deb packages
        self.plotItem.getAxis('bottom').enableAutoSIPrefix(False)
        
        self.updateViews()
        self.plotItem.vb.sigResized.connect(self.updateViews)
        
        
    def _initRightAxis(self, label, colour):
        
        self.vb2 = ViewBox()
        self.plotItem.showAxis('right')
        self.plotItem.scene().addItem(self.vb2)
        self.plotItem.getAxis('right').linkToView(self.vb2)
        self.vb2.setXLink(self.plotItem)
        self.plotItem.getAxis('right').setLabel(label, color=colour)
        
        
    @Slot()
    def updateViews(self):
        ## Copied from PyQtGraph MultiplePlotAxes.py example ##
        # view has resized; update auxiliary views to match
        self.vb2.setGeometry(self.plotItem.vb.sceneBoundingRect())
        # need to re-update linked axes since this was called
        # incorrectly while views had different shapes.
        # (probably this should be handled in ViewBox.resizeEvent)
        self.vb2.linkedViewChanged(self.plotItem.vb, self.vb2.XAxis)
    
    @staticmethod
    def _makeScatterStyle(colour):
        pen = mkPen(colour)
        brush = mkBrush(colour)
        d = {'pen':None, 'symbol':'x', 'symbolPen':pen, 'symbolBrush':brush}
        return d

    @staticmethod
    def _makeFillStyle(colour):
        pen = mkPen(colour)
        brush = mkBrush(colour)
        d = {'pen':pen, 'brush':brush, 'fillLevel':0}
        return d


    def _getMonthlyOdometer(self):
        
        months = [dt.month for dt in self.data.datetimes]
        
        odo = np.zeros(len(self.data.distance))
        prev = 0
        for i in range(len(self.data.distance)):
            if i == 0 or months[i] != months[i-1]:
                prev = 0
            else:
                prev = odo[i-1]
            odo[i] = prev + self.data.distance[i]
            
        return odo