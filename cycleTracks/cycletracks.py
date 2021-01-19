#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main window for cycleTracks.
"""

import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QApplication, QDockWidget, QSizePolicy, 
                             QAction)
from PyQt5.QtCore import Qt
import pandas as pd
from cycleplotwidget import CyclePlotWidget
from cycledataviewer import CycleDataViewer
from cycledata import CycleData
from addcycledata import AddCycleData

    
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

        self.data = CycleData(self.df)

        self.viewer = CycleDataViewer(self.data)
        self.addData = AddCycleData()
        self.plot = CyclePlotWidget(self.data)
        
        dockWidgets = [(self.viewer, Qt.LeftDockWidgetArea, "Monthly Data"),
                       (self.addData, Qt.LeftDockWidgetArea, "Add Data")]
        
        for widget, area, title in dockWidgets:
            self.createDockWidget(widget, area, title=title)
            
        self.setCentralWidget(self.plot)
        
        policy = QSizePolicy.Minimum
        # self.viewer.setSizePolicy(policy, QSizePolicy.Preferred)
        self.addData.setSizePolicy(policy, QSizePolicy.Preferred)
        self.plot.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        
        self.createActions()
        self.createMenus()
        
        self.setWindowTitle('Cycle Tracks')
        self.showMaximized()
               
        
    def _backup(self):
        bak = self.file + '.bak'
        self.df.to_csv(bak, sep=self.sep)
        
    def createDockWidget(self, widget, area, title=None):
        self.dock = QDockWidget()
        self.dock.setWidget(widget)
        if title is not None:
            self.dock.setWindowTitle(title)
        self.addDockWidget(area, self.dock)
        
    def createActions(self):
        
        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q",
                               statusTip="Exit the application", 
                               triggered=self.close)
            
    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.exitAct)
    
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CycleTracks()
    window.show()
    sys.exit(app.exec_())
    