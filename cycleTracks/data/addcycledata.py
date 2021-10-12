"""
QWidget containing a QTableWidget, where users can add new cycling data. 

User input will be validated live; if data is invalid, the 'Ok' button cannot
be clicked.
"""

from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QWidget, QPushButton, 
                             QVBoxLayout, QHBoxLayout)
from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot

from .adddatatablemixin import AddDataTableMixin
from cycleTracks.util import dayMonthYearToFloat, parseDate

from datetime import datetime
import calendar

class TableWidgetDateItem(QTableWidgetItem):
    """ QTableWidgetItem, which will sort dates. """
    def __lt__(self, other):
        item0 = self.text()
        item1 = other.text()
        item0, item1 = [parseDate(item).strftime("%d %b %Y") for item in [item0, item1]]
        value0 = dayMonthYearToFloat(item0)
        value1 = dayMonthYearToFloat(item1)
        return value0 < value1

class AddCycleData(AddDataTableMixin, QWidget):
    """ QWidget containing a QTableWidget, where users can add new data. 
    
        User input is validated live; it is not possible to submit invalid data.
    """
    
    newData = Signal(dict)
    """ **signal** newData(dict `data`)
    
        Emitted with a dict to be appended to the DataFrame.
    """
    
    rowRemoved = Signal()
    """ **signal** rowRemoved()
    
        Emitted when the current row is removed from the table.
    """
    
    def __init__(self, widthSpace=10):
        super().__init__()
        
        self.widthSpace = widthSpace
        
        # self.table = QTableWidget(0, len(self.headerLabels))
        # self.table.setHorizontalHeaderLabels(self.headerLabels)
        # self.table.verticalHeader().setVisible(False)
        
        self._clicked = []
        self._makeEmptyRow()
        
        self.table.currentCellChanged.connect(self._cellClicked)
        
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
        
        msg = "Add new session(s) data to viewer and plot."
        self.setToolTip(msg)
        
        
    def sizeHint(self):
        # can't believe this is necessary...
        width = self.table.verticalHeader().length() + self.widthSpace
        for i in range(self.table.columnCount()):
            width += self.table.columnWidth(i)
        height = self.table.sizeHint().height()
        return QSize(width, height)
    
    @Slot(int, int)
    def _cellClicked(self, row, col):
        if (row, col) not in self._clicked:
            self._clicked.append((row, col))
        
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
        self._clicked = [item for item in self._clicked if item[0] != row]
        self._cellClicked(row, 0)
        
    @Slot()
    def _removeSelectedRow(self):
        """ Remove the currently selected row from the table. """
        row = self.table.currentRow()
        self._clicked = [item for item in self._clicked if item[0] != row]
        self.table.removeRow(row)
        self.rowRemoved.emit()
        
    @Slot()
    def _addData(self):
        """ Take all data from the table and emit it as a list of dicts with 
            the `newData` signal, then clear the table.
        """
        self.table.focusNextChild()
        valid = self._validate()
        if not valid:
            return None
        
        values = self._getValues()
        self.newData.emit(values)
            
        for row in reversed(range(self.table.rowCount())):
            self.table.removeRow(row)
        self._clicked = []
        self._makeEmptyRow()
