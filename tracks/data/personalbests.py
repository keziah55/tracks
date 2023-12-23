"""
Single `PersonalBests` object to manage the two widgets that display personal bests.
"""

from qtpy.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView, QLabel, 
                            QDialogButtonBox, QVBoxLayout, QAbstractItemView)
from qtpy.QtCore import Qt, QObject, QSize, Slot, Signal
from tracks.util import dayMonthYearToFloat, hourMinSecToFloat, intToStr
from tracks.data import Data
from customQObjects.widgets import TimerDialog
import re
from datetime import date


class PersonalBests(QObject):
    """ Object to manage the two PB widgets.
    
        The :meth:`newData` method updates the data in each widget and creates
        the dialog box with the correct message, if required.
    """
    
    itemSelected = Signal(object)
    """ itemSelected(Timestamp `ts`)
    
        Emitted when an item in the PB table is selected, either by 
        clicking on it or by navigating with the up or down keys. The datetime
        timestamp of the selected row is passed with this signal.
    """
    
    numSessionsChanged = Signal(int)
    """ numSessionsChanged(int `numSessions`)
    
        Emitted when the number of sessions shown in the PBTable is changed.
    """
    
    monthCriterionChanged = Signal(str)
    """ monthCriterionChanged(str `criterion`)
    
        Emitted when the criterion for calculating the best month is changed.
    """
    
    statusMessage = Signal(str)
    
    def __init__(self, parent, activity, numSessions=5, monthCriterion="distance", sessionsKey="Speed (km/h)"):
        super().__init__()
        self.parent = parent
        self.newPBdialog = NewPBDialog()
        self.bestMonth = PBMonthLabel(parent=self, activity=activity, column=monthCriterion)
        self.bestSessions = PBTable(parent=self, activity=activity, rows=numSessions, key=sessionsKey)
        
    @property
    def data(self):
        return self.parent.data
        
    @Slot(object)
    def newData(self, idx=None):
        self.emitStatusMessage()
        
        bestSession = self.bestSessions.newData()
        bestMonth = self.bestMonth.newData()
        
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
            self.bestSessions.setTable(highlightNew=True)
        if bestMonth is not None:
            self.bestMonth.setText()
            
        self.statusMessage.emit("")
    
    def emitStatusMessage(self):
        self.statusMessage.emit("Checking for new PBs...")
        
    def state(self) -> dict:
        """ Return dict of values to be saved in settings (that aren't set in preferences) """
        state = {
            "sessionsKey": self.bestSessions.selectKey,
            }
        return state

