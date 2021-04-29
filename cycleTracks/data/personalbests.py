"""
QTableWidget showing the top sessions.
"""

from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView,
                             QDialog, QDialogButtonBox, QLabel, QVBoxLayout,
                             QWidget, QGroupBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot as Slot
from PyQt5.QtGui import QFontMetrics
from . import CycleData
import re
import calendar


class PersonalBests(QWidget):
    
    def __init__(self, parent):
        super().__init__()
        
        self.labelGroup = QGroupBox("Best month")
        self.label = PBMonthLabel(parent)
        groupLayout = QVBoxLayout()
        groupLayout.addWidget(self.label)
        self.labelGroup.setLayout(groupLayout)
        
        self.tableGroup = QGroupBox("Top five sessions")
        self.table = PBTable(parent)
        groupLayout = QVBoxLayout()
        groupLayout.addWidget(self.table)
        self.tableGroup.setLayout(groupLayout)
        
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.labelGroup)
        self.layout.addWidget(self.tableGroup)
        self.setLayout(self.layout)
        
        
    @Slot()
    def newData(self):
        self.table.newData()
        self.label.newData()
    

class PBMonthLabel(QLabel):
    
    def __init__(self, parent, column='Distance (km)'):
        super().__init__()
        self.parent = parent
        self.column = column
        self.newData()
        
    @property
    def data(self):
        return self.parent.data
    
    @Slot()
    def newData(self):
        pass
        # dfs = self.data.splitMonths()
        # totals = []
        # for monthYear, df in dfs:
        #     if df.empty:
        #         continue
        #     monthData = CycleData(df)
        #     date = df['Date'].iloc[0]
        #     monthName = f"{calendar.month_name[date.month]} {date.year}"
        #     totalDist = sum(monthData.distance)
        #     totalDist = self.data.fmtFuncs['Distance (km)'](totalDist)
            
        #     totals.append((monthName, totalDist))
        # totals.sort(key=lambda tup: float(tup[1]), reverse=True)
        # best = totals[0]
        # self.setText(f"{best[0]}: {best[1]}km")
    
    

class PBTable(QTableWidget):
    """ QTableWidget showing the top sessions.

        By default, it will show the five fastest sessopns. Clicking on another header
        (except 'Date' or 'Gear') will show the top five sessions for that column.
    
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
        
        self.newPBdialog = NewPBDialog()
        
        self.selectableColumns = ['Time', 'Distance (km)', 'Avg. speed (km/h)', 'Calories']
        
        self.setHorizontalHeaderLabels(self.headerLabels)
        
        # make header tall enough for two rows of text (avg speed has line break)
        font = self.header.font()
        metrics = QFontMetrics(font)
        height = metrics.height()
        self.header.setMinimumHeight(height*2)
        
        self.header.sectionClicked.connect(self.selectColumn)
        self.selectColumn(self.headerLabels.index('Avg. speed\n(km/h)'))
        
    @property
    def data(self):
        return self.parent.data
    
    @property
    def header(self):
        return self.horizontalHeader()
    
    def _getBestSessions(self, n=5, key="Avg. speed (km/h)", order='descending'):
        if order == 'descending':
            n *= -1
        if key == 'Time':
            series = self.data.timeHours
        else:
            series = self.data[key]
        pb = []
        indices = series.argsort()[n:][::-1]
        for idx in indices:
            row = {}
            for key in self.headerLabels:
                key = re.sub(r"\s", " ", key) # remove \n from avg speed
                value = self.data.formatted(key)[idx]
                row[key] = value
            pb.append(row)
        return pb
                
        
    def makeTable(self, n=5, key="Avg. speed (km/h)", order='descending'):
        pb = self._getBestSessions(n=n, key=key, order=order)
        
        self.selectKey = key
        self.dates = [row['Date'] for row in pb]
        
        for rowNum, row in enumerate(pb):
            for colNum, key in enumerate(self.headerLabels):
                key = re.sub(r"\s", " ", key) # remove \n from avg speed
                value = row[key]
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
                
    @Slot()
    def newData(self):
        pb = self._getBestSessions(key=self.selectKey)
        newDates = [row['Date'] for row in pb]
        if newDates != self.dates:
            i = 0
            while newDates[i] == self.dates[i]:
                i += 1
            self.newPBdialog.setMessage(self.selectKey, i, pb[i][self.selectKey])
            self.newPBdialog.exec_()
            self.makeTable(key=self.selectKey)
            
    
class NewPBDialog(QDialog):
    """ Dialog showing a message congratulating the user on a new PB.
    
        The dialog has an 'Ok' button, but will also timeout after a few milliseconds.
        
        Parameters
        ----------
        timeout : int
            Number of milliseconds for the dialog to be shown. Default is 3000.
    """
    
    def __init__(self, timeout=3000):
        super().__init__()
        
        self.label = QLabel()
        font = self.label.font()
        font.setPointSize(14)
        self.label.setFont(font)
        
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        self.okButton = self.buttonBox.button(QDialogButtonBox.Ok)
        self.okButton.clicked.connect(self.accept)
        
        self.timer = QTimer()
        self.timer.setInterval(timeout)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.accept)
        
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
        self.setWindowTitle("New personal best")
        
    def setMessage(self, key, idx, value):
        key = re.sub(r"\s", " ", key) # remove \n from avg speed
        # check for units
        m = re.search(r"\((?P<unit>.+)\)", key)
        if m is not None:
            unit = m.group('unit')
            key = re.sub(r"\(.+\)", "", key) # remove units in brackets
        else:
            unit = ""
        key = key.strip()
        key = key.lower()
        
        colour = "#f7f13b"
        
        msg = f"<span>New #{idx+1} {key} - </span>"
        msg += f"<span style='color: {colour}'>{value}{unit}</span>"
        msg += "<span>! Congratulations!</span>"
        
        self.label.setText(msg)
        self.timer.start()
        