"""
Plot preferences
"""

from datetime import date
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QHBoxLayout, QSpinBox, 
                             QVBoxLayout, QWidget, QRadioButton, QLabel)
from PyQt5.QtCore import pyqtSlot as Slot
from customQObjects.widgets import GroupWidget
from customQObjects.core import Settings

class PlotPreferences(QWidget):
    
    def __init__(self, mainWindow):
        super().__init__()
        self.mainWindow = mainWindow
        
        self.settings = Settings()
        self.settings.beginGroup("plot")
        
        plotStyleGroup = GroupWidget("Plot style")
        self.darkStyleButton = QRadioButton("Dark")
        self.lightStyleButton = QRadioButton("Light")
        plotStyle = self.settings.value("style", "dark")
        button = self.darkStyleButton if plotStyle == "dark" else self.lightStyleButton
        button.setChecked(True)
        self.styleLabel = QLabel("Style will be updated when Cycle Tracks is next opened.")
        
        for button in [self.darkStyleButton, self.lightStyleButton]:
            button.clicked.connect(lambda _: self.styleLabel.setVisible(True))
        
        plotStyleGroup.addWidget(self.darkStyleButton)
        plotStyleGroup.addWidget(self.lightStyleButton)
        plotStyleGroup.addWidget(self.styleLabel)
        self.styleLabel.setVisible(False)
        
        plotConfigGroup = GroupWidget("Default plot range", layout="vbox")
        
        self.plotRangeCombo = QComboBox()
        self.plotRangeCombo.addItem("1 month")
        self.plotRangeCombo.addItem("3 months")
        self.plotRangeCombo.addItem("6 months")
        self.plotRangeCombo.addItem("1 year")
        self.plotRangeCombo.addItem("Current year")
        self.plotRangeCombo.addItem("All")
        
        self.customRangeCheckBox = QCheckBox("Custom range")
        self.customRangeSpinBox = QSpinBox()
        self.customRangeSpinBox.setSuffix(" months")
        maxMonths = len(mainWindow.data.splitMonths())
        self.customRangeSpinBox.setRange(1, maxMonths)
        self.customRangeCheckBox.clicked.connect(self.setCustomRange)
        
        customRange = self.settings.value("customRange", False)
        rng = self.settings.value("range", "All")
        
        self.setCustomRange(customRange)
        if customRange:
            rng = int(rng)
            self.customRangeSpinBox.setValue(rng)
        else:
            items = [self.plotRangeCombo.itemText(idx) for idx in range(self.plotRangeCombo.count())]
            idx = items.index(rng)
            self.plotRangeCombo.setCurrentIndex(idx)
            
        plotRangeLayout = QHBoxLayout()
        plotRangeLayout.addWidget(self.plotRangeCombo)
        
        customRangeLayout = QHBoxLayout()
        customRangeLayout.addWidget(self.customRangeCheckBox)
        customRangeLayout.addWidget(self.customRangeSpinBox)
        
        plotConfigGroup.addLayout(plotRangeLayout)
        plotConfigGroup.addLayout(customRangeLayout)
        
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(plotStyleGroup)
        mainLayout.addWidget(plotConfigGroup)
        mainLayout.addStretch(1)

        self.setLayout(mainLayout)
        self.settings.endGroup()
        
        # apply initial state
        self.apply()
        
    def apply(self):
        customRange = self.customRangeCheckBox.isChecked()
        if customRange:
            months = self.customRangeSpinBox.value()
        else:
            text = self.plotRangeCombo.currentText()
            if text == "1 year":
                text = "12 months"
            elif text == "Current year":
                text = f"{date.today().month} months"
            months = None if text == 'All' else int(text.strip(' months'))
        self.mainWindow.plot.setXAxisRange(months, fromRecentSession=False)
        
        self.settings.beginGroup("plot")
        if self.darkStyleButton.isChecked():
            self.settings.setValue("style", "dark")
        else:
            self.settings.setValue("style", "light")
        
        self.settings.setValue("customRange", customRange)
        if customRange:
            self.settings.setValue("range", self.customRangeSpinBox.value())
        else:
            self.settings.setValue("range", self.plotRangeCombo.currentText())
        self.settings.endGroup()
    
    @Slot(bool)
    def setCustomRange(self, custom):
        self.customRangeCheckBox.setChecked(custom)
        if custom:
            self.customRangeSpinBox.setEnabled(True)
            self.plotRangeCombo.setEnabled(False)
        else:
            self.customRangeSpinBox.setEnabled(False)
            self.plotRangeCombo.setEnabled(True)