class PBMonthLabel(QLabel):
    
    def __init__(self, parent, activity, column='Distance (km)'):
        super().__init__()
        self.parent = parent
        self._activity = activity
        self.column = column
        self.pbCount = (None, None)
        self.monthYear = self.time = self.distance = self.calories = ""
        self.newData()
        self.setText()
        self.setAlignment(Qt.AlignHCenter)
        
    def sizeHint(self):
        size = super().sizeHint()
        height = int(1.5*size.height())
        return QSize(size.width(), height)
    
    @property
    def data(self):
        return self.parent.data
        
    def setColumn(self, column, pbCount=None, pbMonthRange=None):
        self.column = column
        self.pbCount = (pbCount, pbMonthRange)
        self.newData()
        self.setText()
        col = re.sub(r" +\(.*\)", "", column).lower()
        if self.parent is not None:
            if pbCount is not None:
                t = " - Most PBs - "
                t += f"{pbMonthRange} months" if pbMonthRange is not None else "All time"
            else:
                t = ""
            c = self.data.quickNames[col]
            self.parent.monthCriterionChanged.emit(f"{c}{t}")
        
    @Slot()
    def newData(self):
        if self.pbCount[0] is not None:
            month = self._pbCount()
            if month is None:
                dfs = []
                self.numPBs = 0
            else:
                dfs = [month]
                self.numPBs = len(month[1])
        else:
            dfs = self.data.splitMonths(returnType="Data")
            self.numPBs = None
            
        if len(dfs) == 0:
            return None
        
        totals = [(monthYear, monthData.make_summary()) for monthYear, monthData in dfs]
        
        try:
            totals.sort(key=lambda tup: float(tup[1][self.column]), reverse=True)
        except ValueError:
            totals.sort(key=lambda tup: hourMinSecToFloat(tup[1][self.column]), reverse=True)
        monthYear, summaries = totals[0]
        self.time, self.distance, _, self.calories, *vals = summaries
        
        self.setText()
        
        if monthYear != self.monthYear:
            self.monthYear = monthYear
            msg = self.makeMessage(monthYear)
            return msg
        else:
            return None
        
    def _pbCount(self):
        pbCount, pbMonthRange = self.pbCount
        idx = self.data.getPBs(self.column, pbCount)
        
        if len(idx) == 0:
            return None
        
        pb_df = self.data.df.loc[idx].copy()
        
        if pbMonthRange is not None:
            month = date.today().month
            year = date.today().year
            month = month - pbMonthRange
            if month <= 0:
                month += 12
                year -= 1
            today = f"{date.today().year}{date.today().month:02d}{date.today().day:02d}"
            prev = f"{year}{month:02d}01"
            pb_df = pb_df.query(f'{prev} <= Date <= {today}')
            
        data = Data(pb_df)
        pb_dfs = data.splitMonths(returnType="Data")
        pb_dfs.sort(key=lambda item: len(item[1]), reverse=True)
        return pb_dfs[0]
        
    @classmethod
    def _matchColumn(cls, column, lst):
        if column in lst:
            return lst.index(column)
        else:
            # strip units and make all lower case
            lst = [re.sub(r" +\(.*\)", "", item) for item in lst]
            lst = [item.lower() for item in lst]
            column = column.lower()
            return cls._matchColumn(column, lst)
        
    def makeMessage(self, monthYear):
        colour = "#f7f13b"
        msg = "<span>New best month - </span>"
        msg += f"<span style='color: {colour}'>{monthYear}</span>!"
        return msg
        
    def _makeText(self):
        s = f"<b>{self.monthYear}</b>: <b>{self.distance}</b> km, <b>{self.time}</b> hours, <b>{self.calories}</b> calories"
        if self.numPBs is not None:
            s += f"; {self.numPBs} PBs"
        return s

    def setText(self):
        text = self._makeText()
        super().setText(text)
        
