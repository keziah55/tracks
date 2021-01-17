#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main window for cycleTracks.
"""

import sys
import os
from PyQt5.QtWidgets import (QDesktopWidget, QMainWindow, QApplication, 
                             QHBoxLayout, QWidget)
import pandas as pd
from cycleplotwidget import CyclePlotWidget
from cycledataviewer import CycleDataViewer

    
class CycleTracks(QMainWindow):
    def __init__(self):
        super().__init__()
        
        home = os.path.expanduser('~')
        path = os.path.join(home, '.cycletracks')
        os.makedirs(path, exist_ok=True)
        self.file = os.path.join(path, 'cycletracks.csv')
        self.sep = ','
        if not os.path.exists(self.file):
            header = ['Date', 'Time', 'Distance (km)', 'Calories', 'Gear']
            s = self.sep.join(header)
            with open(self.file, 'w') as fileobj:
                fileobj.write(s+'\n')
                
        self.df = pd.read_csv(self.file, sep=self.sep, parse_dates=['Date'])
        self._backup() # TODO call this after every save (or change?)

        self.layout = QHBoxLayout()
        
        self.data = CycleDataViewer(self.df)
        self.plot = CyclePlotWidget(self.df)
        
        self.layout.addWidget(self.data)
        self.layout.addWidget(self.plot)
        
        self.mainWidget = QWidget()
        self.mainWidget.setLayout(self.layout)
        self.setCentralWidget(self.mainWidget)
        
        self.setWindowTitle('CycleTrack')
        # self.resize(1000, 800)
        # self._centre()
        self.showMaximized()
        self.show()
        
        
    def _centre(self):
        """ Centre window on screen. """
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
        
    def _backup(self):
        bak = self.file + '.bak'
        self.df.to_csv(bak, sep=self.sep)
            
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CycleTracks()
    sys.exit(app.exec_())
    