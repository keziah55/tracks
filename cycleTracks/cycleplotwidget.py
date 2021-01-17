#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subclass of PyQtGraph.PlotWidget to plot cycling data. 
"""

from pyqtgraph import (PlotWidget, DateAxisItem, PlotCurveItem, ViewBox, mkPen, 
                       mkBrush, InfiniteLine)
import numpy as np
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtWidgets import QVBoxLayout, QWidget

from cycledata import CycleData
from cycleplotlabel import CyclePlotLabel


class CyclePlotWidget(QWidget):
    
    def __init__(self, df):
        
        super().__init__()
        
        self.layout = QVBoxLayout()
        self.plotWidget = _CyclePlotWidget(df)
        self.plotLabel = CyclePlotLabel(self.plotWidget.style)
        self.plotWidget.currentPoint.connect(self.plotLabel.setLabels)
        
        self.layout.addWidget(self.plotWidget)
        self.layout.addWidget(self.plotLabel)
        
        self.setLayout(self.layout)
        

class _CyclePlotWidget(PlotWidget):
    """ Sublcass of PyQtGraph.PlotWidget to display cycling data.
    
        Parameters
        ----------
        df : pandas.DataFrame
            Dataframe of csv data.
    """
    
    currentPoint = Signal(dict)
    """ **signal**  currentPoint(dict `values`)
        
        Emitted when a point in the plot is hovered over. The dict provides
        the date, speed, distance, calories and time data for the chosen point.
    """
    
    def __init__(self, df):
        super().__init__(axisItems={'bottom': DateAxisItem()})
        
        self.hgltPnt = None
        
        self.data = CycleData(df)
        
        self.style = {'speed':{'colour':"#024aeb",
                               'symbol':'x'},
                      'odometer':{'colour':"#4d4d4d"},# "#"},
                      'distance':{'colour':"#cf0202"},
                      'time':{'colour':"#19b536"},
                      'calories':{'colour':"#ff9100"},
                      'highlightPoint':{'colour':"#faed00"}}
        
        self._initRightAxis()
        
        # plot avg speed
        style = self._makeScatterStyle(**self.style['speed'])
        self.speed = self.data.distance/self.data.timeSecs
        self.plotItem.scatterPlot(self.data.dateTimestamps, self.speed, **style)
        
        # plot monthly total distance        
        style = self._makeFillStyle(self.style['odometer']['colour'])
        dts, odo = self.data.getMonthlyOdometer()
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
        self.vLine = InfiniteLine(angle=90, movable=False)
        self.hLine = InfiniteLine(angle=0, movable=False)
        self.plotItem.addItem(self.vLine, ignoreBounds=True)
        self.plotItem.addItem(self.hLine, ignoreBounds=True)
        
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
        d = {'symbol':symbol, 'symbolPen':pen, 'symbolBrush':brush}
        return d

    @staticmethod
    def _makeFillStyle(colour):
        """ Make style for PlotCurveItem with fill underneath. """
        pen = mkPen(colour)
        brush = mkBrush(colour)
        d = {'pen':pen, 'brush':brush, 'fillLevel':0}
        return d
    
    
    def _highlightPoint(self, point):
        """ Change pen of given point (and reset any previously highlighted
            points). 
        """
        
        pen = mkPen(self.style['highlightPoint']['colour'])
        
        if self.hgltPnt is not None:
            self.hgltPnt.resetPen()
            
        self.hgltPnt = point
        self.hgltPnt.setPen(pen)

    @Slot(object)
    def mouseMoved(self, pos):
        
        if self.plotItem.sceneBoundingRect().contains(pos):
            mousePoint = self.plotItem.vb.mapSceneToView(pos)
            
            idx = int(mousePoint.x())
            if idx > min(self.data.dateTimestamps) and idx < max(self.data.dateTimestamps):
                self._makeLabels(idx)
                pts = self.scatterPointsAtX(mousePoint, self.plotItem.listDataItems()[0].scatter)
                if len(pts) != 0:
                    self._highlightPoint(pts[0])
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())
            
    def _makeLabels(self, ts):
        # given timestamp in seconds, find nearest date and speed
        idx = (np.abs(self.data.dateTimestamps - ts)).argmin()
        
        d = {}
        d['date'] = self.data.dateFmt[idx]
        d['speed'] = self.speed[idx]
        d['distance'] = self.data.distance[idx]
        d['calories'] = self.data.calories[idx]
        d['time'] = self.data.time[idx]
        
        self.currentPoint.emit(d)
        
    def scatterPointsAtX(self, pos, scatter):
        """ Return a list of points on `scatter` under the x-coordinate of the 
            given position `pos`, ignoring the y-coord.
        """
        # Tried to subclass ScatterPlotItem and add this method there, but it
        # messed up the DateAxis
        x = pos.x()
        pw = scatter.pixelWidth()
        pts = []
        for s in scatter.points():
            sp = s.pos()
            ss = s.size()
            sx = sp.x()
            s2x = ss * 0.5
            if scatter.opts['pxMode']:
                s2x *= pw
            if x > sx-s2x and x < sx+s2x:
                pts.append(s)
        return pts[::-1]