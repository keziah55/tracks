"""
Plot preferences
"""

from datetime import date
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QHBoxLayout, QSpinBox, 
                             QVBoxLayout, QWidget, QLineEdit, QPushButton,
                             QColorDialog, QGridLayout, QLabel)
from PyQt5.QtCore import QTimer, pyqtSlot as Slot
from PyQt5.QtGui import QPalette, QColor
from customQObjects.widgets import GroupWidget
from customQObjects.core import Settings

class StyleDesigner(QWidget):
    
    def __init__(self, name, style, invalidNames=[]):
        super().__init__()
        
        self.invalidNames = invalidNames
        
        self.layout = QGridLayout()
        
        self.nameEdit = QLineEdit()
        self.setName(name)
        self.layout.addWidget(self.nameEdit, 0, 0, 1, -1)
        
        self.colours = {}
        row = 1
        for key in style:
            if key == "highlightPoint":
                label = "Highlight point"
            else:
                label = key.capitalize()
            colourName = QLabel(label)
            colourValue = QLabel()
            self.colours[key] = colourValue
            self.layout.addWidget(colourName, row, 0)
            self.layout.addWidget(colourValue, row, 1)
            row += 1
            
        self.saveButton = QPushButton("Add custom theme")
        self.layout.addWidget(self.saveButton, row, 1)
        self.setLayout(self.layout)
        
        self.setStyle(style)
        
        self.validateTimer = QTimer()
        self.validateTimer.setSingleShot(True)
        self.validateTimer.setInterval(50)
        self.validateTimer.timeout.connect(self._validate)
        self.nameEdit.textChanged.connect(self.validateTimer.start)
        self._validate()
        
    @property
    def name(self):
        return self.nameEdit.text()
        
    @property
    def invalidNames(self):
        return self._invalidNames
    
    @invalidNames.setter
    def invalidNames(self, names):
        names = [name.lower() for name in names]
        self._invalidNames = names
        
    def appendInvalidName(self, name):
        self.invalidNames.append(name.lower())
        
    def setName(self, name):
        self.nameEdit.setText(name.lower())
        
    def setStyle(self, style, name=None):
        for key, value in style.items():
            widget = self.colours[key]
            colour = QColor(value['colour'])
            widget.setPalette(QPalette(colour))
            widget.setAutoFillBackground(True)
        
        if name is not None:
            self.setName(name)
        
    def _validate(self):
        name = self.nameEdit.text().lower()
        if name in self.invalidNames:
            self.saveButton.setEnabled(False)
        else:
            self.saveButton.setEnabled(True)

class PlotPreferences(QWidget):
    
    def __init__(self, mainWindow):
        super().__init__()
        self.mainWindow = mainWindow
        
        self.settings = Settings()
        self.settings.beginGroup("plot")
        
        plotStyleGroup = GroupWidget("Plot style")
        self.plotStyleList = QComboBox()
        self.plotStyleList.addItems(["Dark", "Light", "Add custom theme..."])
        plotStyle = self.settings.value("style", "dark")
        self.plotStyleList.setCurrentText(plotStyle.capitalize())
        
        self.customStyle = StyleDesigner(plotStyle, self.mainWindow.plot.getStyle(plotStyle),
                                         invalidNames=["dark", "light"])
        self.customStyle.setEnabled(False)
        self.plotStyleList.currentTextChanged.connect(self._updateCustomStyleWidget)
        
        plotStyleGroup.addWidget(self.plotStyleList)
        plotStyleGroup.addWidget(self.customStyle)

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
        
        style = self.plotStyleList.currentText().lower()
        self.mainWindow.plot.setStyle(style)
        
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
        self.settings.setValue("style", style)
        
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
            
    def _updateCustomStyleWidget(self, name):
        if name == "Add custom theme...":
            self.customStyle.setEnabled(True)
            self.customStyle.setName(name=f"custom-{self.customStyle.name}")
        else:
            name = name.lower()
            style = self.mainWindow.plot.getStyle(name)
            self.customStyle.setStyle(style, name=name)
            self.customStyle.setEnabled(False)
            