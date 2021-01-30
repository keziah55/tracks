"""
QWidget containing a QTableWidget, where users can add new cycling data. 

User input will be validated live; if data is invalid, the 'Ok' button cannot
be clicked.
"""

from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QWidget, QPushButton, 
                             QVBoxLayout, QHBoxLayout)
from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtGui import QBrush, QColor

from cycleTracks.util import (isDate, isFloat, isInt, isDuration, parseDate, 
                              parseDuration, dayMonthYearToFloat)

from datetime import datetime
import calendar
from functools import partial

class TableWidgetDateItem(QTableWidgetItem):
    """ QTableWidgetItem, which will sort dates. """
    def __lt__(self, other):
        item0 = self.text()
        item1 = other.text()
        value0 = dayMonthYearToFloat(item0)
        value1 = dayMonthYearToFloat(item1)
        return value0 < value1

class AddCycleData(QWidget):
    """ QWidget containing a QTableWidget, where users can add new data. 
    
        User input is validated live; it is not possible to submit invalid data.
    """
    
    newData = Signal(dict)
    """ **signal** newData(dict `data`)
    
        Emitted with a dict to be appended to the DataFrame.
    """
    
    invalid = Signal(int, int)
    """ **signal** invalid(int `row`, int `col`)
    
        Emitted if the data in cell `row`,`col` is invalid.
    """
    
    def __init__(self, widthSpace=10):
        super().__init__()
        
        self.widthSpace = widthSpace
        
        self.headerLabels = ['Date', 'Time', 'Distance (km)', 'Calories', 'Gear']
        
        # dict of methods to validate and cast types for input data in each column
        validateMethods = [isDate, isDuration, isFloat, 
                           isFloat, isInt]
        parseDatePd = partial(parseDate, pd_timestamp=True)
        castMethods = [parseDatePd, parseDuration, float, float, int]
        self.mthds = {name:{'validate':validateMethods[i], 'cast':castMethods[i]}
                      for i, name in enumerate(self.headerLabels)}
        
        self.table = QTableWidget(0, len(self.headerLabels))
        self.table.setHorizontalHeaderLabels(self.headerLabels)
        # self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setVisible(False)
        self._makeEmptyRow()
        self.defaultBrush = self.table.item(0,0).background()
        self.invalidBrush = QBrush(QColor("#910404"))
        # self.table.verticalHeader().resizeSections(QHeaderView.ResizeToContents)
        
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
        self.okButton.setShortcut(Qt.Key_Enter)
        
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
        # can't believe this is necessary...
        width = self.table.verticalHeader().length() + self.widthSpace
        for i in range(self.table.columnCount()):
            width += self.table.columnWidth(i)
        height = self.table.sizeHint().height()
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
        
        item = TableWidgetDateItem(date)
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
                mthd = self.mthds[name]['validate']
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
        
        self.table.sortItems(0, Qt.AscendingOrder)

        for row in range(self.table.rowCount()):
            for col, name in enumerate(self.headerLabels):
                item = self.table.item(row, col)
                value = item.text()
                mthd = self.mthds[name]['cast']
                value = mthd(value)
                values[name].append(value)
                
        self.newData.emit(values)
            
        for row in reversed(range(self.table.rowCount())):
            self.table.removeRow(row)
        self._makeEmptyRow()
    