#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QTreeWidget showing data from cycling DataFrame.
"""

from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QHeaderView
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtCore import pyqtSlot as Slot
import pandas as pd
import calendar
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
    
    def __init__(self, df, widthSpace=5):
        super().__init__()
        
        self.df = df
        
        self.widthSpace = widthSpace
        
        self.headerLabels = ['Date', 'Time', 'Distance (km)', 'Calories']
        self.setHeaderLabels(self.headerLabels)
        self.header().setStretchLastSection(False)
        
        self.makeTree()
        
        self.sortAscending = False
        self.header().sectionDoubleClicked.connect(self.sortTree)
        
    def sizeHint(self):
        width = self.header().length() + self.widthSpace
        height = super().sizeHint().height()
        return QSize(width, height)
    
    @Slot(int)
    def sortTree(self, idx):
        """ Sort the tree based on column `idx`. """
        self.sortAscending = not self.sortAscending
        order = Qt.AscendingOrder if self.sortAscending else Qt.DescendingOrder
        for rootItem in self.topLevelItems:
            rootItem.sortColumn = idx
        self.sortItems(idx, order)
        
    @property 
    def topLevelItems(self):
        """ List of top level QTreeWidgetItems. """
        items = [self.topLevelItem(i) for i in range(self.topLevelItemCount())]
        return items
        
    @staticmethod
    def splitMonths(df):
        """ Split `df` into list of DataFrames, split by month. """
        grouped = df.groupby(pd.Grouper(key='Date', freq='M'))
        return [group for _,group in grouped]
    
    def makeTree(self):
        """ Populate tree with data from DataFrame. """
        
        dfs = self.splitMonths(self.df)
        
        for df in reversed(dfs):
            
            # root item of tree: summary of month, with total time, distance
            # and calories (in bold)
            data = CycleData(df) # make CycleData object for the month, so we can access `timeHours`
            date = df['Date'].iloc[0]
            rootText = [f"{calendar.month_name[date.month]} {date.year}"]
            rootText.append(self._getHMS(sum(data.timeHours)))
            rootText.append(f"{sum(data.distance):.2f}")
            rootText.append(f"{sum(data.calories):.2f}")
            
            rootItem = CycleTreeWidgetItem(self)
            for idx, text in enumerate(rootText):
                rootItem.setText(idx, text)
                rootItem.setTextAlignment(idx, Qt.AlignCenter)
                font = rootItem.font(idx)
                font.setBold(True)
                rootItem.setFont(idx, font)
                
            # make rows of data for tree
            for _, row in df.iterrows():
                item = QTreeWidgetItem(rootItem)
                for idx, col in enumerate(self.headerLabels):
                    data = row[col]
                    if col == 'Date':
                        data = data.strftime("%d %b %Y")
                    item.setText(idx, str(data))
                    item.setTextAlignment(idx, Qt.AlignCenter)
                    
        self.header().resizeSections(QHeaderView.ResizeToContents)
        
        
    def _getHMS(self, totalHours):
        """ Convert `totalHours` float to HH:MM.ss string. """
        
        hours, mins = divmod(totalHours, 1)
        mins *= 60
        mins, secs = divmod(mins, 1)
        secs *= 60
        s = f"{hours:02.0f}:{mins:02.0f}.{secs:02.0f}"
        
        return s
