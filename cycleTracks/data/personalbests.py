"""

"""
from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QWidget, QPushButton, 
                             QVBoxLayout, QHBoxLayout)
from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot
from PyQt5.QtGui import QBrush, QColor

class PersonalBests(QTableWidget):
    
    def __init__(self, parent, rows=5):
        self.headerLabels = ['Date', 'Time', 'Distance (km)', 'Avg. speed\n(km/h)', 
                             'Calories', 'Gear']
        columns = len(self.headerLabels)
        super().__init__(rows, columns)
        self.parent = parent
        
        self.setHorizontalHeaderLabels(self.headerLabels)
        # self.header().setStretchLastSection(False)
        self.makeTable(n=rows)
        
    @property
    def data(self):
        return self.parent.data
    
    def makeTable(self, n=5):
        indices = self.data.avgSpeed.argsort()[-n:][::-1]
        for rowNum, idx in enumerate(indices):
            for colNum, key in enumerate(self.data.propertyNames.keys()):
                item = QTableWidgetItem()
                item.setText(str(self.data[key][idx]))
                item.setTextAlignment(Qt.AlignCenter)
                self.setItem(rowNum, colNum, item)
                