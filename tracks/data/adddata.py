"""
QWidget containing a QTableWidget, where users can add new cycling data. 

User input will be validated live; if data is invalid, the 'Ok' button cannot
be clicked.
"""

from qtpy.QtWidgets import (
    QTableWidgetItem,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
)
from qtpy.QtCore import QSize, Qt
from qtpy.QtCore import Signal, Slot
from qtpy.QtGui import QKeySequence

from .adddatatablemixin import AddDataTableMixin
from tracks.util import dayMonthYearToFloat, parseDate

from datetime import datetime
import calendar


class TableWidgetDateItem(QTableWidgetItem):
    """QTableWidgetItem, which will sort dates."""

    def __lt__(self, other):
        item0 = self.text()
        item1 = other.text()
        item0, item1 = [parseDate(item).strftime("%d %b %Y") for item in [item0, item1]]
        value0 = dayMonthYearToFloat(item0)
        value1 = dayMonthYearToFloat(item1)
        return value0 < value1


class AddData(AddDataTableMixin, QWidget):
    """QWidget containing a QTableWidget, where users can add new data.

    User input is validated live; it is not possible to submit invalid data.
    """

    new_data = Signal(dict)
    """ **signal** new_data(dict `data`)

        Emitted with a dict to be appended to the DataFrame.
    """

    row_removed = Signal()
    """ **signal** row_removed()

        Emitted when the current row is removed from the table.
    """

    def __init__(self, activity, widthSpace=10):
        super().__init__(activity)

        self.widthSpace = widthSpace

        self._clicked = []
        self._makeEmptyRow()

        self.table.currentCellChanged.connect(self._cell_clicked)

        self.addLineButton = QPushButton("New line")
        self.rmvLineButton = QPushButton("Remove line")
        self.rmvLineButton.setToolTip("Remove currently selected line")
        self.okButton = QPushButton("Ok")
        try:
            self.okButton.setShortcut(Qt.Key_Enter)
        except:
            self.okButton.setShortcut(QKeySequence(Qt.Key_Enter))

        self.addLineButton.clicked.connect(self._makeEmptyRow)
        self.rmvLineButton.clicked.connect(self._remove_selected_row)
        self.okButton.clicked.connect(self._add_data)

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
    def _cell_clicked(self, row, col):
        if (row, col) not in self._clicked:
            self._clicked.append((row, col))

    @Slot()
    def _makeEmptyRow(self):
        """Add a new row to the end of the table, with today's date in the
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

        # for i in range(len(self.header_labels[1:])):
        for i in range(1, self.table.columnCount()):
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, i, item)
        self._clicked = [item for item in self._clicked if item[0] != row]
        self._cell_clicked(row, 0)

    @Slot()
    def _remove_selected_row(self):
        """Remove the currently selected row from the table."""
        row = self.table.currentRow()
        self._clicked = [item for item in self._clicked if item[0] != row]
        self.table.removeRow(row)
        self.row_removed.emit()

    @Slot()
    def _add_data(self):
        """Take all data from the table and emit it as a list of dicts with
        the `new_data` signal, then clear the table.
        """
        self.table.focusNextChild()
        valid = self._validate()
        if not valid:
            return None

        values = self._get_values()
        self.new_data.emit(values)

        for row in reversed(range(self.table.rowCount())):
            self.table.removeRow(row)
        self._clicked = []
        self._makeEmptyRow()
