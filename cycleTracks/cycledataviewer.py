#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
from cycledata import CycleData


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
        if self._isNumeric(item0) and self._isNumeric(item1):
            return float(item0) < float(item1)
        elif self._isMonthYear(item0) and self._isMonthYear(item1):
            m0, y0 = self._getMonthYear(item0)
            m1, y1 = self._getMonthYear(item1)
            if y0 != y1:
                return y0 < y1
            else:
                return m0 < m1
        elif self._isHourMinSec(item0) and self._isHourMinSec(item1):
            h0, m0, s0 = self._getHourMinSec(item0)
            h1, m1, s1 = self._getHourMinSec(item1)
            if h0 != h1:
                return h0 < h1
            elif m0 != m1:
                return m0 < m1
            else:
                return s0 < s1
        else:
            return item0 < item1
        
    @property 
    def sortColumn(self):
        return self._sortColumn
    
    @sortColumn.setter 
    def sortColumn(self, value):
        self._sortColumn = value
        
    @staticmethod
    def _isNumeric(value):
        try:
            float(value)
            ret = True
        except ValueError:
            ret = False
        return ret
    
    @classmethod 
    def _isMonthYear(cls, value):
        try:
            cls._getMonthYear(value)
            ret = True
        except ValueError:
            ret = False
        return ret
        
    @staticmethod
    def _getMonthYear(value):
        month, year = value.split(' ')
        try:
            idx = list(calendar.month_name).index(month)
        except ValueError:
            try:
                idx = list(calendar.month_abbr).index(month)
            except ValueError:
                raise ValueError(f"{month} is not valid month")
        year = int(year)
        
        return idx, year
    
    @classmethod
    def _isHourMinSec(cls, value):
        try:
            cls._getHourMinSec(value)
            ret = True
        except ValueError:
            ret = False
        return ret

    @staticmethod
    def _getHourMinSec(value):
        hours, minssec = value.split(':')
        mins, secs = minssec.split('.')
        return int(hours), int(mins), int(secs)
        

class CycleDataViewer(QTreeWidget):
    
    def __init__(self, data, widthSpace=5):
        super().__init__()
        
        self.data = data
        
        self.widthSpace = widthSpace
        
        self.headerLabels = ['Date', 'Time', 'Distance (km)', 'Avg. speed\n(km/hr)', 
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
        
    @property 
    def topLevelItems(self):
        """ List of top level QTreeWidgetItems. """
        items = [self.topLevelItem(i) for i in range(self.topLevelItemCount())]
        return items
        
    def makeTree(self):
        """ Populate tree with data from DataFrame. """
        
        dfs = self.data.splitMonths()
        
        for df in reversed(dfs):
            
            # root item of tree: summary of month, with total time, distance
            # and calories (in bold)
            data = CycleData(df) # make CycleData object for the month, so we can access `timeHours`
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
                    col = re.sub(r"\s", " ", col)
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
        """ Convert `totalHours` float to HH:MM.ss string. """
        hours, mins = divmod(totalHours, 1)
        mins *= 60
        mins, secs = divmod(mins, 1)
        secs *= 60
        s = f"{hours:02.0f}:{mins:02.0f}.{secs:02.0f}"
        return s
