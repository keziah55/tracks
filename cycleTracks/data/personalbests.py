"""
QTableWidget showing the top sessions.
"""

from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView, QLabel, 
                             QDialogButtonBox, QVBoxLayout, QWidget, QAbstractItemView)
from PyQt5.QtCore import Qt, pyqtSlot as Slot, pyqtSignal as Signal
from PyQt5.QtGui import QFontMetrics
from . import CycleData
from cycleTracks.util import dayMonthYearToFloat, hourMinSecToFloat
from customQObjects.widgets import TimerDialog, GroupWidget
import re
import numpy as np


class PersonalBests(QWidget):
    
    itemSelected = Signal(object)
    
    def __init__(self, parent):
        super().__init__()
        
        self.newPBdialog = NewPBDialog()
        
        self.dataAnalysis = parent.dataAnalysis
        
        self.labelGroup = GroupWidget("Best month")
        self.label = PBMonthLabel(parent)
        self.labelGroup.addWidget(self.label)
        
        self.tableGroup = GroupWidget("Top five sessions")
        self.table = PBTable(parent)
        self.tableGroup.addWidget(self.table)
        self.table.itemSelected.connect(self.itemSelected)
        
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.labelGroup)
        self.layout.addWidget(self.tableGroup)
        self.setLayout(self.layout)
        
    @Slot()
    def newData(self):
        bestSession = self.table.newData()
        bestMonth = self.label.newData()
        
        if bestSession is None and bestMonth is None:
            return None
        
        if bestSession is not None and bestMonth is not None:
            msg = bestSession + "<br>and<br>" + bestMonth
        else:
            msg = [msg for msg in (bestSession, bestMonth) if msg is not None][0]
        msg += "<br><span>Congratulations!</span>"
        
        msg = f"<center>{msg}</center>"
        
        self.newPBdialog.setMessage(msg)
        self.newPBdialog.exec_()
        
        if bestSession is not None:
            self.table.setTable()
        if bestMonth is not None:
            self.label.setText()

