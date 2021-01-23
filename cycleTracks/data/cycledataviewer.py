"""
QTreeWidget showing data from cycling DataFrame.
"""

from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QHeaderView
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5.QtGui import QFontMetrics
import re
import calendar
import itertools
from .cycledata import CycleData
from cycleTracks.util import(isHourMinSec, isMonthYear, isNumeric, getHourMinSec, 
                             getMonthYear)

class CycleTreeWidgetItem(QTreeWidgetItem):
    """ QTreeWidgetItem subclass, with __lt__ method overridden, so that 
        the QTreeWidget can sort the items, where each column may contain
        a number, month and year, or time in HH:MM.ss.
    
        This requires a `sortColumn` property to be added. This must be set
        to the desired sort column index on every instance of this object
        before calling `QTreeWidget.sortItems()`. As far as I can tell, the
        `idx` arg to `QTreeWidget.sortItems()` is ignored.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sortColumn = 0
    
    def __lt__(self, other):
        item0 = self.text(self.sortColumn)
        item1 = other.text(self.sortColumn)
        if isNumeric(item0) and isNumeric(item1):
            return float(item0) < float(item1)
        elif isMonthYear(item0) and isMonthYear(item1):
            value0 = getMonthYear(item0)
            value1 = getMonthYear(item1)
            return value0 < value1
        elif isHourMinSec(item0) and isHourMinSec(item1):
            value0 = getHourMinSec(item0)
            value1 = getHourMinSec(item1)
            return value0 < value1
        else:
            return item0 < item1
        
    @property 
    def sortColumn(self):
        return self._sortColumn
    
    @sortColumn.setter 
    def sortColumn(self, value):
        self._sortColumn = value
        

class CycleDataViewer(QTreeWidget):
    """ QTreeWidget showing cycling data, split by month.
    
        Each item in the tree shows a summary: month, total time, total distance,
        max. avg. speed and total calories.
        
        The tree can be sorted by double clicking on the header.
    
        Parameters
        ----------
        data : CycleData
            CycleData object
        widthSpace : int
            Spacing to add to width in `sizeHint`. Default is 5.
    """
    
    def __init__(self, parent, widthSpace=10):
        super().__init__()
        
        self.parent = parent
        
        self.widthSpace = widthSpace
        
        self.headerLabels = ['Date', 'Time', 'Distance (km)', 'Avg. speed\n(km/h)', 
                             'Calories']
        self.setHeaderLabels(self.headerLabels)
        self.header().setStretchLastSection(False)
        # make header tall enough for two rows of text (avg speed has line break)
        font = self.header().font()
        metrics = QFontMetrics(font)
        height = metrics.height()
        self.header().setMinimumHeight(height*2)
        # align header text centrally
        for idx in range(len(self.headerLabels)):
            self.headerItem().setTextAlignment(idx, Qt.AlignCenter)
        
        self.makeTree()
        
        self.sortOrder = [itertools.cycle([Qt.DescendingOrder, Qt.AscendingOrder])
                          for _ in range(len(self.headerLabels))]
        self.header().sectionDoubleClicked.connect(self.sortTree)
        
    def sizeHint(self):
        width = self.header().length() + self.widthSpace
        height = super().sizeHint().height()
        return QSize(width, height)
    
    @property
    def data(self):
        return self.parent.data
    
    @property 
    def topLevelItems(self):
        """ List of top level QTreeWidgetItems. """
        items = [self.topLevelItem(i) for i in range(self.topLevelItemCount())]
        return items
    
    @Slot()
    def newData(self):
        expanded = []
        for item in self.topLevelItems:
            if item.isExpanded():
                expanded.append(item.text(0))
        self.clear()
        self.makeTree()
        for item in self.topLevelItems:
            if item.text(0) in expanded:
                self.expandItem(item)
    
    @Slot(int)
    def sortTree(self, idx):
        """ Sort the tree based on column `idx`. """
        # switch sort order
        order = next(self.sortOrder[idx])
        
        # set sort column index
        for rootItem in self.topLevelItems:
            rootItem.sortColumn = idx
            
        # make header label for sort column italic
        for i in range(self.header().count()):
            font = self.headerItem().font(i)
            if i == idx:
                font.setItalic(True)
            else:
                font.setItalic(False)
            self.headerItem().setFont(i, font)
                
        self.sortItems(idx, order)
        
        
    def makeTree(self):
        """ Populate tree with data from CycleData object. """
        
        dfs = self.data.splitMonths()
        
        for df in reversed(dfs):
            if df.empty:
                continue
            
            # root item of tree: summary of month, with total time, distance
            # and calories (in bold)
            data = CycleData(df) # make CycleData object for the month
            date = df['Date'].iloc[0]
            rootText = [f"{calendar.month_name[date.month]} {date.year}"]
            rootText.append(self._getHMS(sum(data.timeHours)))
            rootText.append(f"{sum(data.distance):.2f}")
            rootText.append(f"{max(data.avgSpeed):.2f}")
            rootText.append(f"{sum(data.calories):.2f}")
            
            rootItem = CycleTreeWidgetItem(self)
            for idx, text in enumerate(rootText):
                rootItem.setText(idx, text)
                rootItem.setTextAlignment(idx, Qt.AlignCenter)
                font = rootItem.font(idx)
                font.setBold(True)
                rootItem.setFont(idx, font)
                
            # make rows of data for tree
            for rowIdx in reversed(range(len(data))):
                item = QTreeWidgetItem(rootItem)
                for idx, col in enumerate(self.headerLabels):
                    col = re.sub(r"\s", " ", col) # remove \n from avg speed
                    value = data[col][rowIdx]
                    if col == 'Date':
                        value = value.strftime("%d %b %Y")
                    elif col != 'Time':
                        value = f"{value:.2f}"
                    item.setText(idx, value)
                    item.setTextAlignment(idx, Qt.AlignCenter)
                    
        self.header().resizeSections(QHeaderView.ResizeToContents)
        
        
    @staticmethod
    def _getHMS(totalHours):
        """ Convert `totalHours` float to hh:mm:ss string. """
        hours, mins = divmod(totalHours, 1)
        mins *= 60
        mins, secs = divmod(mins, 1)
        secs *= 60
        s = f"{hours:02.0f}:{mins:02.0f}:{secs:02.0f}"
        return s
    