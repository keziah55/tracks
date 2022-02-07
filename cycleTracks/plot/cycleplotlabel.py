"""
QWidget containing QLabels for each data series in the CyclePlotWidget.
"""

from qtpy.QtWidgets import QLabel, QHBoxLayout, QWidget
from qtpy.QtCore import Signal
from qtpy.QtCore import Qt

class ClickableLabel(QLabel):
    """ QLabel that emits `clicked` signal. 
    
        Parameters
        ----------
        name : str
            Identifying string to emit with `clicked` signal.
        text : str, optional
            Text to display in label.
        colour : {str, QColor}, optional
            Colour to display text in.
        fontSize : int
            Font size for label text. Default is 12.
    """
    
    clicked = Signal(str)
    """ **signal** clicked(str `name`) 
    
        Emitted when label clicked, with given name.
    """
    
    def __init__(self, name, text="", colour=None, fontSize=12):
        super().__init__()
        self.name = name
        self.colour = colour
        self.fontSize = fontSize
        if text is not None:
            self.setText(text)
    
    def mouseReleaseEvent(self, event):
        self.clicked.emit(self.name)
        super().mouseReleaseEvent(event)
        
    def setText(self, text):
        """ Set label text. Automatically apply style. """
        fontSize = f"font-size: {self.fontSize}pt"
        if self.colour is not None:
            style = f"'{fontSize}; color: {self.colour}'"
        else:
            style = f"'{fontSize}'"
        html = f"<div style={style}>{text}</div>"
        super().setText(html)


class CyclePlotLabel(QWidget):
    
    labelClicked = Signal(str)
    """ **signal** labelClicked(str `name`) 
    
        Emitted when a label is clicked.
    """
    
    def __init__(self, style, fontSize=12):
        
        super().__init__()
        
        self.style = style
        
        self.layout = QHBoxLayout()
        
        self.data = {}
        self.data['date'] = {'string':"{}"}
        self.data['speed'] = {'string':"Avg. speed: {:.3f} km/h"}
        self.data['distance'] = {'string':"Distance: {} km"}
        self.data['calories'] = {'string':"Calories: {}"}
        self.data['time'] = {'string':"Time: {}"}
        
        for key in self.data:
            # make ClickableLabel with given size
            colour = self.style[key]['colour'] if key in self.style.keys else None
            widget = ClickableLabel(key, colour=colour, fontSize=fontSize)
            widget.setAlignment(Qt.AlignCenter)
            # connect to labelClicked signal
            widget.clicked.connect(self.labelClicked)
            # add to dict and layout
            self.data[key]['widget'] = widget
            self.layout.addWidget(widget)
            
        self.setLayout(self.layout)
            
    def setLabels(self, dct):
        """ For given `dct` set label text. """
        for key, data in dct.items():
            if key in self.data.keys():
                text = self.data[key]['string'].format(data)
                label = self.data[key]['widget']
                label.setText(text)

    def setStyle(self, style):
        self.style = style
        for key, value in self.data.items():
            colour = self.style[key]['colour'] if key in self.style.keys else None
            value['widget'].colour = colour