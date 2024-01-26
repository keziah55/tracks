"""
Plot preferences
"""

from qtpy.QtWidgets import (QCheckBox, QComboBox, QHBoxLayout, QSpinBox, 
                             QVBoxLayout, QWidget, QLineEdit, QPushButton,
                             QColorDialog, QGridLayout, QLabel, QSizePolicy)
from qtpy.QtCore import QTimer, Slot, Signal, QSize
from qtpy.QtGui import QPalette, QColor#, QPen, QBrush, QIcon, QPixmap, QImage, QPainter
# from pyqtgraph.graphicsItems.ScatterPlotItem import renderSymbol, drawSymbol
from customQObjects.widgets import GroupBox, ComboBox
from customQObjects.core import Settings
from tracks import make_foreground_icon 
from tracks.util import parse_month_range
import warnings


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
        
        self.gridLayout = QGridLayout()
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        
        self.nameEdit = QLineEdit()
        if name is not None:
            self.setName(name)
            
        foregroundColour = self.palette().windowText().color()
        icon = make_foreground_icon("accept", foregroundColour, ext="png")
        self.saveButton = QPushButton(icon, "")
        self.saveButton.setToolTip("Save theme")
        icon = make_foreground_icon("cancel", foregroundColour, ext="png")
        self.cancelButton = QPushButton(icon, "")
        self.cancelButton.setToolTip("Discard changes")
        self.saveButton.clicked.connect(self._saveStyle)
        self.cancelButton.clicked.connect(self._resetLastSaved)
        
        topLayout = QHBoxLayout()
        topLayout.addWidget(self.nameEdit)
        topLayout.addWidget(self.saveButton)
        topLayout.addWidget(self.cancelButton)
        topLayout.setContentsMargins(0, 0, 0, 0)
        
        listHeight = None
        
        self._colourButtonWidgets = {}
        self._symbolListWidgets = {}
        row = 0
        for key in styleKeys:
            if key == "highlight_point":
                label = "Highlight point"
            else:
                label = key.capitalize()
            colourName = QLabel(label)
            colourValue = ColourButton()
            self._colourButtonWidgets[key] = colourValue
            self.gridLayout.addWidget(colourName, row, 0)
            self.gridLayout.addWidget(colourValue, row, 1)
            if key in symbolKeys:
                symbolList = self._createSymbolList()
                self._symbolListWidgets[key] = symbolList
                self.gridLayout.addWidget(symbolList, row, 2)
                if listHeight is None:
                    listHeight = symbolList.sizeHint().height()
            self._colourButtonWidgets[key].clicked.connect(self.setColour)
            row += 1
            
        if listHeight is not None:
            for rowNum in range(self.gridLayout.rowCount()):
                item = self.gridLayout.itemAtPosition(rowNum, 1)
                item.widget().height = listHeight
                item.widget().width = 2*listHeight
            
        layout = QVBoxLayout()
        layout.addLayout(topLayout)
        layout.addLayout(self.gridLayout)
        
        self.setLayout(layout)
        
        self.setEditMode(False)
        
        if style is not None:
            self.setStyle(style)
        self._lastSavedName, self._lastSavedStyle = self.getStyle()
        
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
        
    def setStyle(self, style, name=None, setAsPrevious=False):
        """ Set colours and symbols from `style` dict and optionally style `name`. 
        
            If `setAsPrevious` is True, the given style (and name, if applicable)
            will be saved as the internal 'last style' (used when discarding changes).
            You may want to use this if you are setting the initial style by 
            calling this method, rather than by passing the style to the constructor.
        """
        for key, value in style.items():
            # two possible `style` dict strutures, due to my own stupidity
            # easiest to support both here
            # first get colour and/or symbol from dict item
            c, s = None, None
            if isinstance(value, dict):
                c = value['colour']
                s = value.get('symbol', None)
            elif QColor.isValidColor(value):
                c = value
            elif value in self.symbols:
                s = value
                key = key.removesuffix("Symbol")
            # apply colour and/or symbol value
            if c is not None:
                widget = self._colourButtonWidgets[key]
                widget.setColour(c)
            if s is not None:
                widget = self._symbolListWidgets[key]
                widget.setCurrentText(self.symbols[s].capitalize())
                
        if name is not None:
            self.setName(name)
        if setAsPrevious:
            self._lastSavedName, self._lastSavedStyle = self.getStyle()
            
    def getStyle(self):
        style = {}
        for row in range(self.gridLayout.rowCount()):
            key = self.gridLayout.itemAtPosition(row, 0).widget().text().lower()
            colour = self.gridLayout.itemAtPosition(row, 1).widget().colour
            
            # turn 'highlight point' back into 'highlight_point'
            key = key.replace(" ", "_")
            style[key] = {"colour": colour}
            
            symbol = self.gridLayout.itemAtPosition(row, 2)
            if symbol is not None:
                symbol = symbol.widget().currentText().lower()
                style[key]["symbol"] = self.reverseSymbolDict[symbol]
        return self.name, style
    
    def _saveStyle(self):
        self._lastSavedName, self._lastSavedStyle = self.getStyle()
        self.saveStyle.emit(self._lastSavedName, self._lastSavedStyle)
        self.setEditMode(False)
        
    def _resetLastSaved(self):
        self.setStyle(self._lastSavedStyle, self._lastSavedName)
        
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
            self.cancelButton.setEnabled(True)
        else:
            self.cancelButton.setEnabled(False)
            
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
        self.width = None
        super().__init__(*args, **kwargs)
        self._colour = None
        if colour is not None:
            self.setColour(colour)
            
    def mouseReleaseEvent(self, ev):
        self.clicked.emit(self, self.colour)
        
    def sizeHint(self):
        hint = super().sizeHint()
        height = self.height if self.height is not None else hint.height()
        width = self.width if self.width is not None else hint.width()
        return QSize(width, height)
        # if self.height is not None:
        #     return QSize(hint.width(), self.height)
        # else:
        #     return hint
        
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
    
    name = "Plot"
    
    def __init__(self, mainWindow):
        super().__init__()
        self.mainWindow = mainWindow
        
        plotStyleGroup = GroupBox("Plot style")
        styles = self.mainWindow.plot.get_valid_styles()
        self.customStyle = StyleDesigner(styleKeys=self.mainWindow.plot.get_style_keys(),
                                         symbolKeys=self.mainWindow.plot.get_style_symbol_keys(),
                                         invalidNames=styles)
        self.customStyle.setEnabled(False)
        self.customStyle.saveStyle.connect(self._saveStyle)
        
        self.plotStyleList = ComboBox()
        styles = [s.capitalize() for s in styles]
        self.plotStyleList.addItems(styles)
        self.plotStyleList.currentTextChanged.connect(self._updateCustomStyleWidget)
        
        foregroundColour = self.palette().windowText().color()
        
        icon = make_foreground_icon("add", foregroundColour, ext="png")
        self.addPlotStyleButton = QPushButton(icon, "")
        self.addPlotStyleButton.setCheckable(True)
        self.addPlotStyleButton.setToolTip("Add theme")
        self.addPlotStyleButton.toggled.connect(self._addStyle)
        
        icon = make_foreground_icon("edit", foregroundColour)
        self.editPlotStyleButton = QPushButton(icon, "")
        self.editPlotStyleButton.setCheckable(True)
        self.editPlotStyleButton.setToolTip("Edit theme")
        self.editPlotStyleButton.toggled.connect(self._editStyle)
        
        icon = make_foreground_icon("trash", foregroundColour)
        self.deletePlotStyleButton = QPushButton(icon, "")
        self.deletePlotStyleButton.setToolTip("Delete theme")
        self.deletePlotStyleButton.clicked.connect(self._deleteTheme)
        
        self.plotStyleList.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.editPlotStyleButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.deletePlotStyleButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        
        plotStyleBox = QHBoxLayout()
        plotStyleBox.addWidget(self.plotStyleList)
        plotStyleBox.addWidget(self.addPlotStyleButton)
        plotStyleBox.addWidget(self.editPlotStyleButton)
        plotStyleBox.addWidget(self.deletePlotStyleButton)
        
        plotStyleGroup.addLayout(plotStyleBox)
        plotStyleGroup.addWidget(self.customStyle)

        plotConfigGroup = GroupBox("Default plot range", layout="vbox")
        
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
        
    def setCurrentValues(self):
        """ Set widget values from `settings` """
        self.settings = Settings()
        self.settings.beginGroup("plot")

        plotStyle = self.settings.value("style", "dark")
        self.plotStyleList.setCurrentText(plotStyle.capitalize())
        # does setCurrentText not emit currentTextChanged signal?
        self._enableDisableDeleteButton(plotStyle)
        
        current_plot_style = self.mainWindow.plot.get_style(plotStyle)
        from pprint import pprint; pprint(current_plot_style)
    
        # self.customStyle.setName(plotStyle)
        self.customStyle.setStyle(self.mainWindow.plot.get_style(plotStyle), 
                                  name=plotStyle, setAsPrevious=True)
        
        self._setMonthRange()
        
        self.settings.endGroup()
        
    def _setMonthRange(self):
        """
        Read month range from settings and set widget values
        
        NB this method assumes that `settings` is in the 'plot' group.
        """
        customRange = self.settings.value("customRange", False)
        rng = self.settings.value("range", "All")
        
        self.setCustomRange(customRange)
        if customRange:
            monthRange = parse_month_range(rng)
            if monthRange is None:
                # custom month range cannot be parsed
                # set customRange to False and call this method again
                warnings.warn(f"Could not get custom number of months from '{rng}'")
                self.settings.setValue("customRange", False)
                self._setMonthRange()
            else:
                self.customRangeSpinBox.setValue(monthRange)
        else:
            items = [self.plotRangeCombo.itemText(idx) for idx in range(self.plotRangeCombo.count())]
            idx = items.index(rng)
            self.plotRangeCombo.setCurrentIndex(idx)
        
    def _saveStyle(self, name, style, setStyle=True):
        self.mainWindow.plot.add_custom_style(name.lower(), style, set_style=setStyle)
        if name.capitalize() not in self.plotStyleList.items:
            idx = self.plotStyleList.count()-1
            self.plotStyleList.insertItem(idx, name.capitalize())
            self.plotStyleList.setCurrentIndex(idx)
        self.addPlotStyleButton.setChecked(False)
        self.editPlotStyleButton.setChecked(False)
        self.customStyle.setEnabled(False)
        
    def _editStyle(self, edit):
        self.customStyle.setEditMode(edit)
        if edit:
            self.customStyle.setName(self.plotStyleList.currentText())
            self._updateCustomStyleWidget()
        else:
            # TODO call _saveStyle here?
            self.customStyle.setEnabled(False)  
        
    def apply(self):
        
        if self.addPlotStyleButton.isChecked() or self.editPlotStyleButton.isChecked():
            styleName, styleDct = self.customStyle.getStyle()
            self._saveStyle(styleName, styleDct, setStyle=True)
        else:
            styleName = self.plotStyleList.currentText().lower()
            self.mainWindow.plot.set_style(styleName)
        
        customRange = self.customRangeCheckBox.isChecked()
        if customRange:
            months = self.customRangeSpinBox.value()
        else:
            text = self.plotRangeCombo.currentText()
            months = parse_month_range(text)
        self.mainWindow.plot.set_x_axis_range(months)
        
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
            
    def _addStyle(self):
        self.customStyle.setEnabled(True)
        styleNames = [self.plotStyleList.itemText(idx).lower() 
                      for idx in range(self.plotStyleList.count())]
        name = f"custom-{self.customStyle.name}"
        while name.lower() in styleNames:
            name = f"custom-{name}"
        self.customStyle.setName(name)
            
    def _updateCustomStyleWidget(self, name=None):
        if name is None:
            self.customStyle.setEnabled(True)
            name = self.customStyle.name
            self.customStyle.setName(name)
        else:
            name = name.lower()
            style = self.mainWindow.plot.get_style(name)
            self.customStyle.setStyle(style, name=name)
            self.customStyle.setEnabled(False)
            self._enableDisableDeleteButton(name)
                
    def _enableDisableDeleteButton(self, plotStyle):
        if plotStyle in self.mainWindow.plot.get_default_styles():
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
        self.mainWindow.plot.remove_custom_style(styleName.lower())