#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subclass of pyqtgraph.PlotWidget.
"""

from datetime import datetime
from pyqtgraph import PlotWidget, DateAxisItem

class CyclePlotWidget(PlotWidget):
    def __init__(self, df, *args, **kwargs):
        key = 'axisItems'
        axisDict = {'bottom': DateAxisItem()}
        if key in kwargs.keys():
            kwargs[key].update(axisDict)
        else:
            kwargs[key] = axisDict
            
        super().__init__(*args, **kwargs)
        
        self.df = df
        
        date = [datetime.strptime(d, "%Y-%m-%d").timestamp() for d in self.df['Date']]
        self.plotItem.plot(date, self.df['Distance (km)'])
        