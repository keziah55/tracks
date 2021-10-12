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
from pandas._testing import assert_frame_equal
from .plot import CyclePlotWidget
from .data import CycleData, CycleDataAnalysis, CycleDataViewer, AddCycleData, PersonalBests
from .preferences import PreferencesDialog
from .util import intToStr
from customQObjects.core import Settings


class CycleTracks(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.settings = Settings()
        self.statusBar()
        self.statusTimeout = 2000
        
        self.file = self.getFile()
        self.sep = ','
        if not os.path.exists(self.file):
            header = ['Date', 'Time', 'Distance (km)', 'Calories', 'Gear']
            s = self.sep.join(header)
            with open(self.file, 'w') as fileobj:
                fileobj.write(s+'\n')
                
        df = pd.read_csv(self.file, sep=self.sep, parse_dates=['Date'])
        self.data = CycleData(df)
        self.save()
        self.dataAnalysis = CycleDataAnalysis(self.data)

        numTopSessions = self.settings.value("pb/numSessions", 5, int)
        monthCriterion = self.settings.value("pb/bestMonthCriterion", "distance")
        self.pb = PersonalBests(self, numSessions=numTopSessions, 
                                monthCriterion=monthCriterion)
        self.viewer = CycleDataViewer(self)
        self.addData = AddCycleData()
        plotStyle = self.settings.value("plot/style", "dark")
        self.plot = CyclePlotWidget(self, style=plotStyle)
        
        self.pb.bestMonth.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.pb.bestSessions.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.addData.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        
        self.addData.newData.connect(self.data.append)
        self.data.dataChanged.connect(self.viewer.newData)
        self.data.dataChanged.connect(self.plot.newData)
        self.data.dataChanged.connect(self.pb.newData)
        self.data.dataChanged.connect(self.save)
        self.plot.pointSelected.connect(self.viewer.highlightItem)
        self.viewer.itemSelected.connect(self.plot.setCurrentPointFromDate)
        self.viewer.requestRemoveData.connect(self.data.removeRows)
        self.viewer.requestAddData.connect(self.data.append)
        self.pb.itemSelected.connect(self.plot.setCurrentPointFromDate)
        self.pb.numSessionsChanged.connect(self.setPbSessionsDockLabel)
        self.pb.monthCriterionChanged.connect(self.setPbMonthDockLabel)
        
        self.fileChangedTimer = QTimer()
        self.fileChangedTimer.setInterval(100)
        self.fileChangedTimer.setSingleShot(True)
        self.fileChangedTimer.timeout.connect(self.csvFileChanged)
        self.fileWatcher = QFileSystemWatcher([self.file])
        self.fileWatcher.fileChanged.connect(self.startTimer)
        
        
        dockWidgets = [(self.pb.bestMonth, Qt.LeftDockWidgetArea, f"Best month ({monthCriterion})", "PB month"),
                       (self.pb.bestSessions, Qt.LeftDockWidgetArea, f"Top {intToStr(numTopSessions)} sessions", "PB sessions"),
                       (self.viewer, Qt.LeftDockWidgetArea, "Monthly data"),
                       (self.addData, Qt.LeftDockWidgetArea, "Add data")]
        
        for args in dockWidgets:
            self.createDockWidget(*args)
        self.setCentralWidget(self.plot)
        
        state = self.settings.value("window/state", None)
        if state is not None:
            self.restoreState(state)
            
        geometry = self.settings.value("window/geometry", None)    
        if geometry is not None:
            self.restoreGeometry(geometry)
        
        self.prefDialog = PreferencesDialog(self)
        
        self.createActions()
        self.createMenus()
        
        fileDir = os.path.split(__file__)[0]
        path = os.path.join(fileDir, "..", "images/icon.png")
        icon = QIcon(path)
        self.setWindowIcon(icon)
        
    def show(self):
        super().show()
        self.prefDialog.ok()
        
    @staticmethod
    def getFile():
        home = os.path.expanduser('~')
        path = os.path.join(home, '.cycletracks')
        os.makedirs(path, exist_ok=True)
        file = os.path.join(path, 'cycletracks2.csv')
        return file
        
    @Slot()
    def save(self):
        self.data.df.to_csv(self.file, sep=self.sep, index=False)
        self.backup()
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
        try: 
            assert_frame_equal(self.data.df, df, check_exact=False)
        except AssertionError:
            msg = "CycleTracks csv file changed on disk. Do you want to reload?"
            btn = QMessageBox.question(self, "File changed on disk", msg)
            if btn == QMessageBox.Yes:
                self.loadCsvFile()
            
    def loadCsvFile(self):
        df = pd.read_csv(self.file, sep=self.sep, parse_dates=['Date'])
        self.backup()
        self.data.setDataFrame(df)
        
    def createDockWidget(self, widget, area, title, key=None):
        dock = QDockWidget()
        dock.setWidget(widget)
        dock.setWindowTitle(title)
        dock.setObjectName(title)
        self.addDockWidget(area, dock)
        if not hasattr(self, "dockWidgets"):
            self.dockWidgets = {}
        if key is None:
            key = title
        self.dockWidgets[key] = dock
        
    def setPbSessionsDockLabel(self, num):
        label = f"Top {intToStr(num)} sessions"
        self.dockWidgets["PB sessions"].setWindowTitle(label)
    
    def setPbMonthDockLabel(self, monthCriterion):
        label = f"Best month ({monthCriterion})"
        self.dockWidgets["PB month"].setWindowTitle(label)
        
    def close(self, *args, **kwargs):
        self.backup()
        state = self.saveState()
        geometry = self.saveGeometry()
        self.settings.setValue("window/state", state)
        self.settings.setValue("window/geometry", geometry)
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
    