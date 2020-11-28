#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subclass PyQtGraph.PlotItem and PyQtGraph.ScatterPlotItem, in order to add
the method :py:meth:`pointsAtX` to ScatterPlotItem. This method returns a list
of points under the x-coordinate of a given position and ignores the y-coord.
"""

from pyqtgraph import PlotItem, PlotDataItem, ScatterPlotItem


class CycleTracksPlotItem(PlotItem):
    
    def plot(self, *args, **kargs):
        """
        Add and return a new plot.
        See :func:`PlotDataItem.__init__ <pyqtgraph.PlotDataItem.__init__>` for data arguments
        
        Extra allowed arguments are:
            clear    - clear all plots before displaying new data
            params   - meta-parameters to associate with this data
        """
        clear = kargs.get('clear', False)
        params = kargs.get('params', None)
          
        if clear:
            self.clear()
            
        item = PlotDataItem(*args, **kargs)
        item.scatter = CycleTracksScatterPlotItem()
        item.scatter.setParentItem(item)
        item.scatter.sigClicked.connect(item.scatterClicked)
        item.setData(*args, **kargs)
            
        if params is None:
            params = {}
        self.addItem(item, params=params)
        
        return item
    


class CycleTracksScatterPlotItem(ScatterPlotItem):
    
    def pointsAtX(self, pos):
        x = pos.x()
        pw = self.pixelWidth()
        pts = []
        for s in self.points():
            sp = s.pos()
            ss = s.size()
            sx = sp.x()
            s2x = ss * 0.5
            if self.opts['pxMode']:
                s2x *= pw
            if x > sx-s2x and x < sx+s2x:
                pts.append(s)
        return pts[::-1]