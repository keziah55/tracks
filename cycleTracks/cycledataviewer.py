#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Read-only QTextEdit showing data from cycling DataFrame.
"""
from PyQt5.QtWidgets import (QDesktopWidget, QMainWindow, QApplication, 
                             QHBoxLayout, QWidget, QTextEdit)

class CycleDataViewer(QTextEdit):
    
    def __init__(self, df):
        super().__init__()
        
        self.setReadOnly(True)