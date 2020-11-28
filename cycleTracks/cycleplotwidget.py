#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subclass of pyqtgraph.PlotWidget.
"""

from pyqtgraph import (PlotWidget, DateAxisItem, PlotCurveItem, ViewBox, mkPen, 
                       mkBrush, InfiniteLine)
import numpy as np
from PyQt5.QtCore import pyqtSlot as Slot
from .cycledata import CycleData
    

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
    