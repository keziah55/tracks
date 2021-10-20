"""
Plot preferences
"""

from datetime import date
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QHBoxLayout, QSpinBox, 
                             QVBoxLayout, QWidget, QLineEdit, QPushButton,
                             QColorDialog, QGridLayout, QLabel, QSizePolicy)
from PyQt5.QtCore import QTimer, pyqtSlot as Slot, pyqtSignal as Signal, QSize
from PyQt5.QtGui import QPalette, QColor#, QPen, QBrush, QIcon, QPixmap, QImage, QPainter
# from pyqtgraph.graphicsItems.ScatterPlotItem import renderSymbol, drawSymbol
from customQObjects.widgets import GroupWidget
from customQObjects.core import Settings
from cycleTracks import makeForegroundIcon 

class StyleDesigner(QWidget):
    
    saveStyle = Signal(str, dict)
    
    symbols = {'o':'circle', 's':'square', 't':'triangle', 'd':'diamond', 
                '+':'plus', 't1':'triangle up', 't2':'triangle right', 
                't3':'triangle left', 'p':'pentagon', 'h':'hexagon', 
                'star':'star', 'x':'cross', 'arrow_up':'arrow up', 
                'arrow_right':'arrow right', 'arrow_down':'arrow down', 
                'arrow_left':'arrow left', 'crosshair':'crosshair'}
    
    @classmethod
    @property
    def reverseSymbolDict(cls):
        return {value:key for key, value in cls.symbols.items()}
 
    def __init__(self, name=None, style=None, styleKeys=None, symbolKeys=[], 
                 invalidNames=[]):
        super().__init__()
        
        if style is None and styleKeys is None:
            raise ValueError("StyleDesigner needs either style dict or list of style keys.")
        
        if style is not None:
            styleKeys = self.style.keys()

        self.invalidNames = invalidNames
        # self.editing = False
        
        self.layout = QGridLayout()
        
        self.nameEdit = QLineEdit()
        if name is not None:
            self.setName(name)
        self.layout.addWidget(self.nameEdit, 0, 0, 1, -1)
        
        listHeight = None
        
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
            if key in symbolKeys:
                symbolList = self._createSymbolList()
                self.layout.addWidget(symbolList, row, 2)
                if listHeight is None:
                    listHeight = symbolList.sizeHint().height()
            self.colours[key].clicked.connect(self.setColour)
            row += 1
            
        if listHeight is not None:
            for rowNum in range(self.layout.rowCount()):
                item = self.layout.itemAtPosition(rowNum, 1)
                item.widget().height = listHeight
            
        # TODO both save and cancel buttons currently don't do anything
        self.saveButton = QPushButton("Save theme")
        self.cancelButton = QPushButton("Cancel")
        # self.cancelButton.setVisible(False)
        self.layout.addWidget(self.saveButton, row, 1) # use 'row' value from above
        self.layout.addWidget(self.cancelButton, row, 2)
        self.setLayout(self.layout)
        
        self.saveButton.clicked.connect(self._saveStyle)
        self.setEditMode(False)
        
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
            
    def getStyle(self):
        style = {}
        for row in range(1, self.layout.rowCount()-1): # don't need first and last from layout
            key = self.layout.itemAtPosition(row, 0).widget().text().lower()
            colour = self.layout.itemAtPosition(row, 1).widget().colour
            
            # turn 'highlight point' back into 'highlightPoint'
            first, *rest = key.split(' ')
            key = first + ''.join([s.capitalize() for s in rest])
            style[key] = colour
            
            symbol = self.layout.itemAtPosition(row, 2)
            if symbol is not None:
                symbol = symbol.widget().currentText().lower()
                style[f"{key}Symbol"] = self.reverseSymbolDict[symbol]
        return self.name, style
    
    def _saveStyle(self):
        self.saveStyle.emit(*self.getStyle())
        self.setEditMode(False)
        
    def _validate(self):
        if not self.editing:
            name = self.nameEdit.text().lower()
            if name in self.invalidNames:
                self.saveButton.setEnabled(False)
            else:
                self.saveButton.setEnabled(True)
                
    def setEditMode(self, edit=None):
        if edit is not None:
            self.editing = edit
        if self.editing:
            self.saveButton.setEnabled(True)
            self.cancelButton.setVisible(True)
        else:
            self.cancelButton.setVisible(False)
            
    def setColour(self, widget, initialColour):
        colour = QColorDialog.getColor(QColor(initialColour), self)
        if colour.isValid(): 
            widget.setColour(colour)
            
    def _createSymbolList(self, colour=None):
        
        availableSymbols = ['x', 'o', 's', 't', 'd', '+', 't1', 't2', 't3', 'p', 
                            'h', 'star']
        
        widget = QComboBox()
        for name in availableSymbols:
            widget.addItem(self.symbols[name].capitalize())
        
        # if colour is None:
        #     colour = self.palette().color(self.foregroundRole())
        # if isinstance(colour, str):
        #     colour = QColor(colour)
        # pen = QPen(colour)
        # brush = QBrush(colour)
        # size = 512
        # widget = QComboBox()
        # for symbol in symbols:
        #     pixmap = QPixmap(size, size)
        #     pixmap.fill(QColor("#00000000"))
        #     painter = QPainter(pixmap)
        #     painter.setRenderHint(painter.RenderHint.Antialiasing)
        #     painter.resetTransform()
        #     painter.translate(256, 256)
        #     drawSymbol(painter, symbol, 128, pen, brush)
        #     painter.end()
        #     # pixmap = renderSymbol(symbol, size, pen, brush, device=pixmap)
        #     pixmap.save(f"symbols/{symbol}.png")
        #     # pixmap = QPixmap()
        #     # pixmap.convertFromImage(image)
        #     widget.addItem(QIcon(pixmap), symbol)
        return widget
        


