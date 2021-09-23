"""
Plot preferences
"""

from datetime import date
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QHBoxLayout, QSpinBox, 
                             QVBoxLayout, QWidget, QLineEdit, QPushButton,
                             QColorDialog, QGridLayout, QLabel)
from PyQt5.QtCore import QTimer, pyqtSlot as Slot, pyqtSignal as Signal
from PyQt5.QtGui import QPalette, QColor
from customQObjects.widgets import GroupWidget
from customQObjects.core import Settings

class StyleDesigner(QWidget):
    
    def __init__(self, name=None, style=None, styleKeys=None, invalidNames=[]):
        super().__init__()
        
        if style is None and styleKeys is None:
            raise ValueError("StyleDesigner needs either style dict or list of style keys.")
        
        if style is not None:
            styleKeys = self.style.keys()

        self.invalidNames = invalidNames
        
        self.layout = QGridLayout()
        
        self.nameEdit = QLineEdit()
        if name is not None:
            self.setName(name)
        self.layout.addWidget(self.nameEdit, 0, 0, 1, -1)
        
        self.colours = {}
        row = 1
        for key in styleKeys:
            if key == "highlightPoint":
                label = "Highlight point"
            else:
                label = key.capitalize()
            colourName = QLabel(label)
            colourValue = ColourButton()
            self.colours[key] = colourValue
            self.layout.addWidget(colourName, row, 0)
            self.layout.addWidget(colourValue, row, 1)
            self.colours[key].clicked.connect(self.setColour)
            row += 1
            
        self.saveButton = QPushButton("Add custom theme")
        self.layout.addWidget(self.saveButton, row, 1)
        self.setLayout(self.layout)
        
        if style is not None:
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
            widget.setColour(value['colour'])
        if name is not None:
            self.setName(name)
        
    def _validate(self):
        name = self.nameEdit.text().lower()
        if name in self.invalidNames:
            self.saveButton.setEnabled(False)
        else:
            self.saveButton.setEnabled(True)
            
    def setColour(self, widget, initialColour):
        colour = QColorDialog.getColor(QColor(initialColour), self)
        if colour.isValid(): 
            widget.setColour(colour)


class ColourButton(QLabel):
    """ QLabel that responds to mouse clicks by emitting a `clicked` signal.
    
        Created to mimic a QPushButton that does not change style when clicked.
    """
    
    clicked = Signal(object, str)
    """ clicked = Signal(ColourButton button, str colour) 
    
        Emitted when clicked, with the reference to the button and its current colour.
    """
    
    def __init__(self, *args, colour=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._colour = None
        if colour is not None:
            self.setColour(colour)
            
    def mouseReleaseEvent(self, ev):
        self.clicked.emit(self, self.colour)
        
    @property
    def colour(self):
        """ Return the current colour of the button, as a string. 
        
            Returns None if colour has not been set.
        """
        if self._colour is None:
            return None
        else:
            return self._colour.name()

    def setColour(self, colour):
        """ Set the colour of the ColourButton. 
        
            `colour` can be either a QColor instance or any valid arg to QColor.
            See `QColor docs <https://doc.qt.io/qt-5/qcolor.html>_` for more details.
        """
        if isinstance(colour, str):
            colour = QColor(colour)
        if not isinstance(colour, QColor):
            raise TypeError()
        self._colour = colour
        self.setPalette(QPalette(self._colour))
        self.setAutoFillBackground(True)

class PlotPreferences(QWidget):
    
    def __init__(self, mainWindow):
        super().__init__()
        self.mainWindow = mainWindow
        
        plotStyleGroup = GroupWidget("Plot style")
        self.plotStyleList = QComboBox()
        self.plotStyleList.addItems(["Dark", "Light", "Add custom theme..."])
        
        self.customStyle = StyleDesigner(styleKeys=self.mainWindow.plot.getStyleKeys(),
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
        
        self.setCurrentValues()
        # apply initial state
        self.apply()
        
    def setCurrentValues(self):
        self.settings = Settings()
        self.settings.beginGroup("plot")

        plotStyle = self.settings.value("style", "dark")
        self.plotStyleList.setCurrentText(plotStyle.capitalize())
        
        self.customStyle.setName(plotStyle)
        self.customStyle.setStyle(self.mainWindow.plot.getStyle(plotStyle))
        
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
        
        self.settings.endGroup()
        
        
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
            