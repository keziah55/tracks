#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main window for cycleTracks.
"""

import sys
import os

from datetime import datetime
from pyqtgraph import PlotWidget, DateAxisItem

from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtWidgets import (QAction, QDesktopWidget, QMainWindow, QMessageBox, 
                             QApplication, QHBoxLayout, QWidget)
from PyQt5.QtCore import pyqtSlot as Slot

import pandas as pd

home = os.path.expanduser('~')
    
class CycleTracks(QMainWindow):
    def __init__(self):
        super().__init__()
        
        path = os.path.join(home, '.cycletracks')
        os.makedirs(path, exist_ok=True)
        self.file = os.path.join(path, 'cycletracks.csv')
        self.sep = ','
        if not os.path.exists(self.file):
            header = ['Date', 'Time', 'Distance (km)', 'Calories', 'Gear']
            s = self.sep.join(header)
            with open(self.file, 'w') as fileobj:
                fileobj.write(s+'\n')
                
        self.df = pd.read_csv(self.file, sep=self.sep)
        self._backup() # TODO call this after every save (or change?)

        self.layout = QHBoxLayout()
        
        date = [datetime.strptime(d, "%Y-%m-%d").timestamp() for d in self.df['Date']]
        self.plot = PlotWidget(axisItems = {'bottom': DateAxisItem()})
        self.plot.plotItem.plot(date, self.df['Distance (km)'])
        
        self.layout.addWidget(self.plot)
        
        self.mainWidget = QWidget()
        self.mainWidget.setLayout(self.layout)
        self.setCentralWidget(self.mainWidget)
        
        self.show()
        
        
    def _backup(self):
        bak = self.file + '.bak'
        self.df.to_csv(bak, sep=self.sep)
            
        
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CycleTracks()
    sys.exit(app.exec_())