class ColourButton(QLabel):
    """ QLabel that responds to mouse clicks by emitting a `clicked` signal.
    
        Created to mimic a QPushButton that does not change style when clicked.
    """
    
    clicked = Signal(object, str)
    """ clicked = Signal(ColourButton button, str colour) 
    
        Emitted when clicked, with the reference to the button and its current colour.
    """
    
    def __init__(self, *args, colour=None, **kwargs):
        self.height = None
        super().__init__(*args, **kwargs)
        self._colour = None
        if colour is not None:
            self.setColour(colour)
            
    def mouseReleaseEvent(self, ev):
        self.clicked.emit(self, self.colour)
        
    def sizeHint(self):
        hint = super().sizeHint()
        if self.height is not None:
            return QSize(hint.width(), self.height)
        else:
            return hint
        
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
        styles = self.mainWindow.plot.getValidStyles()
        self.customStyle = StyleDesigner(styleKeys=self.mainWindow.plot.getStyleKeys(),
                                         symbolKeys=self.mainWindow.plot.getStyleSymbolKeys(),
                                         invalidNames=styles)
        self.customStyle.setEnabled(False)
        self.customStyle.saveStyle.connect(self._saveStyle)
        
        self.plotStyleList = QComboBox()
        styles = [s.capitalize() for s in styles]
        styles += ["Add custom theme..."]
        self.plotStyleList.addItems(styles)
        self.plotStyleList.currentTextChanged.connect(self._updateCustomStyleWidget)
        
        foregroundColour = self.palette().windowText().color()
        icon = makeForegroundIcon("edit", foregroundColour)
        self.editPlotStyleButton = QPushButton(icon, "")
        self.editPlotStyleButton.setCheckable(True)
        self.editPlotStyleButton.setToolTip("Edit theme")
        self.editPlotStyleButton.toggled.connect(self._editStyle)
        
        icon = makeForegroundIcon("trash", foregroundColour)
        self.deletePlotStyleButton = QPushButton(icon, "")
        self.deletePlotStyleButton.setToolTip("Delete theme")
        self.deletePlotStyleButton.clicked.connect(self._deleteTheme)
        
        self.plotStyleList.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.editPlotStyleButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.deletePlotStyleButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        
        plotStyleBox = QHBoxLayout()
        plotStyleBox.addWidget(self.plotStyleList)
        plotStyleBox.addWidget(self.editPlotStyleButton)
        plotStyleBox.addWidget(self.deletePlotStyleButton)
        
        plotStyleGroup.addLayout(plotStyleBox)
        plotStyleGroup.addWidget(self.customStyle)

        plotConfigGroup = GroupWidget("Default plot range", layout="vbox")
        
        self.plotRangeCombo = QComboBox()
        ranges = ["1 month", "3 months", "6 months", "1 year", "Current year", "All"]
        self.plotRangeCombo.addItems(ranges)
        
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
        # does setCurrentText not emit currentTextChanged signal?
        self._enableDisableDeleteButton(plotStyle)
    
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
        
    def _saveStyle(self, name, style, setStyle=False):
        self.mainWindow.plot.addCustomStyle(name, style, setStyle=setStyle)
        idx = self.plotStyleList.count()-1
        self.plotStyleList.insertItem(idx, name.capitalize())
        self.plotStyleList.setCurrentIndex(idx)
        
    def _editStyle(self, edit):
        self.customStyle.setEditMode(edit)
        self._updateCustomStyleWidget()
        
    def apply(self):
        
        styleName = self.plotStyleList.currentText().lower()
        if styleName == "add custom theme...":
            styleName, styleDct = self.customStyle.getStyle()
            self._saveStyle(styleName, styleDct, setStyle=True)
        else:
            self.mainWindow.plot.setStyle(styleName)
        
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
        self.settings.setValue("style", styleName)
        
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
            
    def _updateCustomStyleWidget(self, name=None):
        if name is None or name == "Add custom theme...":
            self.customStyle.setEnabled(True)
            if name is None:
                name = self.customStyle.name
            else:
                name = f"custom-{self.customStyle.name}"
            self.customStyle.setName(name)
        else:
            name = name.lower()
            style = self.mainWindow.plot.getStyle(name)
            self.customStyle.setStyle(style, name=name)
            self.customStyle.setEnabled(False)
            self._enableDisableDeleteButton(name)
                
    def _enableDisableDeleteButton(self, plotStyle):
        if plotStyle in self.mainWindow.plot.getDefaultStyles():
            self.deletePlotStyleButton.setEnabled(False)
            self.deletePlotStyleButton.setToolTip("Cannot delete default theme")
        else:
            self.deletePlotStyleButton.setEnabled(True)
            self.deletePlotStyleButton.setToolTip("Delete theme")
            
    def _deleteTheme(self):
        styleName = self.plotStyleList.currentText()
        items = [self.plotStyleList.itemText(idx) for idx in range(self.plotStyleList.count())]
        idx = items.index(styleName)
        self.plotStyleList.removeItem(idx)
        self.mainWindow.plot.removeCustomStyle(styleName.lower())