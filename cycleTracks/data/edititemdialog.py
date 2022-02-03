"""
Dialog box when users can edit rows from the CycleDataViewer.
"""
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QPushButton, QVBoxLayout, 
                             QTableWidget, QTableWidgetItem,
                             QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal as Signal
from PyQt5.QtGui import QIcon
from .adddatatablemixin import AddDataTableMixin

class RemoveButton(QPushButton):
    
    buttonClicked = Signal(QPushButton)
    """ **signal** buttonClicked(QPushButton self)
    
        When clicked, emit signal with reference to self.
    """
    
    def __init__(self):
        icon = QIcon.fromTheme("list-remove")
        super().__init__(icon, "")
        self.clicked.connect(self._emitButtonClicked)
        
    def _emitButtonClicked(self):
        self.buttonClicked.emit(self)
    
    
class EditItemDialog(AddDataTableMixin, QDialog):
    
    def __init__(self, items, itemHeader=None):
        super().__init__(emptyDateValid=False)
        
        if itemHeader is None:
            itemHeader = self.headerLabels
        
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.table.insertColumn(self.table.columnCount())
        self.table.setHorizontalHeaderLabels(self.headerLabels + ["Remove"])
        
        self.removed = []
        self.rows = {}
        
        for row, item in enumerate(items):
            self.table.insertRow(row)
            col = 0
            tableItems = {}
            for idx in range(item.columnCount()):
                if itemHeader[idx] in self.headerLabels:
                    text = item.text(idx)
                    tableItem = QTableWidgetItem(text)
                    tableItem.setTextAlignment(Qt.AlignCenter)
                    tableItem.setFlags(Qt.ItemIsEditable|Qt.ItemIsEnabled)
                    self.table.setItem(row, col, tableItem)
                    tableItems[itemHeader[idx]] = tableItem
                    col += 1
            
            button = RemoveButton()
            button.buttonClicked.connect(self.removeRow)
            self.table.setCellWidget(row, col, button)
            
            self.rows[item.index] = {'tableItems':tableItems, 'button':button, 'rowNum':row}
            
            col += 1
            
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        
        self.okButton =  self.buttonBox.button(QDialogButtonBox.Ok)
        self.okButton.clicked.connect(self.accept)
        cancelButton = self.buttonBox.button(QDialogButtonBox.Cancel)
        cancelButton.clicked.connect(self.reject)
        
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)
        
        # make the QDialog the same size as the table widget
        # i don't know why this is such a faff
        # the dialog will always be the size of the table and there will be no scroll bars
        pad = 2
        self.table.resizeRowsToContents()
        self.table.resizeColumnsToContents() 
        # manually add the widths of each column for width
        # then do the same for the height
        # getting the `length` of the header items did not work
        width = pad
        for i in range(self.table.columnCount()):
            width += self.table.columnWidth(i)
        # start with one row height for the header
        # directly getting the header height is completely wrong
        height = self.table.rowHeight(0) + pad 
        for i in range(self.table.rowCount()):
            height += self.table.rowHeight(i)
        # then set the table's minimum size and the dialog's size policy
        self.table.setMinimumSize(width, height)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.setWindowTitle("Edit or remove data")
        
    def removeRow(self, button):
        """ Remove the row where `button` is. """
        for index, dct in self.rows.items():
            if dct['button'] == button:
                # remove row from table and store index                
                self.table.removeRow(dct['rowNum'])
                self.removed.append(index)
        for index in self.removed:
            # update `rows` dict, so it is correct when getting values
            self.rows.pop(index)
        
    def getValues(self):
        """ Return dict of index: row dict pairs, and list of removed indices. """
        
        values = {}
        
        for index, dct in self.rows.items():
            tableItems = dct['tableItems']
            rowDct = {}
            for key, tableItem in tableItems.items():
                value = tableItem.text()
                mthd = self.mthds[key]['cast']
                value = mthd(value)
                rowDct[key] = value
            values[index] = rowDct
        
        return values, self.removed
                