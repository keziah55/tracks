#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subclass of pyqtgraph.PlotWidget.
"""

from datetime import datetime
from pyqtgraph import (PlotWidget, DateAxisItem, PlotCurveItem, ViewBox, mkPen, 
                       mkBrush, InfiniteLine)
import numpy as np
from PyQt5.QtCore import pyqtSlot as Slot

class CycleData:
    
    def __init__(self, df):
        """ Object providing convenience functions for accessing data from 
            a given DataFrame of cycling data.
        """
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
        """ Return 'Distance (km)' column as numpy array. """
        return np.array(self.df['Distance (km)'])
    
    @property
    def time(self):
        return list(self.df['Time'])
    
    @property
    def date(self):
        return list(self.df['Date'])
    
    @property
    def calories(self):
        return np.array(self.df['Calories'])
    
    @property
    def timeSecs(self):
        """ Return numpy array of 'Time' column, where each value is converted
            to seconds.
        """
        time = [self._timeToSecs(t) for t in self.df['Time']]
        time = np.array([self._convertSecs(s) for s in time])
        return time
    
    @property
    def dateTimestamps(self):
        """ Return 'Date' column, converted to array of timestamps (time since 
            epoch).
    
            See also: :py:meth:`datetimes`.
        """
        return np.array([dt.timestamp() for dt in self.datetimes])

    @property
    def datetimes(self):
        """ Return 'Date' column, converted to list of datetime objects. """
        return [datetime.strptime(d, "%Y-%m-%d") for d in self.df['Date']]
    

class CyclePlotWidget(PlotWidget):
    def __init__(self, df, label):
        super().__init__(axisItems={'bottom': DateAxisItem()})
        
        self.data = CycleData(df)
        
        self.style = {'speed':{'colour':"#024aeb",
                               'symbol':'x'},
                      'odometer':{'colour':"#36cc18"},
                      'distance':{'colour':"#cf0202"},
                      'time':{'colour':"#19b536"},
                      'calories':{'colour':"#ff9100"}}
        
        self._initRightAxis()
        
        # plot avg speed
        style = self._makeScatterStyle(**self.style['speed'])
        self.speed = self.data.distance/self.data.timeSecs
        self.plotItem.plot(self.data.dateTimestamps, self.speed, **style)
        
        # plot monthly total distance        
        style = self._makeFillStyle(self.style['odometer']['colour'])
        dts, odo = self._getMonthlyOdometer()
        dts = [dt.timestamp() for dt in dts]
        curve = PlotCurveItem(dts, odo, **style)
        self.vb2.addItem(curve)
        
        # axis labels
        self.plotItem.setLabels(left='Avg. speed, (km/h)', bottom='Date')
        self.plotItem.getAxis('right').setLabel('Total monthly distance', 
            color=self.style['odometer']['colour'])
        
        # show grid on left and bottom axes
        self.plotItem.getAxis('left').setGrid(255)
        self.plotItem.getAxis('bottom').setGrid(255)
        
        # bug workaround - we don't need units/SI prefix on dates
        # this has been fixed in the pyqtgraph source, so won't be necessary
        # once this makes its way into the deb packages
        self.plotItem.getAxis('bottom').enableAutoSIPrefix(False)
        
        # cross hairs
        self.label = label
        self.vLine = InfiniteLine(angle=90, movable=False)
        self.hLine = InfiniteLine(angle=0, movable=False)
        self.plotItem.addItem(self.vLine, ignoreBounds=True)
        self.plotItem.addItem(self.hLine, ignoreBounds=True)
        
        # SignalProxy(self.plotItem.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        self.plotItem.scene().sigMouseMoved.connect(self.mouseMoved)
        
        # update second view box
        self.updateViews()
        self.plotItem.vb.sigResized.connect(self.updateViews)
        
        
    def _initRightAxis(self):
        self.vb2 = ViewBox()
        self.plotItem.showAxis('right')
        self.plotItem.scene().addItem(self.vb2)
        self.plotItem.getAxis('right').linkToView(self.vb2)
        self.vb2.setXLink(self.plotItem)
        
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
    def _makeScatterStyle(colour, symbol):
        """ Make style for series with no line but with symbols. """
        pen = mkPen(colour)
        brush = mkBrush(colour)
        d = {'pen':None, 'symbol':symbol, 'symbolPen':pen, 'symbolBrush':brush}
        return d

    @staticmethod
    def _makeFillStyle(colour):
        """ Make style for PlotCurveItem with fill underneath. """
        pen = mkPen(colour)
        brush = mkBrush(colour)
        d = {'pen':pen, 'brush':brush, 'fillLevel':0}
        return d


    def _getMonthlyOdometer(self):
        """ Return list of datetime objects and list of floats.
            
            The datetime objects are required, as they add dummy 1st of the 
            month data points to reset the total to 0km.
        """
        
        odo = []
        dts = []
            
        for i, dt in enumerate(self.data.datetimes):
            if i == 0 or self.data.datetimes[i-1].month != dt.month:
                tmp = datetime(self.data.datetimes[i].year, self.data.datetimes[i].month, 1)
                dts.append(tmp)
                prev = 0
                odo.append(prev)
            else:
                prev = odo[-1]
            dts.append(dt)
            odo.append(prev + self.data.distance[i-1])
        
        return dts, odo
    
    @Slot(object)
    def mouseMoved(self, pos):
        if self.plotItem.sceneBoundingRect().contains(pos):
            mousePoint = self.plotItem.vb.mapSceneToView(pos)
            idx = int(mousePoint.x())
            if idx > min(self.data.dateTimestamps) and idx < max(self.data.dateTimestamps):
                text = self._makeLabel(idx)
                self.label.setHtml(text)
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())
            
    def _makeLabel(self, ts):
        # given timestamp in seconds, find nearest date and speed
        idx = (np.abs(self.data.dateTimestamps - ts)).argmin()
        
        d = {}
        d['date'] = self.data.date[idx]
        d['speed'] = f"Avg. speed: {self.speed[idx]:.3f} km/h"
        d['distance'] = f"Distance: {self.data.distance[idx]} km"
        d['calories'] = f"Calories: {self.data.calories[idx]}"
        d['time'] = f"Time: {self.data.time[idx]}"
        
        fontSize = "font-size: 12pt"
        
        html = ""
        for key, value in d.items():
            if key in self.style.keys():
                colour = self.style[key]['colour']
                style = f"'{fontSize}; color: {colour}'"
            else:
                style = f"'{fontSize}'"
            html += f"<div style={style}>{value}</div>"
        
        return html
    