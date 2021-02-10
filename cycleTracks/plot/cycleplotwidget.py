"""
Widget containing plot and labels.
"""

from pyqtgraph import PlotWidget, PlotCurveItem, ViewBox, mkPen, mkBrush, InfiniteLine
import numpy as np
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtWidgets import QVBoxLayout, QWidget

from .cycleplotlabel import CyclePlotLabel
from .custompyqtgraph import CustomAxisItem, CustomDateAxisItem, CustomViewBox
from cycleTracks.util import floatToHourMinSec

# TODO if date label clicked, highlight in tree
# TODO scale y axis when changing series when zoomed in on month

    
class CyclePlotWidget(QWidget):
    """ Widget to display cycling data and labels showing data at the point
        under the mouse.
    
        Parameters
        ----------
        data : CycleData
            CycleData object.
    """
    
    currentPointChanged = Signal(dict)
    """ **signal**  currentPointChanged(dict `values`)
        
        Emitted when a point in the plot is hovered over. The dict provides
        the date, speed, distance, calories and time data for the chosen point.
    """
    
    def __init__(self, parent):
        
        super().__init__()
        
        self.layout = QVBoxLayout()
        self.plotWidget = _CyclePlotWidget(parent)
        self.plotLabel = CyclePlotLabel(self.plotWidget.style)
        self.plotLabel.labelClicked.connect(self.plotWidget.switchSeries)
        self.plotWidget.currentPointChanged.connect(self.plotLabel.setLabels)
        
        self.plotWidget.currentPointChanged.connect(self.currentPointChanged)
        
        self.layout.addWidget(self.plotWidget)
        self.layout.addWidget(self.plotLabel)
        
        self.setLayout(self.layout)
        
    @Slot(object)
    def newData(self, index):
        self.plotWidget.updatePlots(index)
        

