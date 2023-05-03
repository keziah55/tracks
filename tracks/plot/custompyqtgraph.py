"""
Subclasses of pyqtgraph items. 
"""

from pyqtgraph import DateAxisItem, ViewBox, AxisItem, PlotItem
from qtpy.QtCore import Signal
from datetime import datetime

class CustomAxisItem(AxisItem):
    """ Subclass of pyqtgraph.AxisItem, with a `tickFormatter` property.
    
        This can be set to a function which will format this axis' tick values
        as strings in the desired way (e.g. as hh:mm:ss). 
        
        To switch back to default tick spacing, set `tickFormatter` to None.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tickFormatter = None
        
    @property
    def tickFormatter(self):
        return self._tickFormatter
    
    @tickFormatter.setter
    def tickFormatter(self, func):
        self._tickFormatter = func
        
    def tickStrings(self, values, *args, **kwargs):
        if self.tickFormatter is not None:
            return [self.tickFormatter(v) for v in values]
        else:
            return super().tickStrings(values, *args, **kwargs)
        
class CustomDateAxisItem(DateAxisItem):
    """ DateAxisItem that emits `axisDoubleClicked` signal when the axis is 
        double clicked. 
        
        This signal is emitted with timestamps of the surrounding ticks.
    """
    
    axisDoubleClicked = Signal(float, float)
    """ **signal** axisDoubleClicked(float `ts0`, float `ts1`)
    
        Emitted when the axis is double clicked, along with timestamps of the
        surrounding ticks.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tickXs = None
        self.tickVals = None
        # bug workaround - we don't need units/SI prefix on dates
        # this has been fixed in the pyqtgraph source, so won't be necessary
        # once this makes its way into the deb packages
        self.enableAutoSIPrefix(False)
        
    @property
    def tickTimestamps(self):
        """ Return list of tick values, with added timestamps for the months 
            preceding and succeding the tickVals. 
            
            If tickVals is None, return empty list.
        """
        if self.tickVals is None or len(self.tickVals) == 0:
            return []
            
        dt = datetime.fromtimestamp(self.tickVals[0])
        month = dt.month - 1
        year = dt.year
        if month == 0:
            month = 12
            year = year - 1
        ts0 = datetime(year, month, 1).timestamp()
        
        dt = datetime.fromtimestamp(self.tickVals[-1])
        month = dt.month + 1
        year = dt.year
        if month > 12:
            month = 1
            year = year + 1
        ts1 = datetime(year, month, 1).timestamp()
        
        tickVals = [ts0] + self.tickVals + [ts1]
        tickVals.sort()
        
        return tickVals
    
    def mouseClickEvent(self, event):
        """ Override mouseClickEvent to check for double clicks. """
        if event.double() and self.tickXs is not None:
            # positive y coord is underneath axis, not within plot
            if event.pos().y() >= 0:
                x = event.pos().x()
                # get coords of ticks, plus beginning and end
                tickXs = [0] + self.tickXs + [self.boundingRect().width()]
                tickXs.sort()
                                
                for n in range(len(tickXs)-1):
                    # find ticks between which the mouse was clicked
                    tk0 = tickXs[n]
                    tk1 = tickXs[n+1]
                    if tk0 <= x < tk1:
                        # when found, emit signal with corresponding timestamps
                        self.axisDoubleClicked.emit(self.tickTimestamps[n], self.tickTimestamps[n+1])
                        break
        else:
            super().mouseClickEvent(event)
        
    def generateDrawSpecs(self, *args, **kwargs):
        """ Override `generateDrawSpecs` to store `tickXs` from tickSpecs."""
        axisSpec, tickSpecs, textSpecs = super().generateDrawSpecs(*args, **kwargs)
        self.tickXs = [point.x() for _, point, _ in tickSpecs]
        return axisSpec, tickSpecs, textSpecs
    
    def tickValues(self, *args, **kwargs):
        """ Override tickValues to make `tickVals` list. """
        tickVals = super().tickValues(*args, **kwargs)
        self.tickVals = []
        for _, values in tickVals:
            self.tickVals += values
        self.tickVals.sort()
        return tickVals
    
class CustomViewBox(ViewBox):
    """ ViewBox subclass that stores the current xRange and yRange as properties. """
    
    def __init__(self, *args, **kwargs):
        self.xRange = None
        self.yRange = None
        super().__init__(*args, **kwargs)
        
    @property
    def xRange(self):
        return self._xRange
    
    @xRange.setter
    def xRange(self, rng):
        self._xRange = rng
    
    @property
    def yRange(self):
        return self._yRange
    
    @yRange.setter
    def yRange(self, rng):
        self._yRange = rng
    
    def setRange(self, rect=None, xRange=None, yRange=None, **kwargs):
        if rect is not None:
            self.xRange = [rect.left(), rect.right()]
            self.yRange = [rect.top(), rect.bottom()]
        if xRange is not None:
            self.xRange = xRange
        if yRange is not None:
            self.yRange = yRange
        super().setRange(rect, xRange, yRange, **kwargs)
        
class CustomPlotItem(PlotItem):
    """ PlotItem without autoBtn """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.autoBtn = None
            
    def resizeEvent(self, ev):
        return None
        
    def updateButtons(self):
        return None