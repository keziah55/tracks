"""
Dialog box when users can edit rows from the CycleDataViewer.
"""
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QPushButton, QHeaderView,
                             QVBoxLayout, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal as Signal
from PyQt5.QtGui import QIcon

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
    
    
class EditItemDialog(QDialog):
    
    def __init__(self, items, header, itemHeader=None):
        super().__init__()
        
        if itemHeader is None:
            itemHeader = header
        
        header += ["Remove"]
        self.table = QTableWidget(len(items), len(header))
        self.table.setHorizontalHeaderLabels(header)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.verticalHeader().hide()
        
        self.buttons = []
        
        for row, item in enumerate(items):
            col = 0
            for idx in range(item.columnCount()):
                if itemHeader[idx] in header:
                    text = item.text(idx)
                    tableItem = QTableWidgetItem(text)
                    tableItem.setTextAlignment(Qt.AlignCenter)
                    tableItem.setFlags(Qt.ItemIsEditable|Qt.ItemIsEnabled)
                    self.table.setItem(row, col, tableItem)
                    col += 1
            
            button = RemoveButton()
            self.buttons.append(button)
            button.buttonClicked.connect(self.removeRow)
            self.table.setCellWidget(row, col, button)
            col += 1
            
        # self.table.horizontalHeader().resizeSections(QHeaderView.ResizeToContents)
        # self.table.resizeRowsToContents()
        # self.table.resizeColumnsToContents() 

             
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        
        okButton =  self.buttonBox.button(QDialogButtonBox.Ok)
        okButton.clicked.connect(self.accept)
        cancelButton = self.buttonBox.button(QDialogButtonBox.Cancel)
        cancelButton.clicked.connect(self.reject)
        
        ### see AddCycleData sizeHint?
        
        ### https://stackoverflow.com/a/17565859
        # width = self.table.horizontalHeader().length() + 24
        # n = min(8, self.table.rowCount())
        # height = self.table.horizontalHeader().height() * n #self.table.verticalHeader().length() + 32
        # self.setFixedSize(width, height)
        
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

        self.setWindowTitle("Edit or remove data")
        
    # def sizeHint(self):
        # return self.table.size()
    
    def removeRow(self, button):
        idx = self.buttons.index(button)
        self.buttons.pop(idx)
        self.table.removeRow(idx)