class _CyclePlotWidget(PlotWidget):
    """ Sublcass of PyQtGraph.PlotWidget to display cycling data.
    
        Parameters
        ----------
        data : CycleData
            CycleData object.
    """
    
    currentPointChanged = Signal(dict)
    """ **signal**  currentPointChanged(dict `values`)
        
        Emitted when a point in the plot is hovered over. The dict provides
        the date, speed, distance, calories and time data for the chosen point.
    """
    
    def __init__(self, parent):
        self.dateAxis = CustomDateAxisItem()
        super().__init__(axisItems={'bottom':self.dateAxis, 'left':CustomAxisItem('left')},
                         viewBox=CustomViewBox())
        
        # disconnect autoBtn from its slot and connect to new slot that will
        # auto scale both viewBoxes
        self.plotItem.autoBtn.clicked.disconnect(self.plotItem.autoBtnClicked)
        self.plotItem.autoBtn.clicked.connect(self.autoBtnClicked)
        
        self.dateAxis.zoomOnMonth.connect(self.axisDoubleClicked)
        
        self.hgltPnt = None
        
        self.parent = parent
        
        self.style = {'speed':{'colour':"#024aeb",
                               'symbol':'x'},
                      'distance':{'colour':"#cf0202",
                                  'symbol':'x'},
                      'time':{'colour':"#19b536",
                              'symbol':'x'},
                      'calories':{'colour':"#ff9100",
                                  'symbol':'x'},
                      'odometer':{'colour':"#4d4d4d"},# "#"},
                      'highlightPoint':{'colour':"#faed00"}}
        
        self.plottable = ['speed', 'distance', 'time', 'calories']
        
        self._initRightAxis()
        
        self.setYSeries('speed')
        self.plotTotalDistance()
        
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
        
        # update second view box
        self.updateViews()
        self.plotItem.vb.sigResized.connect(self.updateViews)
        
        self.currentPoint = {}
        
    @property
    def data(self):
        return self.parent.data
        
    def _initRightAxis(self):
        self.vb2 = ViewBox()
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
        
    def autoBtnClicked(self):
        # enableAutoRange on both viewBoxes
        if self.plotItem.autoBtn.mode == 'auto':
            for vb in self.viewBoxes:
                vb.enableAutoRange()
            self.plotItem.autoBtn.hide()
        else:
            self.plotItem.disableAutoRange()
        
    @Slot(float, float)
    def axisDoubleClicked(self, x0, x1):
        """ Set range of both view boxes to cover the time between the given timestamps. """
        # apply to both the current scatter and background plot
        if not hasattr(self, 'dataItem') or not hasattr(self, 'backgroundItem'):
            return None
        data = [(self.dataItem.scatter.data['x'], self.dataItem.scatter.data['y'], 
                 self.viewBoxes[0]),
                (self.backgroundItem.xData, self.backgroundItem.yData, 
                 self.viewBoxes[1])]
        
        for xPoints, yData, viewBox in data:
            # find x-coords of points in the given month
            mask = np.in1d(np.where(xPoints > x0)[0], np.where(xPoints < x1)[0])
            if np.any(mask):
                # select the corresponding y data
                idx = np.where(xPoints > x0)[0][mask]
                yPoints = yData[idx]
                # get min and max
                y0 = np.min(yPoints)
                y1 = np.max(yPoints)
                # set min and max for x and y in the viewBox
                viewBox.setRange(xRange=(x0, x1), yRange=(y0, y1))
               
    @Slot(object)
    def updatePlots(self, index):
        self.plotSeries(self.ySeries, mode='set')
        self.plotTotalDistance(mode='set')
        
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
        if key == 'time':
            series = self.data.timeHours
            self.plotItem.getAxis('left').tickFormatter = floatToHourMinSec
        else:
            series = self.data[label]
            self.plotItem.getAxis('left').tickFormatter = None
        styleDict = self.style[key]
        style = self._makeScatterStyle(**styleDict)
        if mode == 'new':
            self.dataItem = self.plotItem.scatterPlot(self.data.dateTimestamps, 
                                                      series, **style)
        elif mode == 'set':
            self.dataItem.setData(self.data.dateTimestamps, series, **style)
        self.plotItem.setLabel('left', text=label, color=styleDict['colour'])
        
        if self.viewBoxes[0].xRange is not None:
            self.axisDoubleClicked(*self.viewBoxes[0].xRange)
        
        
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
            self.plotSeries(key)
        
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
        self.currentPoint['date'] = self.data.dateFmt[idx]
        self.currentPoint['speed'] = self.data.avgSpeed[idx]
        self.currentPoint['distance'] = self.data.distance[idx]
        self.currentPoint['calories'] = self.data.calories[idx]
        self.currentPoint['time'] = self.data.time[idx]
        self.currentPointChanged.emit(self.currentPoint)
    
    def _highlightPoint(self, point):
        """ Change pen of given point (and reset any previously highlighted
            points). 
        """
        pen = mkPen(self.style['highlightPoint']['colour'])
        
        try:
            # if other points are already highlighted, remove highlighting
            self.hgltPnt.resetPen()
        except (AttributeError, RuntimeError):
            pass
            
        self.hgltPnt = point
        self.hgltPnt.setPen(pen)

    @Slot(object)
    def mouseMoved(self, pos):
        
        if self.plotItem.sceneBoundingRect().contains(pos):
            mousePoint = self.plotItem.vb.mapSceneToView(pos)
            
            idx = int(mousePoint.x())
            if idx > min(self.data.dateTimestamps) and idx < max(self.data.dateTimestamps):
                self._makePointDict(idx)
                pts = self.scatterPointsAtX(mousePoint, self.dataItem.scatter)
                if len(pts) != 0:
                    self._highlightPoint(pts[0])
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())
            
    def _makePointDict(self, ts):
        # given timestamp in seconds, find nearest date and speed
        idx = (np.abs(self.data.dateTimestamps - ts)).argmin()
        self.setCurrentPoint(idx)
        
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
    