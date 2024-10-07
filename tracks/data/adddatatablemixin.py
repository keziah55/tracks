from qtpy.QtWidgets import QTableWidget
from qtpy.QtCore import Qt, QTimer, Slot, Signal
from qtpy.QtGui import QBrush, QColor
from functools import partial
from collections import namedtuple
from tracks.util import get_cast_func, get_validate_func

ValidateFuncs = namedtuple("ValidateFuncs", ["validate", "cast"])


class AddDataTableMixin(object):
    """
    Mixin providing validation and type casting for a table for adding data.

    Should be used as part of a widget that has a `table` attribute. If it
    also has a `okButton`, this will be enabled/diabled when validation
    is performed.
    """

    invalid = Signal(int, int)
    """ **signal** invalid(int `row`, int `col`)

        Emitted if the data in cell `row`,`col` is invalid.
    """

    def __init__(self, activity, *args, emptyDateValid=True, **kwargs):
        super().__init__(*args, **kwargs)

        self._activity = activity

        self._measures = self._activity.filter_measures("relation", lambda r: r is None)

        self.header_labels = [m.full_name for m in self._measures.values()]
        self.headerLabelColumnOffset = 0
        self.table = QTableWidget(0, len(self.header_labels))
        self.table.setHorizontalHeaderLabels(self.header_labels)
        self.table.verticalHeader().setVisible(False)

        self.funcs = {}
        for name, m in self._activity.measures.items():
            if m.relation is not None:
                continue

            if m.dtype == "date":
                validate_func = partial(
                    get_validate_func("date"), allowEmpty=emptyDateValid
                )
                cast_func = partial(get_cast_func("date"))
            else:
                cast_func = get_cast_func(m.dtype)
                validate_func = get_validate_func(m.dtype)

            self.funcs[m.slug] = ValidateFuncs(validate_func, cast_func)

        self.validateTimer = QTimer()
        self.validateTimer.setInterval(100)
        self.validateTimer.setSingleShot(True)
        self.validateTimer.timeout.connect(self._validate)
        self.table.cellChanged.connect(self.validateTimer.start)

        self.invalid.connect(self._invalid)

    @property
    def _default_brush(self):
        # made this a property rather than setting in constructor as the mixin
        # doesn't have a `table` attribute when __init__ is called
        return self.table.item(0, 0).background()

    @property
    def _invalid_brush(self):
        return QBrush(QColor("#910404"))

    @Slot(int, int)
    def _invalid(self, row, col):
        """
        Set the background of cell `row`,`col` to the `_invalid_brush` and disable the 'Ok' button.
        """
        self.table.item(row, col).setBackground(self._invalid_brush)
        if hasattr(self, "okButton"):
            self.okButton.setEnabled(False)

    @Slot()
    def _validate(self):
        """
        Validate all data in the table.

        If data is valid and the widget has an `okButton`, it will be enabled.
        """
        # it would be more efficient to only validate a single cell, after its
        # text has been changed, but this table is unlikely to ever be more
        # than a few rows long, so this isn't too inefficient
        allValid = True
        for row in range(self.table.rowCount()):
            for col, name in enumerate(self._measures):
                col += self.headerLabelColumnOffset
                item = self.table.item(row, col)
                value = item.text()
                mthd = self.funcs[name].validate
                valid = mthd(value)
                if not valid:
                    if hasattr(self, "_clicked"):
                        if (row, col) not in self._clicked:
                            continue
                    self.invalid.emit(row, col)
                    allValid = False
                elif (
                    valid
                    and self.table.item(row, col).background() == self._invalid_brush
                ):
                    self.table.item(row, col).setBackground(self._default_brush)

        if allValid and hasattr(self, "okButton"):
            self.okButton.setEnabled(True)

        return allValid

    def _get_values(self):
        values = {name: [] for name in self._measures}

        self.table.sortItems(0, Qt.AscendingOrder)

        for row in range(self.table.rowCount()):
            for col, name in enumerate(self._measures):
                item = self.table.item(row, col)
                value = item.text()
                func = self.funcs[name].cast
                value = func(value)
                values[name].append(value)

        return values
