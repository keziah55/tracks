#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QTreeWidget showing data from cycling DataFrame.
"""

from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
import pandas as pd
import calendar

class CycleDataViewer(QTreeWidget):
    
    def __init__(self, df):
        super().__init__()
        
        self.df = df
        
        self.header = ['Date', 'Time', 'Distance (km)', 'Calories']
        self.setHeaderLabels(self.header)
        
        self.makeTree()
        
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
        
            for idx, row in df.iterrows():
                item = QTreeWidgetItem(rootItem)
                for n, col in enumerate(self.header):
                    data = row[col]
                    if col == 'Date':
                        data = data.strftime("%d %b %Y")
                    item.setText(n, str(data))
                