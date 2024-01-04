from qtpy.QtWidgets import QToolBar, QApplication
from qtpy.QtGui import QPalette
from qtpy.QtCore import Qt, Signal
from tracks import make_foreground_icon

class PlotToolBar(QToolBar):
    """ Vertical tool bar with buttons to control the plot. """
    
    # signals emitted when buttons clicked
    viewAllClicked = Signal()
    viewRangeClicked = Signal()
    highlightPBClicked = Signal(bool)
    
    def __init__(self):
        super().__init__()
        
        self.setOrientation(Qt.Vertical)
        
        # get foreground colour for buttons
        palette = QApplication.style().standardPalette()
        colour = palette.color(QPalette.WindowText)
        
        rangeButtons = {"view_all":("View all points", self.viewAllClicked), 
                        "view_range":("View custom range", self.viewRangeClicked)}
        for name, params in rangeButtons.items():
            tooltip, signal = params
            icon = make_foreground_icon(name, colour, ext="png")
            action = self.addAction(icon, "", signal.emit)
            action.setToolTip(tooltip)
        self.addSeparator()
        
        icon = make_foreground_icon("pb", colour, ext="png")
        action = self.addAction(icon, "")
        action.setToolTip("Highlight every point that was a PB")
        action.setCheckable(True)
        action.triggered.connect(self.highlightPBClicked.emit)
