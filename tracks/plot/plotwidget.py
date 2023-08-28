"""
Widget containing plot and labels.
"""

from datetime import datetime, timedelta
from pathlib import Path
from pyqtgraph import (PlotWidget as _PlotWidget, PlotCurveItem, mkPen, mkBrush, 
                       InfiniteLine, setConfigOptions)
import numpy as np
from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from customQObjects.core import Settings

from .plotlabel import PlotLabel
from .plottoolbar import PlotToolBar
from .custompyqtgraph import (CustomPlotItem, CustomAxisItem, CustomDateAxisItem, 
                              CustomViewBox)
from tracks.util import floatToHourMinSec

class PlotWidget(QWidget):
    """ Widget to display cycling data and labels showing data at the point
        under the mouse.
    
        Parameters
        ----------
        parent : Tracks
            Tracks main window object.
        style : str, optional
            Plot style to apply.
    """
    
    currentPointChanged = Signal(dict)
    """ **signal**  currentPointChanged(dict `values`)
        
        Emitted when a point in the plot is hovered over. The dict provides
        the date, speed, distance, calories and time data for the chosen point.
    """
    
    pointSelected = Signal(object)
    """ **signal** pointSelected(datetime `currentPoint`)
        
        Emitted when the plot is double clicked, with the date from the
        current point.
    """
    
    def __init__(self, parent, style="dark"):
        
        super().__init__()
        
        self.plotState = None
        self.plotLabel = None
        self.parent = parent
        
        self.plotToolBar = PlotToolBar()
        self._makePlot(parent, style=style)
        
        self.plotLayout = QHBoxLayout()
        self.plotLayout.addWidget(self.plotWidget)
        self.plotLayout.addWidget(self.plotToolBar)
        self.layout = QVBoxLayout()
        self.layout.addLayout(self.plotLayout)
        self.layout.addWidget(self.plotLabel)
        
        self.setLayout(self.layout)
        
    def _makePlot(self, *args, **kwargs):
        self.plotWidget = Plot(*args, **kwargs)
        if self.plotLabel is None:
            self.plotLabel = PlotLabel(self.plotWidget.style)
        else:
            self.plotLabel.setStyle(self.plotWidget.style)
        self.plotLabel.labelClicked.connect(self.plotWidget.switchSeries)
        self.plotWidget.currentPointChanged.connect(self.plotLabel.setLabels)
        self.plotWidget.pointSelected.connect(self.pointSelected)
        
        self.plotToolBar.viewAllClicked.connect(self.plotWidget.viewAll)
        self.plotToolBar.viewRangeClicked.connect(self.plotWidget.resetMonthRange)
        self.plotToolBar.highlightPBClicked.connect(self.plotWidget._highlightPBs)
        
    @Slot(object)
    def newData(self, idx=None):
        self.plotWidget.updatePlots()
        
    @Slot(object)
    def setCurrentPointFromDate(self, date):
        self.plotWidget.setCurrentPointFromDate(date)
        
    @Slot(object, bool)
    def setXAxisRange(self, months, fromRecentSession=True):
        self.plotWidget.setXAxisRange(months, fromRecentSession=fromRecentSession)
        
    @Slot(str)
    def setStyle(self, style, force=False):
        if force or self.plotWidget.style.name != style:
            self.plotState = self.plotWidget.getState()
            self.plotLayout.removeWidget(self.plotWidget)
            self.plotWidget.deleteLater()
            self._makePlot(self.parent, style=style)
            self.plotWidget.setState(self.plotState)
            self.plotLayout.insertWidget(0, self.plotWidget)
            
    def addCustomStyle(self, name, style, setStyle=True):
        self.plotWidget.style.addStyle(name, style)
        if setStyle:
            self.setStyle(name, force=True)
        
    def removeCustomStyle(self, name):
        # TODO remove style from file
        # and update current?
        self.plotWidget.style.removeStyle(name)
            
    def getStyle(self, name):
        return self.plotWidget.style.getStyleDict(name)
    
    def getStyleKeys(self):
        return self.plotWidget.style.keys
    
    def getStyleSymbolKeys(self):
        return self.plotWidget.style.symbolKeys
    
    def getValidStyles(self):
        return self.plotWidget.style.validStyles
    
    def getDefaultStyles(self):
        return self.plotWidget.style.defaultStyles

