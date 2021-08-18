#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main window for cycleTracks.
"""

import os
from PyQt5.QtWidgets import QMainWindow, QDockWidget, QAction, QSizePolicy, QMessageBox
from PyQt5.QtCore import Qt, QFileSystemWatcher, QTimer, pyqtSlot as Slot
from PyQt5.QtGui import QIcon
import pandas as pd
from .plot import CyclePlotWidget
from .data import CycleData, CycleDataAnalysis, CycleDataViewer, AddCycleData, PersonalBests
from .preferences import PreferencesDialog
from customQObjects.core import Settings


class CycleTracks(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.settings = Settings()
        
        self.file = self.getFile()
        self.sep = ','
        if not os.path.exists(self.file):
            header = ['Date', 'Time', 'Distance (km)', 'Calories', 'Gear']
            s = self.sep.join(header)
            with open(self.file, 'w') as fileobj:
                fileobj.write(s+'\n')
                
        self.fileChangedTimer = QTimer()
        self.fileChangedTimer.setInterval(100)
        self.fileChangedTimer.setSingleShot(True)
        self.fileChangedTimer.timeout.connect(self.csvFileChanged)
        self.fileWatcher = QFileSystemWatcher([self.file])
        self.fileWatcher.fileChanged.connect(self.startTimer)
        
        df = pd.read_csv(self.file, sep=self.sep, parse_dates=['Date'])
        self.data = CycleData(df)
        self.backup()
        self.dataAnalysis = CycleDataAnalysis(self.data)

        self.pb = PersonalBests(self)
        self.viewer = CycleDataViewer(self)
        self.addData = AddCycleData()
        plotStyle = self.settings.value("plot/style", "dark")
        self.plot = CyclePlotWidget(self, style=plotStyle)
        
        # self.pb.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.pb.label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.pb.table.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.addData.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        
        self.addData.newData.connect(self.data.append)
        self.data.dataChanged.connect(self.viewer.newData)
        self.data.dataChanged.connect(self.plot.newData)
        self.data.dataChanged.connect(self.pb.newData)
        self.data.dataChanged.connect(self.backup)
        self.data.dataChanged.connect(self.save)
        self.plot.pointSelected.connect(self.viewer.highlightItem)
        self.viewer.itemSelected.connect(self.plot.setCurrentPointFromDate)
        self.pb.itemSelected.connect(self.plot.setCurrentPointFromDate)
        
        dockWidgets = [#(self.pb, Qt.LeftDockWidgetArea, "Personal Bests"),
                       (self.pb.label, Qt.LeftDockWidgetArea, "Best month"),
                       (self.pb.table, Qt.LeftDockWidgetArea, "Top five sessions"),
                       (self.viewer, Qt.LeftDockWidgetArea, "Monthly Data"),
                       (self.addData, Qt.LeftDockWidgetArea, "Add Data")]
        
        for widget, area, title in dockWidgets:
            self.createDockWidget(widget, area, title=title)
            
        self.setCentralWidget(self.plot)
        
        self.prefDialog = PreferencesDialog(self)
        
        self.createActions()
        self.createMenus()
        self.statusBar()
        self.statusTimeout = 2000
        
        fileDir = os.path.split(__file__)[0]
        path = os.path.join(fileDir, "..", "images/icon.png")
        icon = QIcon(path)
        self.setWindowIcon(icon)
        self.showMaximized()
            
    @staticmethod
    def getFile():
        home = os.path.expanduser('~')
        path = os.path.join(home, '.cycletracks')
        os.makedirs(path, exist_ok=True)
        file = os.path.join(path, 'cycletracks.csv')
        return file
        
    @Slot()
    def save(self):
        self.data.df.to_csv(self.file, sep=self.sep, index=False)
        self.statusBar().showMessage("Data saved", msecs=self.statusTimeout)
        
    @Slot()
    def backup(self):
        bak = self.file + '.bak'
        self.data.df.to_csv(bak, sep=self.sep, index=False)
        
    @Slot(str)
    def startTimer(self, file):
        self._fileChanged = file
        self.fileChangedTimer.start()
        
    @Slot()
    def csvFileChanged(self):
        df = pd.read_csv(self._fileChanged, sep=self.sep, parse_dates=['Date'])
        if not self.data.df.equals(df):
            msg = "CycleTracks csv file changed on disk. Do you want to reload?"
            btn = QMessageBox.question(self, "File changed on disk", msg)
            if btn == QMessageBox.Yes:
                self.loadCsvFile()
            
    def loadCsvFile(self):
        df = pd.read_csv(self.file, sep=self.sep, parse_dates=['Date'])
        self.backup()
        self.data.setDataFrame(df)
        
    def createDockWidget(self, widget, area, title):
        dock = QDockWidget()
        dock.setWidget(widget)
        dock.setWindowTitle(title)
        self.addDockWidget(area, dock)
        if not hasattr(self, "dockWidgets"):
            self.dockWidgets = {}
        self.dockWidgets[title] = dock
        
    def close(self, *args, **kwargs):
        self.backup()
        super().close()
        
    def createActions(self):
        
        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q",
                               statusTip="Exit the application", 
                               triggered=self.close)
            
        self.saveAct = QAction("&Save", self, shortcut="Ctrl+S", 
                               statusTip="Save data", triggered=self.save)
        
        self.combineAct = QAction("&Combine", self, shortcut="Ctrl+Shift+C", 
                                  statusTip="Combine the selected rows in the viewer",
                                  triggered=self.viewer.combineRows)
        
        self.preferencesAct = QAction("&Preferences", self, shortcut="F12",
                                      statusTip="Edit preferences",
                                      triggered=self.prefDialog.show)
        
    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)
        
        self.editMenu = self.menuBar().addMenu("&Edit")
        self.editMenu.addAction(self.combineAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.preferencesAct)
        
        self.viewMenu = self.menuBar().addMenu("&View")
        self.panelMenu = self.viewMenu.addMenu("&Panels")
        for key in sorted(self.dockWidgets):
            dock = self.dockWidgets[key]
            self.panelMenu.addAction(dock.toggleViewAction())
    