class PBMonthLabel(QLabel):
    
    def __init__(self, parent, column='Distance (km)'):
        super().__init__()
        self.parent = parent
        self.column = column
        self.monthYear = self.time = self.distance = self.calories = ""
        self.newData()
        self.setText()
        
    @property
    def data(self):
        return self.parent.data
    
    @Slot()
    def newData(self):
        dfs = self.data.splitMonths()
        totals = []
        for monthYear, df in dfs:
            monthData = CycleData(df)
            summaries = [monthData.summaryString('Time (hours)'), 
                         monthData.summaryString('Distance (km)'),
                         monthData.summaryString('Avg. speed (km/h)', func=max),
                         monthData.summaryString('Calories'),
                         monthData.summaryString('Gear', func=lambda v: np.around(np.mean(v)))]
            totals.append((monthYear, summaries))
        totals.sort(key=lambda tup: float(tup[1][1]), reverse=True)
        monthYear, summaries = totals[0]
        self.time, self.distance, _, self.calories, *vals = summaries
        
        if monthYear != self.monthYear:
            self.monthYear = monthYear
            msg = self.makeMessage(monthYear)
            return msg
        else:
            return None
        
    def makeMessage(self, monthYear):
        colour = "#f7f13b"
        msg = "<span>New best month - </span>"
        msg += f"<span style='color: {colour}'>{monthYear}</span>!"
        return msg
        
    def _makeText(self):
        s = f"<b>{self.monthYear}</b>: <b>{self.distance}</b> km, <b>{self.time}</b> hours, <b>{self.calories}</b> calories"
        return s

    def setText(self):
        text = self._makeText()
        super().setText(text)
        

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
    
    itemSelected = Signal(object)
    
    def __init__(self, parent, rows=5):
        self.headerLabels = ['Date', 'Time', 'Distance (km)', 'Avg. speed\n(km/h)', 
                             'Calories', 'Gear']
        columns = len(self.headerLabels)
        super().__init__(rows, columns)
        self.parent = parent
        
        self.newPBdialog = NewPBDialog()
        
        # dict of columns that can be selected and the functions used to compare values
        self.selectableColumns = {'Time':hourMinSecToFloat, 'Distance (km)':float, 
                                  'Avg. speed (km/h)':float, 'Calories':float}
        
        self.setHorizontalHeaderLabels(self.headerLabels)
        
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        self.selectKey = "Avg. speed (km/h)"
        
        # make header tall enough for two rows of text (avg speed has line break)
        font = self.header.font()
        metrics = QFontMetrics(font)
        height = metrics.height()
        self.header.setMinimumHeight(height*2)
        
        self.currentCellChanged.connect(self._cellChanged)
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
        # Get indices of series, when series is sorted in reverse order.
        # Get indices, and make `pb` list, for whole series, not just top `n`,
        # so that, if there are multiple tied values that would extend the table
        # over `n` rows, only the most recent sessions will be shown here.
        # (So that the table is always `n` rows long.)
        indices = series.argsort()[::-1] 
        for idx in indices:
            row = {}
            for k in self.headerLabels:
                k = re.sub(r"\s", " ", k) # remove \n from avg speed
                value = self.data.formatted(k)[idx]
                row[k] = value
            row['datetime'] = self.data['Date'][idx]
            pb.append(row)
            
        # sort by date first, then by speed, so if values are tied, most recent will be first 
        # (this also means that the number for the message is correct automatically)
        pb.sort(key=lambda dct: dayMonthYearToFloat(dct['Date']), reverse=True)
        func = self.selectableColumns[key]
        reverse = True if order == "descending" else False        
        pb.sort(key=lambda dct: func(dct[key]), reverse=reverse)
        
        # return only `n` values
        pb = pb[:n]
            
        return pb
    
       
    def setTable(self, n=5, key="Avg. speed (km/h)", order='descending'):
        
        self.items = self._getBestSessions(n=n, key=key, order=order)
        
        self.selectKey = key
        self.dates = [row['Date'] for row in self.items]
        
        rowNums = ['1']
        for idx in range(1, len(self.items)):
            if self.items[idx]['Avg. speed (km/h)'] == self.items[idx-1]['Avg. speed (km/h)']:
                if rowNums[-1][-1] != "=":
                    # add an equals sign (unless there's one there already)
                    rowNums[-1] += "="
                rowNums.append(rowNums[-1])
            else:
                rowNums.append(str(idx+1))
        
        for rowNum, row in enumerate(self.items):
            for colNum, key in enumerate(self.headerLabels):
                key = re.sub(r"\s", " ", key) # remove \n from avg speed
                value = row[key]
                item = QTableWidgetItem()
                item.setText(value)
                item.setTextAlignment(Qt.AlignCenter)
                self.setItem(rowNum, colNum, item)
                
        self.setVerticalHeaderLabels(rowNums)
                
        self.header.resizeSections(QHeaderView.ResizeToContents)

    @Slot(int)
    def selectColumn(self, idx):
        col = self.headerLabels[idx]
        col = re.sub(r"\s", " ", col) # remove \n from avg speed
        if col in self.selectableColumns:
            self.clearContents()
            self.setTable(key=col)
            
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
        dates = [row['Date'] for row in self.items]
        if newDates != dates:
            i = 0
            while newDates[i] == dates[i]:
                i += 1
            msg = self.makeMessage(self.selectKey, i, pb[i][self.selectKey])
            return msg
        else:
            None
            
    @Slot(int, int, int, int)
    def _cellChanged(self, row, column, previousRow, previousColumn):
        dct = self.items[row]
        self.itemSelected.emit(dct['datetime'])

    def makeMessage(self, key, idx, value):
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
        msg += f"<span style='color: {colour}'>{value}{unit}</span>!"
        
        return msg


class NewPBDialog(TimerDialog):
    """ Dialog showing a message congratulating the user on a new PB.
    
        The dialog has an 'Ok' button, but will also timeout after a few milliseconds.
        
        Parameters
        ----------
        timeout : int
            Number of milliseconds for the dialog to be shown. Default is 3000.
    """
    def __init__(self, timeout=3000):
        super().__init__(timeout=timeout)
        
        self.label = QLabel()
        font = self.label.font()
        font.setPointSize(14)
        self.label.setFont(font)
        
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        self.okButton = self.buttonBox.button(QDialogButtonBox.Ok)
        self.okButton.clicked.connect(self.accept)
        
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
        self.setWindowTitle("New personal best")
        
    def setMessage(self, text):
        self.label.setText(text)
        