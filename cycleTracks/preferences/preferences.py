"""
Preferences dialog
"""
from qtpy.QtWidgets import (QAbstractScrollArea, QDialog, QDialogButtonBox, 
                             QListWidget, QStackedWidget, QVBoxLayout, QHBoxLayout)

from .plotpref import PlotPreferences
from .datapref import DataPreferences

class PreferencesDialog(QDialog):
    
    pages = [PlotPreferences, DataPreferences]
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.contentsWidget = QListWidget()
        self.pagesWidget = QStackedWidget()
        
        pages = sorted(self.pages, key=lambda widget: widget.name)
        
        for page in pages:
            widget = page(parent)
            self.pagesWidget.addWidget(widget)
            self.contentsWidget.addItem(widget.name)

        self.contentsWidget.currentItemChanged.connect(self.changePage)
        self.contentsWidget.setCurrentRow(0)
        
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Apply|QDialogButtonBox.Close)
        
        okButton =  self.buttonBox.button(QDialogButtonBox.Ok)
        okButton.clicked.connect(self.ok)
        applyButton =  self.buttonBox.button(QDialogButtonBox.Apply)
        applyButton.clicked.connect(self.apply)
        closeButton = self.buttonBox.button(QDialogButtonBox.Close)
        closeButton.clicked.connect(self.close)

        horizontalLayout = QHBoxLayout()
        horizontalLayout.addWidget(self.contentsWidget)
        horizontalLayout.addWidget(self.pagesWidget)
        
        self.contentsWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(horizontalLayout)
        mainLayout.addWidget(self.buttonBox)

        self.setLayout(mainLayout)

        self.setWindowTitle("Preferences")

    def changePage(self, current, previous):
        if not current:
            current = previous
        self.pagesWidget.setCurrentIndex(self.contentsWidget.row(current))
        
    def show(self):
        for n in range(self.pagesWidget.count()):
            self.pagesWidget.widget(n).setCurrentValues()
        super().show()
        
    def apply(self):
        self.pagesWidget.currentWidget().apply()
        
    def ok(self):
        for idx in range(self.pagesWidget.count()):
            self.pagesWidget.widget(idx).apply()
        self.accept()