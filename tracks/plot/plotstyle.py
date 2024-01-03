#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Class to manage reading/writing plotStyle.ini
"""

from pathlib import Path
from customQObjects.core import Settings

class PlotStyle:
    """ 
    Class to manage plot styles. 
    
    Does not store the style directly, but gets (and sets) from a 
    Settings object, which manages the plotStyles.ini file.
    
    The default styles "dark" and "light" will be written to the file in 
    the constructor, if they do not exist in the file.
    """
    
    defaultStyles = ["dark", "light"]
    
    def __init__(self, activity, style="dark"):
        
        plotStyleFile = Path(Settings().fileName()).parent.joinpath('plotStyles.ini')
        self.settings = Settings(str(plotStyleFile), Settings.NativeFormat)
        
        self.symbolKeys = list(activity.filter_measures("plottable", lambda b: b))
        self.keys = self.symbolKeys + ['odometer', 'highlightPoint', 'foreground', 'background']
        
        # default colours for series
        default_colours = {
            "dark":# green,  red,       blue,      orange,    pink,      cyan,      brown,     purple
                ["#19b536", "#cf0202", "#024aeb", "#ff9100", "#ff2be3", "#2aa0a6", "#6f420a", "#8b3bcc"],
            "light":# green, red,       blue,      orange,    pink,      cyan,      brown,     purple
                ["#2bb512", "#d80d0d", "#0981cb", "#ff9100", "#c621b3", "#007069", "#442806", "#4a1f6c"]
        }
        if len(self.symbolKeys) > len(default_colours["dark"]):
            # repeat colour list, if necessary
            repeat, mod = divmod(len(default_colours["dark"]), len(self.symbolKeys))
            dark_default = default_colours["dark"] * repeat + default_colours["dark"][:mod]
            light_default = default_colours["light"] * repeat + default_colours["light"][:mod]
        else:
            dark_default = default_colours["dark"][:len(self.symbolKeys)]
            light_default = default_colours["light"][:len(self.symbolKeys)]
        
        # append default colours for odometer etc
        dark_default += ["#4d4d4d", "#faed00", "#969696", "#000000"]
        light_default = [ "#9f9f9f", "#deb009", "#4d4d4d", "#ffffff"]
        defaults = {'dark':dict(zip(self.keys, dark_default)),
                    'light':dict(zip(self.keys, light_default))}
        defaultSymbols = {key:'x' for key in self.symbolKeys}
        
        for styleName, styleDct in defaults.items():
            if styleName not in self.settings.childGroups():
                self.settings.beginGroup(styleName)
                for key, colour in styleDct.items():
                    self.settings.setValue(key, colour)
                for key, symbol in defaultSymbols.items():
                    self.settings.setValue(f"{key}Symbol", symbol)
                self.settings.endGroup()
        
        self.name = style
        
    @property
    def name(self):
        return self._styleName

    @name.setter 
    def name(self, name):
        if name.lower() not in self.validStyles:
            msg = f"Plot style must be one of {', '.join(self.validStyles)}, not '{name}'."
            raise ValueError(msg)
        self._styleName = name.lower()
        
    @property 
    def validStyles(self):
        return self.settings.childGroups()
        
    def __getattr__(self, name):
        if name in self.keys:
            return self._getStyle(name)
        else:
            return self.__getattribute__(name)
        
    def __getitem__(self, name):
        if name in self.keys: 
            return self._getStyle(name)
        else:
            raise KeyError(f"PlotStyle has no field '{name}'")
            
    def _getStyle(self, field):
        if field in ['foreground', 'background']:
            return self.settings.value(f"{self.name}/{field}")
        
        dct = {'colour':self.settings.value(f"{self.name}/{field}")}
        symbol = self.settings.value(f"{self.name}/{field}Symbol")
        if symbol is not None:
            dct['symbol'] = symbol
        return dct
    
    def getStyleDict(self, name=None):
        if name is None:
            name = self.name
        style = {}
        for field in self.keys:
            dct = {'colour':self.settings.value(f"{name}/{field}")}
            symbol = self.settings.value(f"{name}/{field}Symbol")
            if symbol is not None:
                dct['symbol'] = symbol
            style[field] = dct
        return style
    
    def addStyle(self, name, style):
        self.settings.beginGroup(name)
        for key, value in style.items():
            self.settings.setValue(key, value)
        self.settings.endGroup()
    
    def removeStyle(self, name):
        self.settings.remove(name)