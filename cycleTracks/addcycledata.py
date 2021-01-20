#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QWidget containing a QTableWidget, where users can add new cycling data. 

User input will be validated live; if data is invalid, the 'Ok' button cannot
be clicked.
"""

from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QWidget, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QHeaderView)
from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtGui import QBrush, QColor

from validate import (validateDate, validateFloat, validateInt, validateTime,
                      parseDate, parseTime)

from datetime import datetime
import calendar

class AddCycleData(QWidget):
    
    newData = Signal(dict)
    """ **signal** newData(dict `data`)
    
        Emitted with a dict to be appended to the DataFrame.
    """
    
    invalid = Signal(int, int)
    """ **signal** invalid(int `row`, int `col`)
    
        Emitted if the data in cell `row`,`col` is invalid.
    """
    
    def __init__(self, widthSpace=5):
        super().__init__()
        
        self.widthSpace = widthSpace
        
        self.headerLabels = ['Date', 'Time', 'Distance (km)', 'Calories', 'Gear']
        validateMethods = [validateDate, validateTime, validateFloat, 
                           validateFloat, validateInt]
        self.validateMethods = dict(zip(self.headerLabels, validateMethods))
        
        # TODO combine these into one dict
        # TODO make partial of parseDate with pd_timestamp=True
        castMethods = [parseDate, parseTime, float, float, int]
        self.castMethods = dict(zip(self.headerLabels, castMethods))
        
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
        """ Add a new row to the end of the table, with today's date in the 
            'Date' field and the rest blank. 
        """
        
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
        """ Remove the currently selected row from the table. """
        row = self.table.currentRow()
        self.table.removeRow(row)
        
    @Slot(int, int)
    def _invalid(self, row, col):
        """ Set the background of cell `row`,`col` to the `invalidBrush` and 
            disable the 'Ok' button.
        """
        self.table.item(row, col).setBackground(self.invalidBrush)
        self.okButton.setEnabled(False)
        
    @Slot()
    def _validate(self):
        """ Validate all data in the table. """
        # it would be more efficient to only validate a single cell, after its
        # text has been changed, but this table is unlikely to ever be more 
        # than a few rows long, so this isn't too inefficient
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
                
    @Slot()
    def _addData(self):
        """ Take all data from the table and emit it as a list of dicts with 
            the `newData` signal, then clear the table.
        """
        values = {name:[] for name in self.headerLabels}

        for row in range(self.table.rowCount()):
            for col, name in enumerate(self.headerLabels):
                item = self.table.item(row, col)
                value = item.text()
                mthd = self.castMethods[name]
                value = mthd(value)
                # if name == 'Date':
                #     value = parseDate(value, pd_timestamp=True)
                # elif name == 'Time':
                #     value = parseTime(value)
                values[name].append(value)
                
        self.newData.emit(values)
            
        self.table.clearContents()