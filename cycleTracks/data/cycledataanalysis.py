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
        