class Plot(_PlotWidget):
    """ Sublcass of PyQtGraph.PlotWidget to display cycling data.
    
        Parameters
        ----------
        parent : QMainWindow
            Main window.
    """
    
    currentPointChanged = Signal(dict)
    """ **signal**  currentPointChanged(dict `values`)
        
        Emitted when a point in the plot is hovered over. The dict provides
        the date, speed, distance, calories and time data for the chosen point.
    """
    
    pointSelected = Signal(object)
    """ **signal** pointSelected(datetime `currentPoint`)
        
        Emitted when the plot is double clicked, with the date from the
        current point.
    """
    
    def __init__(self, parent, style="dark"):
        
        self._ySeries = None
        self.plotItem = None
        self.style = PlotStyle(style)
        self.setStyle(style)
        
        self.dateAxis = CustomDateAxisItem()
        self.plotItem = CustomPlotItem(viewBox=CustomViewBox(), 
                         axisItems={'bottom':self.dateAxis, 'left':CustomAxisItem('left')})
        super().__init__(plotItem=self.plotItem)
        
        self.dateAxis.axisDoubleClicked.connect(self.setPlotRange)
        
        self.hgltPnt = None
        
        self.parent = parent
        
        self.plottable = ['speed', 'distance', 'time', 'calories']
        
        self._initRightAxis()
        
        # axis labels
        self.plotItem.setLabel('bottom',text='Date')
        
        # show grid on left and bottom axes
        self.plotItem.getAxis('left').setGrid(255)
        self.plotItem.getAxis('bottom').setGrid(255)
        
        # cross hairs
        self.vLine = InfiniteLine(angle=90, movable=False)
        self.hLine = InfiniteLine(angle=0, movable=False)
        self.plotItem.addItem(self.vLine, ignoreBounds=True)
        self.plotItem.addItem(self.hLine, ignoreBounds=True)
        
        self.plotItem.scene().sigMouseMoved.connect(self.mouseMoved)
        self.plotItem.scene().sigMouseClicked.connect(self.plotClicked)
        
        # update second view box
        self.updateViews()
        self.plotItem.vb.sigResized.connect(self.updateViews)
        
        self.currentPoint = {}
        
        self._prevHgltPointColour = None
        
        # all points that are/were PBs can be highlighted
        self._showPBs = False
        self._regenerateCachedPBs = {key:False for key in self.plottable}
        self.hgltPBs = {key:[] for key in self.plottable}
        
        self.viewMonths = None
        
        self.setYSeries('speed')
        self.plotTotalDistance()
        
    @property
    def data(self):
        return self.parent.data
        
    def _initRightAxis(self):
        self.vb2 = CustomViewBox()
        self.plotItem.showAxis('right')
        self.plotItem.scene().addItem(self.vb2)
        self.plotItem.getAxis('right').linkToView(self.vb2)
        self.vb2.setXLink(self.plotItem)
        
    @property
    def viewBoxes(self):
        """ Return list of all viexBoxes in the plot. """
        vbx = [self.plotItem.vb]
        if hasattr(self, 'vb2'):
            vbx.append(self.vb2)
        return vbx
        
    @Slot()
    def updateViews(self):
        ## Copied from PyQtGraph MultiplePlotAxes.py example ##
        # view has resized; update auxiliary views to match
        self.vb2.setGeometry(self.plotItem.vb.sceneBoundingRect())
        # need to re-update linked axes since this was called
        # incorrectly while views had different shapes.
        # (probably this should be handled in ViewBox.resizeEvent)
        self.vb2.linkedViewChanged(self.plotItem.vb, self.vb2.XAxis)
        
    def getState(self):
        state = {}
        state['ySeries'] = self.ySeries
        for n, vb in enumerate(self.viewBoxes):
            key = f"vb{n}State"
            state[key] = vb.getState()
        if self.currentPoint:
            state['currentPoint'] = self.currentPoint['index']
        return state
    
    def setState(self, state):
        self.ySeries = state['ySeries']
        for n, vb in enumerate(self.viewBoxes):
            key = f"vb{n}State"
            vb.setState(state[key])
        if len(self.viewBoxes) > 1:
            self.viewBoxes[1].setXLink(self.plotItem)
        if 'currentPoint' in state:
            self.setCurrentPoint(state['currentPoint'])
        
    def setStyle(self, style):
        self.style.name = style
        dct = {'foreground':self.style.foreground,
               'background':self.style.background}
        setConfigOptions(**dct)
        if self.plotItem is not None:
            self.plotItem.setButtonPixmaps()
        if self.ySeries is not None:
            self.updatePlots()
            
    @Slot()
    def viewAll(self):
        # enableAutoRange on both viewBoxes
        for vb in self.viewBoxes:
            vb.enableAutoRange()
        self.updateHighlightPBs()
        
    @Slot()
    def resetMonthRange(self):
        if self.viewMonths is not None:
            self.setXAxisRange(self.viewMonths)
        self.updateHighlightPBs()
    
    @Slot(float, float)
    def setPlotRange(self, x0, x1):
        """ Set range of both view boxes to cover the points between the two
            given timestamps.   
        """
        # apply to both the current scatter and background plot
        if not hasattr(self, 'dataItem') or not hasattr(self, 'backgroundItem'):
            return None
        xRange0, xRange1 = self.viewBoxes[0].xRange
        data = [(self.dataItem.scatter.data['x'], self.dataItem.scatter.data['y'], 
                 self.viewBoxes[0]),
                (self.backgroundItem.xData, self.backgroundItem.yData, 
                 self.viewBoxes[1])]
        
        for xPoints, yData, viewBox in data:
            # find x-coords of points in the given month
            mask = np.in1d(np.where(xPoints >= x0)[0], np.where(xPoints <= x1)[0])
            if np.any(mask):
                # select the corresponding y data
                idx = np.where(xPoints >= x0)[0][mask]
                yPoints = yData[idx]
                # get min and max
                y0 = np.min(yPoints)
                y1 = np.max(yPoints)
                # set min and max for x and y in the viewBox
                viewBox.setRange(xRange=(x0, x1), yRange=(y0, y1))
                
    @Slot(object, bool)
    def setXAxisRange(self, months, fromRecentSession=True):
        """ Scale the plot to show the most recent `months` months. 
        
            If `fromRecentSession` is True (default), the month range is calculated
            relative to the most recent session in the `Data` object.
            Otherwise, it is calculated from the current date.
            These two options are equivalent if there are sessions from the current
            month in the `Data` object.
        """
        if self.data.df.empty:
            return
        self.viewMonths = months
        if fromRecentSession:
            ts1 = self.data.dateTimestamps[-1]
        else:
            now = datetime.now()
            ts1 = now.timestamp()
            if months is not None and now.month != self.data.datetimes[-1].month:
                months -= now.month - self.data.datetimes[-1].month
        if months is None:
            ts0 = self.data.dateTimestamps[0]
        else:
            days = self.viewMonths * 365 / 12 # number of days to go back
            td = timedelta(days=days)
            ts0 = (datetime.fromtimestamp(ts1) - td).timestamp()
        self.setPlotRange(ts0, ts1)
        
    @Slot()
    def updatePlots(self):
        self.plotSeries(self.ySeries, mode='set')
        self.plotTotalDistance(mode='set')
        self.resetMonthRange()
        self._regenerateCachedPBs = {key:True for key in self._regenerateCachedPBs}
        
    @property
    def ySeries(self):
        return self._ySeries
    
    @ySeries.setter 
    def ySeries(self, key):
        self._ySeries = key
        self.plotSeries(self.ySeries)
        
    def setYSeries(self, key):
        self.ySeries = key
    
    def plotSeries(self, key, mode='new'):
        """ Plot given series on y1 axis. """
        label = self.data.quickNames[key]
        # get series and set axis tick formatter
        if key == 'time':
            series = self.data.timeHours
            self.plotItem.getAxis('left').tickFormatter = floatToHourMinSec
        else:
            series = self.data[label]
            self.plotItem.getAxis('left').tickFormatter = None
        # make style
        styleDict = self.style[key]
        style = self._makeScatterStyle(**styleDict)
        # make or update plot
        if mode == 'new':
            self.dataItem = self.plotItem.scatterPlot(self.data.dateTimestamps, 
                                                      series, **style)
            self.plotItem.vb.sigRangeChanged.connect(self.updateHighlightPBs)
        elif mode == 'set':
            self.dataItem.setData(self.data.dateTimestamps, series, **style)
        # set axis label
        self.plotItem.setLabel('left', text=label, color=styleDict['colour'])
        # retain plot range when switching series
        if self.viewBoxes[0].xRange is not None:
            self.setPlotRange(*self.viewBoxes[0].xRange)
        # if PBs were highlighted, highlight again
        self.updateHighlightPBs()
        
    def plotTotalDistance(self, mode='new'):
        """ Plot monthly total distance. """
        colour = self.style['odometer']['colour']
        style = self._makeFillStyle(colour)
        dts, odo = self.data.getMonthlyOdometer()
        dts = [dt.timestamp() for dt in dts]
        if mode == 'new':
            self.backgroundItem = PlotCurveItem(dts, odo, **style)
            self.vb2.addItem(self.backgroundItem)
        elif mode == 'set':
             self.backgroundItem.setData(dts, odo, **style)
        self.plotItem.getAxis('right').setLabel('Total monthly distance', 
            color=colour)
        
    @Slot(str)
    def switchSeries(self, key):
        if key in self.plottable and key in self.data.quickNames.keys():
            self.plotItem.removeItem(self.dataItem)
            self.ySeries = key
            
    @Slot(object)
    def plotClicked(self, event):
        """ If the plot is clicked, emit `pointSelected` signal with 
            `currentPoint` datetime.  
        """
        # get x and y bounds
        yMin = 0 # no top axis
        yMax = self.plotItem.getAxis('bottom').scenePos().y()
        # left axis position is 1,1 (don't know why), so use the bottom axis x here
        xMin = self.plotItem.getAxis('bottom').scenePos().x() 
        xMax = self.plotItem.getAxis('right').scenePos().x()
        
        pos = event.scenePos()
        if xMin <= pos.x() <= xMax and yMin <= pos.y() <= yMax: # event.double() and 
            idx = self.currentPoint['index']
            date = self.data.datetimes[idx]
            self.pointSelected.emit(date)
        
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
    
    @property
    def currentPoint(self):
        return self._point
    
    @currentPoint.setter
    def currentPoint(self, value):
        self._point = value
    
    def setCurrentPoint(self, idx):
        """ Set the `currentPoint` dict from index `idx` in the `data` DataFrame
            and emit `currentPointChanged` signal.
        """
        self.currentPoint['index'] = idx
        self.currentPoint['date'] = self.data.datetimes[idx].strftime("%a %d %b %Y")
        self.currentPoint['speed'] = self.data.speed[idx]
        self.currentPoint['distance'] = self.data.distance[idx]
        self.currentPoint['calories'] = self.data.calories[idx]
        self.currentPoint['time'] = self.data.time[idx]
        self.currentPointChanged.emit(self.currentPoint)
        
    @Slot(object)
    def setCurrentPointFromDate(self, date):
        """ Find point at the given date and highlight it. """
        dt = datetime(date.year, date.month, date.day)
        idx = self.data.datetimes.index(dt)
        pt = self.dataItem.scatter.points()[idx]
        self.ensurePointVisible(pt)
        self._highlightPoint(pt)
        self.setCurrentPoint(idx)
        
    def ensurePointVisible(self, pt):
        ts = pt.pos().x()
        x0, x1 = self.viewBoxes[0].xRange
        if ts < x0:
            x0 = ts - 1e6
        elif ts > x1:
            x1 = ts + 1e6
        self.setPlotRange(x0, x1)
        
    @Slot(object)
    def _highlightPoint(self, point=None):
        """ Change pen and brush of given point (and reset any previously 
            highlighted points). 
        """
        if point is None:
            if self.hgltPnt is not None:
                point = self.hgltPnt
            else:
                return None
        
        # reset previous hgltPoint pen and brush
        if self._prevHgltPointColour is not None:
            pen = mkPen(self._prevHgltPointColour)
            brush = mkBrush(self._prevHgltPointColour)
            try:
                self.hgltPnt.setPen(pen)
                self.hgltPnt.setBrush(brush)
            except:
                pass
        # store current colour of new hgltPoint
        self._prevHgltPointColour = point.pen().color().name()
        
        # set colour of new point
        colour = self.style['highlightPoint']['colour']
        pen = mkPen(colour)
        brush = mkBrush(colour)
        self.hgltPnt = point
        self.hgltPnt.setPen(pen)
        self.hgltPnt.setBrush(brush)
        
    @Slot(bool)
    def _highlightPBs(self, show):
        """ Highlight points that are, or were, PBs. """
        if show:
            self._showPBs = True
            if self._regenerateCachedPBs[self.ySeries] or len(self.hgltPBs[self.ySeries]) == 0:
                self.hgltPBs[self.ySeries] = self._getPBs()
                self._regenerateCachedPBs[self.ySeries] = False
            for idx in self.hgltPBs[self.ySeries]:
                pt = self.dataItem.scatter.points()[idx]
                colour = self.style['highlightPoint']['colour']
                pen = mkPen(colour)
                brush = mkBrush(colour)
                pt.setPen(pen)
                pt.setBrush(brush)
        else:
            self._showPBs = False
            for idx in self.hgltPBs[self.ySeries]:
                pt = self.dataItem.scatter.points()[idx]
                pt.resetPen()
                pt.resetBrush()
                
    def updateHighlightPBs(self):
        if self._showPBs:
            self._highlightPBs(self._showPBs)
        
    def _getPBs(self):
        """ Return array of points that represent(ed) a PB in the current series. """
        num = self.parent.settings.value("pb/numSessions", cast=int)
        return self.data.getPBs(self.ySeries, num)
        # get number of top sessions and current y series
        col = self.data.quickNames[self.ySeries]
        num = self.parent.settings.value("pb/numSessions", cast=int)
        series = self.data[col]
        best = series[:num]
        idx = list(range(num)) # first num values will be PBs
        for n in range(num, len(series)):
            if series[n] >= np.min(best):
                idx.append(n)
                # replace value in best array
                minIdx = np.argmin(best)
                best[minIdx] = series[n]
        return idx
        
    @Slot(object)
    def mouseMoved(self, pos):
        if not self.data.df.empty and self.plotItem.sceneBoundingRect().contains(pos):
            mousePoint = self.plotItem.vb.mapSceneToView(pos)
            
            idx = int(mousePoint.x())
            if idx > min(self.data.dateTimestamps) and idx < max(self.data.dateTimestamps):
                self._setCurrentPointFromTimestamp(idx)
                pts = self.scatterPointsAtX(mousePoint, self.dataItem.scatter)
                if len(pts) != 0:
                    # could be multiple points at same x, so get closest point to mouse by y value
                    yVals = np.array([pt.pos().y() for pt in pts])
                    idx = (np.abs(yVals - mousePoint.y())).argmin()
                    self._highlightPoint(pts[idx])
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())
            
    def _setCurrentPointFromTimestamp(self, ts):
        # given timestamp in seconds, find nearest date and speed
        idx = (np.abs(self.data.dateTimestamps - ts)).argmin()
        self.setCurrentPoint(idx)
        
    @staticmethod
    def scatterPointsAtX(pos, scatter):
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
    

