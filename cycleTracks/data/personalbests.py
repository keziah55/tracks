"""
QTableWidget showing the top sessions.
"""
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSlot as Slot
from PyQt5.QtGui import QFontMetrics
import re

class PersonalBests(QTableWidget):
    """ QTableWidget showing the top sessions.

        By default, it will show the five fastest sessopns. Clicking on another header
        (except 'Date') will show the top five sessions for that column.
    
        Parameters
        ----------
        parent : QWidget
            Main window/widget with :class:`CycleData` object
        rows : int
            Number of rows to display, i.e. the number of top sessions to show.
            Default is 5.
    """
    
    def __init__(self, parent, rows=5):
        self.headerLabels = ['Date', 'Time', 'Distance (km)', 'Avg. speed\n(km/h)', 
                             'Calories', 'Gear']
        columns = len(self.headerLabels)
        super().__init__(rows, columns)
        self.parent = parent
        
        self.selectableColumns = ['Time', 'Distance (km)', 'Avg. speed (km/h)', 
                                  'Calories', 'Gear']
        
        self.setHorizontalHeaderLabels(self.headerLabels)
        
        # make header tall enough for two rows of text (avg speed has line break)
        font = self.header.font()
        metrics = QFontMetrics(font)
        height = metrics.height()
        self.header.setMinimumHeight(height*2)
        
        self.header.sectionClicked.connect(self.selectColumn)
        self.selectColumn(self.headerLabels.index('Avg. speed\n(km/h)'))
        
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        
    @property
    def data(self):
        return self.parent.data
    
    @property
    def header(self):
        return self.horizontalHeader()
    
    def makeTable(self, n=5, key="Avg. speed (km/h)", order='descending'):
        if order == 'descending':
            n *= -1
        if key == 'Time':
            series = self.data.timeHours
        else:
            series = self.data[key]
        indices = series.argsort()[n:][::-1]
        for rowNum, idx in enumerate(indices):
            for colNum, key in enumerate(self.headerLabels):
                key = re.sub(r"\s", " ", key) # remove \n from avg speed
                value = self.data.formatted(key)[idx]
                item = QTableWidgetItem()
                item.setText(value)
                item.setTextAlignment(Qt.AlignCenter)
                self.setItem(rowNum, colNum, item)
                
        self.header.resizeSections(QHeaderView.ResizeToContents)


    @Slot(int)
    def selectColumn(self, idx):
        col = self.headerLabels[idx]
        col = re.sub(r"\s", " ", col) # remove \n from avg speed
        if col in self.selectableColumns:
            self.clearContents()
            self.makeTable(key=col)
            
            for i in range(self.header.count()):
                font = self.horizontalHeaderItem(i).font()
                if i == idx:
                    font.setItalic(True)
                else:
                    font.setItalic(False)
                self.horizontalHeaderItem(i).setFont(font)