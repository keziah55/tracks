#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QTreeWidget showing data from cycling DataFrame.
"""

from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QHeaderView
from PyQt5.QtCore import QSize, Qt
import pandas as pd
import calendar

class CycleDataViewer(QTreeWidget):
    
    def __init__(self, df):
        super().__init__()
        
        self.df = df
        
        self.headerLabels = ['Date', 'Time', 'Distance (km)', 'Calories']
        self.setHeaderLabels(self.headerLabels)
        self.header().setStretchLastSection(False)
        
        self.makeTree()
        
    def sizeHint(self):
        width = self.header().length() #self.header().width()
        height = super().sizeHint().height()
        # print(f"width: {width}, length: {self.header().length()}")
        return QSize(width, height)
        
        
    def splitMonths(self):
        grouped = self.df.groupby(pd.Grouper(key='Date', freq='M'))
        return [group for _,group in grouped]
    
        
    def makeTree(self):
        
        dfs = self.splitMonths()
        
        for df in reversed(dfs):
            date = df['Date'].iloc[0]
            label = f"{calendar.month_name[date.month]} {date.year}"
            rootItem = QTreeWidgetItem(self)
            rootItem.setText(0, label)
        
            for _, row in df.iterrows():
                item = QTreeWidgetItem(rootItem)
                for idx, col in enumerate(self.headerLabels):
                    data = row[col]
                    if col == 'Date':
                        data = data.strftime("%d %b %Y")
                    item.setText(idx, str(data))
                    item.setTextAlignment(idx, Qt.AlignCenter)
                    
        self.header().resizeSections(QHeaderView.ResizeToContents)
