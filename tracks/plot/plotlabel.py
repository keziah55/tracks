"""
QWidget containing QLabels for each data series in the PlotWidget.
"""

from qtpy.QtWidgets import QLabel, QHBoxLayout, QWidget
from qtpy.QtCore import Signal
from qtpy.QtCore import Qt


class ClickableLabel(QLabel):
    """QLabel that emits `clicked` signal.

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
        """Set label text. Automatically apply style."""
        fontSize = f"font-size: {self.fontSize}pt"
        if self.colour is not None:
            style = f"'{fontSize}; color: {self.colour}'"
        else:
            style = f"'{fontSize}'"
        html = f"<div style={style}>{text}</div>"
        super().setText(html)


class PlotLabel(QWidget):
    labelClicked = Signal(str)
    """ **signal** labelClicked(str `name`) 
    
        Emitted when a label is clicked.
    """

    def __init__(self, activity, style, fontSize=12):
        super().__init__()

        self._activity = activity
        self._style = style

        layout = QHBoxLayout()

        self._widgets = {}

        self._names = list(self._activity.filter_measures("plottable", lambda b: b))
        self._names.insert(0, "date")

        for key in self._names:
            # make ClickableLabel with given size
            colour = self._style[key]["colour"] if key in self._style.keys else None
            widget = ClickableLabel(key, colour=colour, fontSize=fontSize)
            widget.setAlignment(Qt.AlignCenter)
            # connect to labelClicked signal
            widget.clicked.connect(self.labelClicked)
            # add to dict and layout
            self._widgets[key] = widget
            layout.addWidget(widget)

        self.setLayout(layout)

    def set_labels(self, series_dct):
        """For given `series_dct` set label text."""
        for key, data in series_dct.items():
            if key in self._names:
                measure = self._activity.get_measure(key)
                text = ""
                kwargs = {"include_unit": True}
                if key == "date":
                    kwargs["date_fmt"] = "%a %d %b %Y"
                else:
                    text = f"{measure.name}: "

                text += measure.formatted(data, **kwargs)
                label = self._widgets[key]
                label.setText(text)

    def set_style(self, style):
        self._style = style
        for key, widget in self._widgets.items():
            colour = self._style[key]["colour"] if key in self._style.keys else None
            widget.colour = colour
