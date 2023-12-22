from qtpy.QtWidgets import QTableWidget
from qtpy.QtCore import Qt, QTimer, Slot, Signal
from qtpy.QtGui import QBrush, QColor
from tracks.util import isDate, isFloat, isInt, isDuration, parseDate, parseDuration
from functools import partial
from collections import namedtuple

ValidateFuncs = namedtuple("ValidateFuncs", ["validate", "cast"])

class AddDataTableMixin(object):
    """ Mixin providing validation and type casting for a table for adding data.
    
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
        
        self.headerLabels = self._activity.user_input_header #['Date', 'Time', 'Distance (km)', 'Calories', 'Gear']
        self.headerLabelColumnOffset = 0
        self.table = QTableWidget(0, len(self.headerLabels))
        self.table.setHorizontalHeaderLabels(self.headerLabels)
        self.table.verticalHeader().setVisible(False)
        
        # dict of methods to validate and cast types for input data in each column
        is_date_partial = partial(isDate, allowEmpty=emptyDateValid)
        parse_date_partial = partial(parseDate, pd_timestamp=True)
        
        validate_methods = {
            "date": is_date_partial,
            "duration": isDuration,
            "float": isFloat,
            "int": isInt
        }
        cast_methods = {
            "date": parse_date_partial,
            "duration": parseDuration,
            "float": float,
            "int": int
        }
        
        self.mthds = {
            m.full_name: ValidateFuncs(validate_methods[m.dtype], cast_methods[m.dtype])
            for name, m in self._activity.measures.items() if m.relation is None
        }
        
        self.validateTimer = QTimer()
        self.validateTimer.setInterval(100)
        self.validateTimer.setSingleShot(True)
        self.validateTimer.timeout.connect(self._validate)
        self.table.cellChanged.connect(self.validateTimer.start)
        
        self.invalid.connect(self._invalid)
        
    @property
    def defaultBrush(self):
        # made this a property rather than setting in constructor as the mixin
        # doesn't have a `table` attribute when __init__ is called
        return self.table.item(0,0).background()
    
    @property
    def invalidBrush(self):
        return QBrush(QColor("#910404"))
    
    @Slot(int, int)
    def _invalid(self, row, col):
        """ 
        Set the background of cell `row`,`col` to the `invalidBrush` and disable the 'Ok' button.
        """
        self.table.item(row, col).setBackground(self.invalidBrush)
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
            for col, name in enumerate(self.headerLabels):
                col += self.headerLabelColumnOffset
                item = self.table.item(row, col)
                value = item.text()
                mthd = self.mthds[name].validate
                valid = mthd(value)
                if not valid:
                    if hasattr(self, "_clicked"):
                        if (row, col) not in self._clicked:
                            continue
                    self.invalid.emit(row, col)
                    allValid = False
                elif valid and self.table.item(row, col).background() == self.invalidBrush:
                    self.table.item(row, col).setBackground(self.defaultBrush) 
                    
        if allValid and hasattr(self, "okButton"):
            self.okButton.setEnabled(True)
            
        return allValid
    
    def _getValues(self):
        
        values = {name:[] for name in self.headerLabels}
        
        self.table.sortItems(0, Qt.AscendingOrder)

        for row in range(self.table.rowCount()):
            for col, name in enumerate(self.headerLabels):
                item = self.table.item(row, col)
                value = item.text()
                mthd = self.mthds[name].cast
                value = mthd(value)
                values[name].append(value)
                
        return values