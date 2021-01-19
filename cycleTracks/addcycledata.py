#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 19 19:29:46 2021

@author: keziah
"""

from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QWidget, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QHeaderView)
from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtGui import QBrush, QColor

from datetime import datetime
import calendar

class AddCycleData(QWidget):
    
    newData = Signal(list)
    
    invalid = Signal(int, int)
    
    def __init__(self, widthSpace=5):
        super().__init__()
        
        self.widthSpace = widthSpace
        
        self.headerLabels = ['Date', 'Time', 'Distance (km)', 'Calories', 'Gear']
        validateMethods = [self._validateDate, self._validateTime, self._validateFloat, 
                           self._validateFloat, self._validateInt]
        self.validateMethods = dict(zip(self.headerLabels, validateMethods))
        
        self.table = QTableWidget(0, len(self.headerLabels))
        self.table.setHorizontalHeaderLabels(self.headerLabels)
        # self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setVisible(False)
        self._makeEmptyRow()
        self.defaultBrush = self.table.item(0,0).background()
        self.invalidBrush = QBrush(QColor("#910404"))
        self.table.verticalHeader().resizeSections(QHeaderView.ResizeToContents)
        
        self.validateTimer = QTimer()
        self.validateTimer.setInterval(100)
        self.validateTimer.setSingleShot(True)
        self.validateTimer.timeout.connect(self._validate)
        self.table.cellChanged.connect(self.validateTimer.start)
        
        self.invalid.connect(self._invalid)
        
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
        
        
    @Slot(int, int)
    def _invalid(self, row, col):
        self.table.item(row, col).setBackground(self.invalidBrush)
        self.okButton.setEnabled(False)
        
    @Slot()
    def _validate(self):
        allValid = True
        for row in range(self.table.rowCount()):
            for col, name in enumerate(self.headerLabels):
                item = self.table.item(row, col)
                value = item.text()
                mthd = self.validateMethods[name]
                valid = mthd(value)
                if not valid:
                    self.invalid.emit(row, col)
                    allValid = False
                elif valid and self.table.item(row, col).background() == self.invalidBrush:
                    self.table.item(row, col).setBackground(self.defaultBrush) 
        if allValid:
            self.okButton.setEnabled(True)
                
    @staticmethod
    def _validateInt(value):
        return value.isdigit()
    
    @staticmethod
    def _validateFloat(value):
        try:
            float(value)
            return True
        except ValueError:
            return False
        
    @staticmethod
    def _validateDate(value):
        return True
    
    @staticmethod
    def _validateTime(value):
        return True
        
        
    @Slot()
    def _addData(self):
        # get data from table, as list of dicts
        # emit `newData`
        # clear table

        values = []

        for row in range(self.table.rowCount()):
            dct = {}
            for col, name in enumerate(self.headerLabels):
                item = self.table.item(row, col)
                dct[name] = item.text()
            values.append(dct)
                
        if values:
            self.newData.emit(values)
                