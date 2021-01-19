#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 19 19:29:46 2021

@author: keziah
"""

from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QWidget, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QHeaderView)
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtGui import QFontMetrics
from cycledata import CycleData

from datetime import datetime
import calendar

class AddCycleData(QWidget):
    
    newData = Signal(list)
    
    def __init__(self, widthSpace=5):
        super().__init__()
        
        self.widthSpace = widthSpace
        
        self.headerLabels = ['Date', 'Time', 'Distance (km)', 'Calories', 'Gear']
        self.table = QTableWidget(0, len(self.headerLabels))
        self.table.setHorizontalHeaderLabels(self.headerLabels)
        # self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setVisible(False)
        self._makeEmptyRow()
        self.table.verticalHeader().resizeSections(QHeaderView.ResizeToContents)
        
        self.addLineButton = QPushButton("New line")
        self.rmvLineButton = QPushButton("Remove line")
        self.rmvLineButton.setToolTip("Remove currently selected line")
        self.okButton = QPushButton("Ok")
        
        self.addLineButton.clicked.connect(self._makeEmptyRow)
        self.rmvLineButton.clicked.connect(self._removeSelectedRow)
        self.okButton.clicked.connect(self._addData)
        
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.addWidget(self.addLineButton)
        self.buttonLayout.addWidget(self.rmvLineButton)
        self.buttonLayout.addWidget(self.okButton)
        self.buttonLayout.addStretch()
        
        self.layout = QVBoxLayout()
        self.layout.addLayout(self.buttonLayout)
        self.layout.addWidget(self.table)
        self.setLayout(self.layout)
        
        
    def sizeHint(self):
        width = self.table.verticalHeader().length() + self.widthSpace
        height = super().sizeHint().height()
        return QSize(width, height)
        
        
    @Slot()
    def _makeEmptyRow(self):
        
        today = datetime.today()
        month = calendar.month_abbr[today.month]
        date = f"{today.day} {month} {today.year}"
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        item = QTableWidgetItem(date)
        item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 0, item)
        
        for i in range(len(self.headerLabels[1:])):
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, i+1, item)
            
    @Slot()
    def _removeSelectedRow(self):
        row = self.table.currentRow()
        self.table.removeRow(row)
        
    @Slot()
    def _addData(self):
        # get data from table, as list of dicts
        # emit `newData`
        # clear table
        pass
        