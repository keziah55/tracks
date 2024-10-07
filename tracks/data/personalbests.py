"""
Single `PersonalBests` object to manage the two widgets that display personal bests.
"""

from qtpy.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QDialogButtonBox,
    QVBoxLayout,
    QAbstractItemView,
)
from qtpy.QtCore import Qt, Slot, Signal
from qtpy.QtGui import QFont
from tracks.util import int_to_str
from customQObjects.widgets import TimerDialog


class PersonalBests(QTableWidget):
    """QTableWidget showing the top sessions.

    By default, it will show the five fastest sessions. Clicking on another header
    (except 'date' or 'Gear') will show the top five sessions for that column.

    Parameters
    ----------
    data : Data
        Data object.
    activity : Activity
        Activity that is represented here
    num_sessions : int
        Number of rows to display, i.e. the number of top sessions to show.
        Default is 5.
    sessions_key : str
        Key by which to get best session.
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

    def __init__(self, data, activity, num_sessions=5, sessions_key="speed"):
        columns = len(activity.header)
        super().__init__(num_sessions, columns)

        self.data = data
        self.newPBdialog = NewPBDialog()

        self._activity = activity

        self.setHorizontalHeaderLabels(self._activity.header)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.select_key = sessions_key
        self.num_best_sessions = num_sessions

        self.currentCellChanged.connect(self._cell_changed)
        self.header.sectionClicked.connect(self._select_column)
        measure = self._activity[self.select_key]
        self._select_column(self._activity.header.index(measure.full_name))

        self.newIdx = None
        self._set_tool_tip(num_sessions)

    @Slot(object)
    def new_data(self, idx=None):
        self._emit_status_message()

        msg = self._new_data()

        if msg is None:
            return None

        msg += "<br><span>Congratulations!</span>"
        msg = f"<center>{msg}</center>"

        self.newPBdialog.set_message(msg)
        self.newPBdialog.exec_()

        if msg is not None:
            self._set_table(highlightNew=True)

        self.statusMessage.emit("")

    def update_values(self, num_sessions=None):
        self._emit_status_message()

        if num_sessions is not None:
            self._set_num_rows(num_sessions)

    def _emit_status_message(self):
        self.statusMessage.emit("Checking for new PBs...")

    def state(self) -> dict:
        """Return dict of values to be saved in settings"""
        state = {
            "sessions_key": self.select_key,
            "num_best_sessions": self.num_best_sessions,
        }
        return state

    @property
    def header(self):
        return self.horizontalHeader()

    @Slot(int)
    def _set_num_rows(self, rows):
        if rows == self.rowCount():
            return
        self.num_best_sessions = rows
        self.setRowCount(rows)
        self._set_table(key=self.select_key, order=self.order)
        self._set_tool_tip(rows)
        self.numSessionsChanged.emit(rows)

    def _set_tool_tip(self, num):
        s = int_to_str(num)
        msg = f"Top {s} sessions, by default, this is determined by fastest average speed.\n"
        msg += "Click on 'Time', 'Distance (km)' or 'Calories' to change the metric.\n"
        msg += "Click on a session to highlight it in the plot."
        self.setToolTip(msg)

    def _get_best_sessions(self, num=5, key="speed", order="descending"):
        validOrders = ["descending", "ascending"]
        if order not in validOrders:
            msg = f"Order '{order}' is invalid. Order must be one of: {', '.join(validOrders)}"
            raise ValueError(msg)

        descending = [order == "descending"]
        cols = [key]
        if key != "date":
            # add 'date' as secondary sort key
            descending.append(True)  # always sort by descending date
            cols.append("date")

        df = self.data.sort(
            cols, descending=descending, return_type="DataFrame", with_index=True, index_name="idx"
        )
        df = df[:num]

        pb = []
        for row in df.rows(named=True):
            for k, measure in self._activity.measures.items():
                row[k] = measure.formatted(row[k])
            pb.append(row)

        return pb

    def _set_table(self, key="speed", order="descending", highlightNew=False):
        """Find top N sessions and display in table."""
        n = self.rowCount()
        self.items = self._get_best_sessions(num=n, key=key, order=order)

        self.select_key = key
        self.order = order
        self.dates = [row["date"] for row in self.items]

        rowNums = ["1"]
        for idx in range(1, len(self.items)):
            if self.items[idx][key] == self.items[idx - 1][key]:
                if rowNums[-1][-1] != "=":
                    # add an equals sign (unless there's one there already)
                    rowNums[-1] += "="
                rowNums.append(rowNums[-1])
            else:
                rowNums.append(str(idx + 1))

        for rowNum, row in enumerate(self.items):
            for colNum, key in enumerate(self._activity.measures):
                value = row[key]
                item = QTableWidgetItem()
                item.setText(value)
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.setItem(rowNum, colNum, item)

        self.setVerticalHeaderLabels(rowNums)

        self.header.resizeSections(QHeaderView.ResizeToContents)

        if highlightNew and self.newIdx is not None:
            self.setCurrentCell(self.newIdx, 0)

    @Slot(int)
    def _select_column(self, idx):
        """When column selected, set table to PBs for that measure."""
        col = self._activity.header[idx]

        m = self._activity.get_measure_from_full_name(col)

        if m is None or m.is_metadata:
            return

        self.clearContents()
        self._set_table(key=m.slug)

        for i in range(self.header.count()):
            font = self.horizontalHeaderItem(i).font()
            if i == idx:
                font.setWeight(QFont.ExtraBold)
            else:
                font.setWeight(QFont.Normal)
            self.horizontalHeaderItem(i).setFont(font)

    @Slot()
    def _new_data(self):
        """
        Check for new PBs.

        Return message string if there is a new PB. Otherwise return None.
        """
        # TODO this calls _get_best_sessions but not _set_table?
        # is _get_best_sessions being called multiple times?
        pb = self._get_best_sessions(num=self.rowCount(), key=self.select_key)
        newDates = [row["date"] for row in pb]
        dates = [row["date"] for row in self.items]
        if newDates != dates:
            i = 0
            if len(dates) > 0:
                while newDates[i] == dates[i]:
                    i += 1
            self.newIdx = i
            msg = self._make_message(self.select_key, i, pb[i][self.select_key])
            return msg
        else:
            None

    @Slot(int, int, int, int)
    def _cell_changed(self, row, column, previousRow, previousColumn):
        """Emit `itemSelected` with date of selected row"""
        if len(self.items) > 0:
            idx = self.items[row]["idx"]
            self.itemSelected.emit(self.data.row(idx)["date"])

    def _make_message(self, key, idx, value):
        """Return message string for new PB"""
        measure = self._activity[key]
        if measure.show_unit and measure.unit is not None:
            value = f"{value} {measure.unit}"
        colour = "#f7f13b"

        msg = f"<span>New #{idx+1} {key} - </span>"
        msg += f"<span style='color: {colour}'>{value}</span>!"

        return msg


class NewPBDialog(TimerDialog):
    """Dialog showing a message congratulating the user on a new PB.

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

    def set_message(self, text):
        self.label.setText(text)
