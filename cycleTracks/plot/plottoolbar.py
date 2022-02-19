from qtpy.QtWidgets import QToolBar
from qtpy.QtCore import Qt, Signal
from cycleTracks import makeForegroundIcon
from pyqtgraph import getConfigOption, mkColor

class PlotToolBar(QToolBar):
    
    # signals emitted when buttons clicked
    viewAllClicked = Signal()
    viewRangeClicked = Signal()
    highlightPBClicked = Signal(bool)
    
    def __init__(self):
        super().__init__()
        
        self.setOrientation(Qt.Vertical)
        
        rangeButtons = {"view_all":("View all points", self.viewAllClicked), 
                        "view_range":("View custom range", self.viewRangeClicked)}
        for name, params in rangeButtons.items():
            tooltip, signal = params
            icon = self._getIcon(name)
            action = self.addAction(icon, "", signal.emit)
            action.setToolTip(tooltip)
        self.addSeparator()
        
        icon = self._getIcon("pb")
        action = self.addAction(icon, "")
        action.setToolTip("Highlight every point that was a PB.")
        action.setCheckable(True)
        action.triggered.connect(self.highlightPBClicked.emit)
        
    def _getIcon(self, name):
        foregroundColour = mkColor(getConfigOption('foreground'))
        icon = makeForegroundIcon(name, foregroundColour, ext="png", returnType="icon")
        return icon