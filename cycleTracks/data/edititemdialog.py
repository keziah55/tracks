"""
Dialog box when users can edit rows from the CycleDataViewer.
"""
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QPushButton,
                             QVBoxLayout, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import Qt

class EditItemDialog(QDialog):
    
    def __init__(self, items, header, itemHeader=None):
        super().__init__()
        
        if itemHeader is None:
            itemHeader = header
        
        self.table = QTableWidget(len(items), len(header))
        self.table.setHorizontalHeaderLabels(header)
        for row, item in enumerate(items):
            col = 0
            for idx in range(item.columnCount()):
                if itemHeader[idx] in header:
                    text = item.text(idx)
                    tableItem = QTableWidgetItem(text)
                    tableItem.setFlags(Qt.ItemIsEditable|Qt.ItemIsEnabled)
                    self.table.setItem(row, col, tableItem)
                    col += 1
            
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        
        okButton =  self.buttonBox.button(QDialogButtonBox.Ok)
        okButton.clicked.connect(self.accept)
        cancelButton = self.buttonBox.button(QDialogButtonBox.Cancel)
        cancelButton.clicked.connect(self.reject)
        
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

        self.setWindowTitle("Edit or remove data")