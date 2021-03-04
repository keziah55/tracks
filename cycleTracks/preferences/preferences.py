"""
Preferences dialog
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QAbstractScrollArea, QDialog, QDialogButtonBox, 
                             QListWidget, QStackedWidget, QVBoxLayout, QHBoxLayout)

from .plotpref import PlotPreferences

class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.contentsWidget = QListWidget()
        self.pagesWidget = QStackedWidget()
        
        self.plotPref = PlotPreferences(parent)
        self.pagesWidget.addWidget(self.plotPref)
        
        self.contentsWidget.addItem("Plot")
        self.contentsWidget.currentItemChanged.connect(self.changePage)
        self.contentsWidget.setCurrentRow(0)
        
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Apply|QDialogButtonBox.Close)
        
        okButton =  self.buttonBox.button(QDialogButtonBox.Ok)
        okButton.clicked.connect(self.ok)
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

        self.setWindowTitle("Config Dialog")

    def changePage(self, current, previous):
        if not current:
            current = previous
        self.pagesWidget.setCurrentIndex(self.contentsWidget.row(current))
        
    def apply(self):
        self.pagesWidget.currentWidget().apply()
        
    def ok(self):
        for idx in range(1, self.pagesWidget.count()):
            self.pagesWidget.widget(idx).apply()
        self.accept()