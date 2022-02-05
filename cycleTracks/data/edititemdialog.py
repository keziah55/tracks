"""
Dialog box when users can edit rows from the CycleDataViewer.
"""
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QVBoxLayout, QWidget,
                             QTableWidgetItem, QSizePolicy, QCheckBox)
from PyQt5.QtCore import Qt
from .adddatatablemixin import AddDataTableMixin
from dataclasses import dataclass
    
@dataclass
class BaseRow:
    index: int
    tableItems: list
    checkBox: QCheckBox
    
    @property
    def checked(self):
        return self.checkBox.isChecked()
    
    def enable(self, state):
        if state:
            flags = Qt.ItemIsEditable|Qt.ItemIsEnabled
        else:
            flags = Qt.ItemIsSelectable
        for item in self.tableItems.values():
            item.setFlags(flags)
    
class Row(BaseRow):
    # inherit dataclass BaseRow and connect the checkBox to enable
    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.checkBox.clicked.connect(self.enable)
    
class EditItemDialog(AddDataTableMixin, QDialog):
    
    def __init__(self, items, itemHeader=None):
        super().__init__(emptyDateValid=False)
        
        if itemHeader is None:
            itemHeader = self.headerLabels
        
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.table.insertColumn(self.table.columnCount())
        self.table.setHorizontalHeaderLabels([""] + self.headerLabels)
        self.headerLabelColumnOffset = 1
        
        self.rows = []
        
        for rowNum, item in enumerate(items):
            self.table.insertRow(rowNum)
            col = 0
            
            checkBox = QCheckBox()
            checkBox.setChecked(True)
            checkBox.setToolTip("Uncheck to remove this data")
            # have to make a widget with a layout and add the check box to 
            # the layout in order to have the check box centred...
            widget = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(checkBox)
            layout.setAlignment(Qt.AlignCenter)
            widget.setLayout(layout)
            self.table.setCellWidget(rowNum, col, widget)
            col += 1
            
            tableItems = {}
            for idx in range(item.columnCount()):
                if itemHeader[idx] in self.headerLabels:
                    text = item.text(idx)
                    tableItem = QTableWidgetItem(text)
                    tableItem.setTextAlignment(Qt.AlignCenter)
                    tableItem.setFlags(Qt.ItemIsEditable|Qt.ItemIsEnabled)
                    self.table.setItem(rowNum, col, tableItem)
                    tableItems[itemHeader[idx]] = tableItem
                    col += 1
            
            self.rows.append(Row(item.index, tableItems, checkBox))
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
        
        
    def getValues(self):
        """ Return dict of index: row dict pairs, and list of indices to be removed. """
        
        values = {}
        remove = []
        
        for row in self.rows:
            if not row.checked:
                remove.append(row.index)
            else:
                dct = {}
                for key, tableItem in row.tableItems.items():
                    value = tableItem.text()
                    mthd = self.mthds[key]['cast']
                    value = mthd(value)
                    dct[key] = value
                values[row.index] = dct
        
        return values, remove
                