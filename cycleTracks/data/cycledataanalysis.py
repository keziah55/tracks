#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Object to provide analysis of CycleData.
"""

from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot
from . import CycleData
import numpy as np

class CycleDataAnalysis:
    
    newBestSession = Signal(str, int, str)
    """ **signal** newBestSession(str `key`, int `idx`, str `value`)
    
        Signal emitted when there is a new top 5 session.
    """
    
    def __init__(self, data):
        self.data = data
        
    def analyseMonthlyAvgSpeed(self):
        months = self.data.splitMonths()
        
        # monthData = []
        monthStats = []
        
        for dateStr, dataFrame in months:
            # monthData.append((dateStr, CycleData(dataFrame)))
            
            data = CycleData(dataFrame)
            dct = {'min':np.min(data.avgSpeed), 'max':np.max(data.avgSpeed),
                   'mean':np.mean(data.avgSpeed), 'std':np.std(data.avgSpeed),
                   'median':np.median(data.avgSpeed), 'data':data.avgSpeed}
            monthStats.append((dateStr, dct))
            
        return monthStats