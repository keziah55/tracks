from PyQt5.QtCore import Qt, pyqtSlot as Slot, pyqtSignal as Signal
from PyQt5.QtGui import QBrush, QColor
from cycleTracks.util import (isDate, isFloat, isInt, isDuration, parseDate, 
                              parseDuration)
from functools import partial

class AddDataTableMixin(object):
    
    invalid = Signal(int, int)
    """ **signal** invalid(int `row`, int `col`)
    
        Emitted if the data in cell `row`,`col` is invalid.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.headerLabels = ['Date', 'Time', 'Distance (km)', 'Calories', 'Gear']
        
        # dict of methods to validate and cast types for input data in each column
        validateMethods = [isDate, isDuration, isFloat, 
                           isFloat, isInt]
        parseDatePd = partial(parseDate, pd_timestamp=True)
        castMethods = [parseDatePd, parseDuration, float, float, int]
        self.mthds = {name:{'validate':validateMethods[i], 'cast':castMethods[i]}
                      for i, name in enumerate(self.headerLabels)}
        
        self.defaultBrush = self.table.item(0,0).background()
        self.invalidBrush = QBrush(QColor("#910404"))
        
        self.invalid.connect(self._invalid)
        
    @Slot(int, int)
    def _invalid(self, row, col):
        """ Set the background of cell `row`,`col` to the `invalidBrush` and 
            disable the 'Ok' button.
        """
        self.table.item(row, col).setBackground(self.invalidBrush)
        if hasattr(self, "okButton"):
            self.okButton.setEnabled(False)
        
    @Slot()
    def _validate(self):
        """ Validate all data in the table. 
        
            If data is valid and the widget has an `okButton`, it will be enabled.
        """
        # it would be more efficient to only validate a single cell, after its
        # text has been changed, but this table is unlikely to ever be more 
        # than a few rows long, so this isn't too inefficient
        allValid = True
        for row in range(self.table.rowCount()):
            for col, name in enumerate(self.headerLabels):
                item = self.table.item(row, col)
                value = item.text()
                mthd = self.mthds[name]['validate']
                valid = mthd(value)
                if not valid:
                    if (row, col) in self._clicked:
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
                mthd = self.mthds[name]['cast']
                value = mthd(value)
                values[name].append(value)
                
        return values