class PBTable(QTableWidget):
    """ QTableWidget showing the top sessions.

        By default, it will show the five fastest sessions. Clicking on another header
        (except 'Date' or 'Gear') will show the top five sessions for that column.
    
        Parameters
        ----------
        parent : QObject
            PersonalBests object that manages this object.
        actvity : Activity
            Activity that is represented here
        rows : int
            Number of rows to display, i.e. the number of top sessions to show.
            Default is 5.
    """
    
    def __init__(self, parent, activity, rows=5, key="Speed (km/h)"):
        self.headerLabels = [
            'Date', 'Time', 'Distance (km)', 'Speed (km/h)', 'Calories', 'Gear']
        columns = len(self.headerLabels)
        super().__init__(rows, columns)
        self._activity = activity
        self.parent = parent
        
        self.setHorizontalHeaderLabels(self.headerLabels)
        
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        self.selectKey = key
        
        self.currentCellChanged.connect(self._cellChanged)
        self.header.sectionClicked.connect(self.selectColumn)
        self.selectColumn(self.headerLabels.index(self.selectKey))
        
        self.newIdx = None
        self._setToolTip(rows)
        
    @property
    def data(self):
        return self.parent.data
    
    @property
    def header(self):
        return self.horizontalHeader()
    
    @Slot(int)
    def setNumRows(self, rows):
        if rows == self.rowCount():
            return
        self.setRowCount(rows)
        self.setTable(key=self.selectKey, order=self.order)
        self._setToolTip(rows)
        if self.parent is not None:
            self.parent.numSessionsChanged.emit(rows)
        
    def _setToolTip(self, num):
        s = intToStr(num)
        msg = f"Top {s} sessions, by default, this is determined by fastest average speed.\n"
        msg += "Click on 'Time', 'Distance (km)' or 'Calories' to change the metric.\n"
        msg += "Click on a session to highlight it in the plot."
        self.setToolTip(msg)
    
    def _getBestSessions(self, num=5, key="Speed (km/h)", order='descending'):
        validOrders = ['descending', 'ascending']
        if order not in validOrders:
            msg = f"Order '{order}' is invalid. Order must be one of: {', '.join(validOrders)}"
            raise ValueError(msg)
            
        if key == 'Time':
            series = self.data.timeHours
        else:
            series = self.data[key]
        
        # sort series and get indices
        slc = -1 if order == 'descending' else 1
        indices = series.argsort()[::slc] 
        
        # iterate through `indices` until we have `num` unique values
        pb = []
        numUnique = 0
        
        for idx in indices:
            # get row (as strings for display)
            row = {k: self.data.formatted(k)[idx] for k in self.headerLabels}
            row['datetime'] = self.data['Date'][idx]
            
            if row[key] not in [dct[key] for dct in pb]:
                # increment unique count if value is new
                numUnique += 1
                
            pb.append(row)
                
            if numUnique == num:
                break
        
        # sort by both key and date, so that, if values are tied, most recent will be first
        # use reverse=True for most recent date (and default order=descending)
        # if order is ascending, will need to negate value
        func = self._activity.get_measure(key).cmp_func
        scale = 1 if order == "descending" else -1
        pb.sort(key=lambda dct: (scale*func(dct[key]), dayMonthYearToFloat(dct['Date'])), reverse=True)
            
        # return only `num` values
        return pb[:num]
       
    def setTable(self, key="Speed (km/h)", order='descending', highlightNew=False):
        n = self.rowCount()
        self.items = self._getBestSessions(num=n, key=key, order=order)
        
        self.selectKey = key
        self.order = order
        self.dates = [row['Date'] for row in self.items]
        
        rowNums = ['1']
        for idx in range(1, len(self.items)):
            if self.items[idx]['Speed (km/h)'] == self.items[idx-1]['Speed (km/h)']:
                if rowNums[-1][-1] != "=":
                    # add an equals sign (unless there's one there already)
                    rowNums[-1] += "="
                rowNums.append(rowNums[-1])
            else:
                rowNums.append(str(idx+1))
        
        for rowNum, row in enumerate(self.items):
            for colNum, key in enumerate(self.headerLabels):
                value = row[key]
                item = QTableWidgetItem()
                item.setText(value)
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
                self.setItem(rowNum, colNum, item)
                
        self.setVerticalHeaderLabels(rowNums)
                
        self.header.resizeSections(QHeaderView.ResizeToContents)
        
        if highlightNew and self.newIdx is not None:
            self.setCurrentCell(self.newIdx, 0)

    @Slot(int)
    def selectColumn(self, idx):
        col = self.headerLabels[idx]
        
        m = self._activity.get_measure_from_full_name(col)
        
        if m is None or m.is_metadata:
            return
        
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
        pb = self._getBestSessions(num=self.rowCount(), key=self.selectKey)
        newDates = [row['Date'] for row in pb]
        dates = [row['Date'] for row in self.items]
        if newDates != dates:
            i = 0
            if len(dates) > 0:
                while newDates[i] == dates[i]:
                    i += 1
            self.newIdx = i
            msg = self.makeMessage(self.selectKey, i, pb[i][self.selectKey])
            return msg
        else:
            None
            
    @Slot(int, int, int, int)
    def _cellChanged(self, row, column, previousRow, previousColumn):
        if self.parent is not None and len(self.items) > 0:
            dct = self.items[row]
            self.parent.itemSelected.emit(dct['datetime'])

    def makeMessage(self, key, idx, value):
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
        