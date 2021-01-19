#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 19 19:29:46 2021

@author: keziah
"""

from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QWidget, QPushButton, 
                             QVBoxLayout, QHBoxLayout)
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5.QtGui import QFontMetrics
from cycledata import CycleData

from datetime import datetime
import calendar

class AddCycleData(QWidget):
    
    def __init__(self):
        super().__init__()
        
        self.headerLabels = ['Date', 'Time', 'Distance (km)', 'Calories', 'Gear']
        self.table = QTableWidget(1, len(self.headerLabels))
        self.table.setHorizontalHeaderLabels(self.headerLabels)
        # self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setVisible(False)
        self._makeEmptyRow()
        
        self.addLineButton = QPushButton("New line")
        self.rmvLineButton = QPushButton("Remove line")
        self.rmvLineButton.setToolTip("Remove currently selected line")
        self.okButton = QPushButton("Ok")
        
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.addWidget(self.addLineButton)
        self.buttonLayout.addWidget(self.rmvLineButton)
        self.buttonLayout.addWidget(self.okButton)
        self.buttonLayout.addStretch()
        
        self.layout = QVBoxLayout()
        self.layout.addLayout(self.buttonLayout)
        self.layout.addWidget(self.table)
        self.setLayout(self.layout)
        
        
    def _makeEmptyRow(self):
        
        today = datetime.today()
        month = calendar.month_abbr[today.month]
        date = f"{today.day} {month} {today.year}"
        
        item = QTableWidgetItem(date)
        item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(0, 0, item)
        
        for i in range(len(self.headerLabels[1:])):
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(0, i+1, item)