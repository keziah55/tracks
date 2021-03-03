"""
Plot preferences
"""

from PyQt5.QtWidgets import (QCheckBox, QComboBox, QGroupBox, QHBoxLayout, QLabel, 
                             QSpinBox, QVBoxLayout, QWidget)
from PyQt5.QtCore import pyqtSlot as Slot

class PlotPreferences(QWidget):
    
    def __init__(self, mainWindow):
        super().__init__()
        
        plotConfigGroup = QGroupBox("Default plot range")
        
        # plotRangeLabel = QLabel("Default plot range")
        self.plotRangeCombo = QComboBox()
        self.plotRangeCombo.addItem("1 month")
        self.plotRangeCombo.addItem("6 months")
        self.plotRangeCombo.addItem("1 year")
        self.plotRangeCombo.addItem("All")
        self.plotRangeCombo.setCurrentIndex(3)
        
        self.customRangeCheckBox = QCheckBox("Custom range")
        self.customRangeSpinBox = QSpinBox()
        self.customRangeSpinBox.setSuffix(" months")
        maxMonths = len(mainWindow.data.splitMonths())
        self.customRangeSpinBox.setRange(1, maxMonths)
        self.customRangeCheckBox.clicked.connect(self.setCustomRange)
        self.setCustomRange(False)
        
        plotRangeLayout = QHBoxLayout()
        plotRangeLayout.addWidget(self.plotRangeCombo)
        
        customRangeLayout = QHBoxLayout()
        customRangeLayout.addWidget(self.customRangeCheckBox)
        customRangeLayout.addWidget(self.customRangeSpinBox)
        
        plotConfigLayout = QVBoxLayout()
        plotConfigLayout.addLayout(plotRangeLayout)
        plotConfigLayout.addLayout(customRangeLayout)
        plotConfigGroup.setLayout(plotConfigLayout)
        
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(plotConfigGroup)
        mainLayout.addStretch(1)

        self.setLayout(mainLayout)
        
        
    def apply(self):
        pass
    
    @Slot(bool)
    def setCustomRange(self, custom):
        if custom:
            self.customRangeSpinBox.setEnabled(True)
            self.plotRangeCombo.setEnabled(False)
        else:
            self.customRangeSpinBox.setEnabled(False)
            self.plotRangeCombo.setEnabled(True)