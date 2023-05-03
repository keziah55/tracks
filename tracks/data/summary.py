"""
A couple of the objects that show that data need to summarise multiple sessions.

The `Summary` object stores the functions used to summarise each category.
"""

from qtpy.QtCore import QObject, Signal
import numpy as np

class Summary(QObject):
    """ Data class to store the functions that should be used to summarise the categories. """
    valueChanged = Signal()
    
    funcs = {'sum':sum, 'min':min, 'max':max, 'mean':np.mean}
    names = {'time':'Time (hours)', 'distance':'Distance (km)',
             'speed':'Speed (km/h)', 'calories':'Calories', 'gear':'Gear'}
    
    def __init__(self, time='sum', distance='sum', speed='max', calories='sum', gear='mean'):
        super().__init__()
        self.time = time
        self.distance = distance
        self.speed = speed
        self.calories = calories
        self.gear = gear
        
    def __setattr__(self, name, value):
        if name in self.names and value not in self.funcs:
            raise ValueError(f"Invalid function name {repr(value)}")
        super().__setattr__(name, value)
        if name in self.names:
            self.valueChanged.emit()
        
    @property    
    def summaryArgs(self):
        """ Get dict of args to `Data.summaryString`. """
        args = []
        for name, arg0 in self.names.items():
            func = getattr(self, name)
            arg1 = self.funcs[func]
            args.append((arg0, arg1))
        return args
        
    def getFunc(self, name):
        return getattr(self, name)
    
    def setFunc(self, *args):
        """ Set the function name for a give summary field. """
        changed = False
        if len(args) == 1 and isinstance(args[0], dict):
            _changed = []
            for name, funcName in args[0].items():
                c = self._setFunc(name, funcName)
                _changed.append(c)
            changed = any(_changed)
        elif len(args) == 2:
            changed = self._setFunc(*args)
        if changed:
            self.valueChanged.emit() # only emit once
            
    def _setFunc(self, name, funcName):
        changed = False
        if getattr(self, name) != funcName:
            self.__setattr__(name, funcName)
            changed = True
        return changed