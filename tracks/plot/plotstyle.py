#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Class to manage reading/writing plot_styles.json
"""

import json
from tracks import get_data_path

class PlotStyle:
    """ 
    Class to manage plot styles. 
    
    Does not store the style directly, but gets (and sets) from a 
    Settings object, which manages the plotStyles.ini file.
    
    The default styles "dark" and "light" will be written to the file in 
    the constructor, if they do not exist in the file.
    """
    
    default_styles = ["dark", "light"]
    
    def __init__(self, activity, style="dark"):
        
        self._activity_name = activity.name
        
        # TODO better way of doing this?
        self.symbol_keys = list(activity.filter_measures("plottable", lambda b: b))
        self.other_keys = ['odometer', 'highlight_point', 'foreground', 'background']
        self.keys = self.symbol_keys + self.other_keys
        
        # read styles from json
        # if there's no style for this activity, make defaults
        all_styles = self._get_all_styles()
        self._style_dict = all_styles.get(activity.name, None)
        
        if self._style_dict is None:
            self._style_dict = self._make_defaults(activity.name)   
            all_styles[self._activity_name] = self._style_dict
            # update json file
            self._write_style_file(all_styles)
        
        self.name = style
        
    @property
    def _plot_style_file(self):
        return get_data_path().joinpath("plot_styles.json")
        
    @property
    def name(self):
        return self._style_name

    @name.setter 
    def name(self, name):
        if name.lower() not in self.valid_styles:
            msg = f"Plot style must be one of {', '.join(self.valid_styles)}, not '{name}'."
            raise ValueError(msg)
        self._style_name = name.lower()
        
    @property 
    def valid_styles(self):
        return list(self._style_dict.keys())
        
    def __getattr__(self, name):
        if name in self.keys:
            return self._get_style(name)
        else:
            return self.__getattribute__(name)
        
    def __getitem__(self, name):
        if name in self.keys: 
            return self._get_style(name)
        else:
            raise KeyError(f"PlotStyle has no field '{name}'")
            
    def _get_style(self, field):
        return self._style_dict[self.name][field]
    
    def get_style_dict(self, name=None):
        if name is None:
            name = self.name
        return self._style_dict[name]
    
    def add_style(self, name, style):
        self._style_dict[name] = style
        self._write_style_file()
        
    def remove_style(self, name):
        self._style_dict.pop(name)
        self._write_style_file()
        
    def _get_all_styles(self):
        if not self._plot_style_file.exists():
            all_styles = {}
        else:
            with open(self._plot_style_file, "r") as fileobj:
                all_styles = json.load(fileobj)
        return all_styles
        
    def _make_defaults(self, activity_name):
        # default colours for series
        default_colours = {
            "dark":# green,  red,       blue,      orange,    pink,      cyan,      brown,     purple
                ["#19b536", "#cf0202", "#024aeb", "#ff9100", "#ff2be3", "#2aa0a6", "#6f420a", "#8b3bcc"],
            "light":# green, red,       blue,      orange,    pink,      cyan,      brown,     purple
                ["#2bb512", "#d80d0d", "#0981cb", "#ff9100", "#c621b3", "#007069", "#442806", "#4a1f6c"]
        }
        if len(self.symbol_keys) > len(default_colours["dark"]):
            # repeat colour list, if necessary
            repeat, mod = divmod(len(default_colours["dark"]), len(self.symbol_keys))
            series_dark_default = default_colours["dark"] * repeat + default_colours["dark"][:mod]
            series_light_default = default_colours["light"] * repeat + default_colours["light"][:mod]
        else:
            series_dark_default = default_colours["dark"][:len(self.symbol_keys)]
            series_light_default = default_colours["light"][:len(self.symbol_keys)]
            
        other_dark_default = ["#4d4d4d", "#faed00", "#969696", "#000000"]
        other_light_default = [ "#9f9f9f", "#deb009", "#4d4d4d", "#ffffff"]
        
        all_defaults = {
            "dark": (series_dark_default, other_dark_default), 
            "light": (series_light_default, other_light_default)
        }
        
        default_symbol = "x"
        defaults = {}
        for name, (series_colour_list, other_colour_list) in all_defaults.items():
            d = {}
            c_list = iter(series_colour_list)
            for key in self.symbol_keys:
                d[key] = {"colour":next(c_list), "symbol":default_symbol}
            c_list = iter(other_colour_list)
            for key in self.other_keys:
                d[key] = {"colour":next(c_list)}
            defaults[name] = d
            
        return defaults
        
    def _write_style_file(self, all_styles=None):
        if all_styles is None:
            all_styles = self._get_all_styles()
            all_styles[self._activity_name] = self._style_dict
        
        with open(self._plot_style_file, 'w') as f:
            json.dump(all_styles, f, indent=4)
