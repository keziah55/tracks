"""
A couple of the objects that show that data need to summarise multiple sessions.

The `Summary` object stores the functions used to summarise each category.
"""

from dataclasses import dataclass
from PyQt5.QtCore import QObject, pyqtSignal as Signal
import numpy as np

@dataclass
class SummaryData:
    """ Data class to store the functions that should be used to summarise the categories. """
    time: str = 'sum'
    distance: str = 'sum'
    speed: str = 'max'
    calories: str = 'sum'
    gear: str = 'mean'
    
    funcs = {'sum':sum, 'min':min, 'max':max, 'mean':np.mean}
    names = {'time':'Time (hours)', 'distance':'Distance (km)',
             'speed':'Avg. speed (km/h)', 'calories':'Calories', 'gear':'Gear'}
    
    def __setattr__(self, name, value):
        if name in self.names and value not in self.funcs:
            raise ValueError(f"Invalid function name {repr(value)}")
        super().__setattr__(name, value)
        
    @property    
    def summaryArgs(self):
        """ Get dict of args to `CycleData.summaryString`. """
        args = []
        for name, arg0 in self.names.items():
            func = getattr(self, name)
            arg1 = self.funcs[func]
            args.append((arg0, arg1))
        return args
    
    
class Summary(QObject):
    """ Wrap `SummaryData` object so it can emit `valueChanged` signal. """
    valueChanged = Signal()
    
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.summary = SummaryData(*args, **kwargs)
        
    def __setattr__(self, name, value):
        if name == "summary":
            super().__setattr__(name, value)
        else:
            self.summary.__setattr__(name, value)
            if name in self.summary.names:
                self.valueChanged.emit()
            
    def __getattr__(self, name):
        if name == "summary":
            return self.summary
        else:
            return getattr(self.summary, name)
        
    def getFunc(self, name):
        return getattr(self.summary, name)
    
    def setFunc(self, *args):
        if len(args) == 1 and isinstance(args, dict):
            for name, funcName in args.items():
                self.summary.__setattr__(name, funcName)
        elif len(args) == 2:
            self.summary.__setattr__(*args)
        self.valueChanged.emit() # only emit once