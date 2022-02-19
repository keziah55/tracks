from qtpy.QtWidgets import QToolBar
from qtpy.QtCore import Qt, Signal
from cycleTracks import makeForegroundIcon

class PlotToolBar(QToolBar):
    """ Vertical tool bar with buttons to control the plot. """
    
    # signals emitted when buttons clicked
    viewAllClicked = Signal()
    viewRangeClicked = Signal()
    highlightPBClicked = Signal(bool)
    
    def __init__(self):
        super().__init__()
        
        self.setOrientation(Qt.Vertical)
        
        # TODO colour we want here really depends on the overall style
        # maybe add a user-override option in preferences?
        # could just add it in the plot style menu, as it is part of the plot
        # 'toolbar foreground'?
        colour = "#ffffff"
        
        rangeButtons = {"view_all":("View all points", self.viewAllClicked), 
                        "view_range":("View custom range", self.viewRangeClicked)}
        for name, params in rangeButtons.items():
            tooltip, signal = params
            icon = makeForegroundIcon(name, colour, ext="png")
            action = self.addAction(icon, "", signal.emit)
            action.setToolTip(tooltip)
        self.addSeparator()
        
        icon = makeForegroundIcon(name, colour, ext="png")
        action = self.addAction(icon, "")
        action.setToolTip("Highlight every point that was a PB")
        action.setCheckable(True)
        action.triggered.connect(self.highlightPBClicked.emit)
