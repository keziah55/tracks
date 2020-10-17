#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subclass of pyqtgraph.PlotWidget.
"""

from datetime import datetime
from pyqtgraph import PlotWidget, DateAxisItem

class CyclePlotWidget(PlotWidget):
    def __init__(self, df, style={}):
        super().__init__(axisItems={'bottom': DateAxisItem()})
        
        self.df = df
        
        date = [datetime.strptime(d, "%Y-%m-%d").timestamp() for d in self.df['Date']]
        self.plotItem.plot(date, self.df['Distance (km)'])
        
        
    def _makeSymbol(self):
        pass