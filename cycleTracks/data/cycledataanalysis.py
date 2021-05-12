#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 12 18:08:48 2021

@author: keziah
"""

import re

class CycleDataAnalysis:
    
    def __init__(self, parent):
        self.parent = parent
        
    @property
    def data(self):
        return self.parent.data
    
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
            for key in self.headerLabels:
                key = re.sub(r"\s", " ", key) # remove \n from avg speed
                value = self.data.formatted(key)[idx]
                row[key] = value
            row['datetime'] = self.data['Date'][idx]
            pb.append(row)
        return pb