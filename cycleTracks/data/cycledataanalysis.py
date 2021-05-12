#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Object to provide analysis of CycleData.
"""

from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot

class CycleDataAnalysis:
    
    newBestSession = Signal(str, int, str)
    """ **signal** newBestSession(str `key`, int `idx`, str `value`)
    
        Signal emitted when there is a new top 5 session.
    """
    
    def __init__(self, data):
        self.data = data
        
        self.keys = ['Date', 'Time', 'Distance (km)', 'Avg. speed (km/h)', 
                     'Calories', 'Gear']
        
        self.bestSessionKey = "Avg. speed (km/h)"
        self.pb = self.getBestSessions()
        
    def getBestSessions(self, n=5, key="Avg. speed (km/h)", order='descending'):
        if order == 'descending':
            n *= -1
        if key == 'Time':
            series = self.data.timeHours
        else:
            series = self.data[key]
        pb = []
        indices = series.argsort()[n:][::-1]
        for idx in indices:
            row = {}
            for key in self.keys:
                value = self.data.formatted(key)[idx]
                row[key] = value
            row['datetime'] = self.data['Date'][idx]
            pb.append(row)
        return pb
    
    @Slot()
    def newData(self):
        pass
    
    def _newBestSessions(self):
        # news PBs
        pb = self.getBestSessions()
        newDates = [row['Date'] for row in pb]
        dates = [row['Date'] for row in self.pb]
        
        if newDates != dates:
            i = 0
            while newDates[i] == dates[i]:
                i += 1
            # self.newPBdialog.setMessage(self.bestSessionKey, i, pb[i][self.bestSessionKey])
            # self.newPBdialog.exec_()
            # self.makeTable(key=self.bestSessionKey)
            
            self.pb = self.getBestSessions()
            
            return self.bestSessionKey, i, pb[i][self.bestSessionKey]
        else:
            return None