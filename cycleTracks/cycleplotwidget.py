#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subclass of pyqtgraph.PlotWidget.
"""

from datetime import datetime
from pyqtgraph import PlotWidget, DateAxisItem, mkPen, mkBrush
import numpy as np

class CyclePlotWidget(PlotWidget):
    def __init__(self, df):
        super().__init__(axisItems={'bottom': DateAxisItem()})
        
        self.df = df
        
        self.colour = "#024aeb"
        style = self._makeStyle(self.colour)
        
        date = [datetime.strptime(d, "%Y-%m-%d").timestamp() for d in self.df['Date']]
        distance = np.array(self.df['Distance (km)'])
        time = [self._timeToSecs(t) for t in self.df['Time']]
        time = np.array([self._convertSecs(s) for s in time])
        speed = distance/time
        
        self.plotItem.plot(date, speed, **style)
        self.plotItem.showGrid(x=True, y=True)
        self.plotItem.setLabels(left='Avg. speed, (km/h)', bottom='Date')
        
        # bug workaround - we don't need units/SI prefix on dates
        # this has been fixed in the pyqtgraph source, so won't be necessary
        # once this makes its way into the deb packages
        self.plotItem.getAxis('bottom').enableAutoSIPrefix(False)
        
    @staticmethod
    def _makeStyle(colour):
        pen = mkPen(colour)
        brush = mkBrush(colour)
        d = {'pen':None, 'symbol':'x', 'symbolPen':pen, 'symbolBrush':brush}
        return d
    
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
