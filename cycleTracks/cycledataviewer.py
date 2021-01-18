#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QTreeWidget showing data from cycling DataFrame.
"""

from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QHeaderView
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFont
import pandas as pd
import calendar
from cycledata import CycleData


class CycleDataViewer(QTreeWidget):
    
    def __init__(self, df, widthSpace=5):
        super().__init__()
        
        self.df = df
        
        self.widthSpace = widthSpace
        
        self.headerLabels = ['Date', 'Time', 'Distance (km)', 'Calories']
        self.setHeaderLabels(self.headerLabels)
        self.header().setStretchLastSection(False)
        
        self.makeTree()
        
    def sizeHint(self):
        width = self.header().length() + self.widthSpace
        height = super().sizeHint().height()
        return QSize(width, height)
        
        
    def splitMonths(self):
        grouped = self.df.groupby(pd.Grouper(key='Date', freq='M'))
        return [group for _,group in grouped]
    
        
    def makeTree(self):
        
        dfs = self.splitMonths()
        
        for df in reversed(dfs):
            data = CycleData(df)
            
            date = df['Date'].iloc[0]
            rootText = [f"{calendar.month_name[date.month]} {date.year}"]
            rootText.append(self._getHMS(sum(data.timeHours)))
            rootText.append(f"{sum(data.distance):.2f}")
            rootText.append(f"{sum(data.calories):.2f}")
            
            rootItem = QTreeWidgetItem(self)
            for idx, text in enumerate(rootText):
                rootItem.setText(idx, text)
                rootItem.setTextAlignment(idx, Qt.AlignCenter)
                font = rootItem.font(idx)
                font.setBold(True)
                rootItem.setFont(idx, font)
                
        
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
        
        hours, mins = divmod(totalHours, 1)
        mins *= 60
        mins, secs = divmod(mins, 1)
        secs *= 60
        s = f"{hours:02.0f}:{mins:02.0f}.{secs:02.0f}"
        
        return s