class PlotStyle:
    """ Class to manage plot styles. 
    
        Does not store the style directly, but gets (and sets) from a 
        Settings object, which manages the plotStyles.ini file.
        
        The default styles "dark" and "light" will be written to the file in 
        the constructor, if they do not exist in the file.
    """
    
    defaultStyles = ["dark", "light"]
    
    def __init__(self, style="dark"):
        
        plotStyleFile = Path(Settings().fileName()).parent.joinpath('plotStyles.ini')
        self.settings = Settings(str(plotStyleFile), Settings.NativeFormat)
        
        self.keys = ['speed', 'distance', 'time', 'calories', 'odometer', 
                     'highlightPoint', 'foreground', 'background']
        self.symbolKeys = ['speed', 'distance', 'time', 'calories']
        
        # make defaults
        darkDefault = ["#024aeb", "#cf0202", "#19b536", "#ff9100", "#4d4d4d",
                       "#faed00", "#969696", "#000000"]
        lightDefault = ["#0981cb", "#d80d0d", "#2bb512", "#ff9100", "#9f9f9f",
                        "#deb009", "#4d4d4d", "#ffffff"]
        defaults = {'dark':dict(zip(self.keys, darkDefault)),
                    'light':dict(zip(self.keys, lightDefault))}
        defaultSymbols = {key:'x' for key in self.symbolKeys}
        
        for styleName, styleDct in defaults.items():
            if styleName not in self.settings.childGroups():
                self.settings.beginGroup(styleName)
                for key, colour in styleDct.items():
                    self.settings.setValue(key, colour)
                for key, symbol in defaultSymbols.items():
                    self.settings.setValue(f"{key}Symbol", symbol)
                self.settings.endGroup()
        
        self.name = style
        
    @property
    def name(self):
        return self._styleName

    @name.setter 
    def name(self, name):
        if name.lower() not in self.validStyles:
            msg = f"Plot style must be one of {', '.join(self.validStyles)}, not '{name}'."
            raise ValueError(msg)
        self._styleName = name.lower()
        
    @property 
    def validStyles(self):
        return self.settings.childGroups()
        
    def __getattr__(self, name):
        if name in self.keys:
            return self._getStyle(name)
        else:
            return self.__getattribute__(name)
        
    def __getitem__(self, name):
        if name in self.keys: 
            return self._getStyle(name)
        else:
            raise KeyError(f"PlotStyle has no field '{name}'")
            
    def _getStyle(self, field):
        if field in ['foreground', 'background']:
            return self.settings.value(f"{self.name}/{field}")
        
        dct = {'colour':self.settings.value(f"{self.name}/{field}")}
        symbol = self.settings.value(f"{self.name}/{field}Symbol")
        if symbol is not None:
            dct['symbol'] = symbol
        return dct
    
    def getStyleDict(self, name=None):
        if name is None:
            name = self.name
        style = {}
        for field in self.keys:
            dct = {'colour':self.settings.value(f"{name}/{field}")}
            symbol = self.settings.value(f"{name}/{field}Symbol")
            if symbol is not None:
                dct['symbol'] = symbol
            style[field] = dct
        return style
    
    def addStyle(self, name, style):
        self.settings.beginGroup(name)
        for key, value in style.items():
            self.settings.setValue(key, value)
        self.settings.endGroup()
    
    def removeStyle(self, name):
        self.settings.remove(name)