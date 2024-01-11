#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main window for Tracks.
"""

from pathlib import Path
from datetime import datetime
from qtpy.QtWidgets import QMainWindow, QDockWidget, QAction, QSizePolicy, QLabel
from qtpy.QtCore import Qt, Slot
from qtpy.QtGui import QIcon
from .activities import ActivityManager
from .preferences import PreferencesDialog
from .util import intToStr
from . import get_data_path
from customQObjects.core import Settings


class Tracks(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        self.settings = Settings()
        
        self._saveLabel = QLabel()
        self._summaryLabel = QLabel()
        
        activity = self.settings.value("activity/current", "cycling")
        
        self._activity_manager = ActivityManager(get_data_path(), self.settings)
        
        activity_objects = self._activity_manager.load_activity(activity)
        
        self.data = activity_objects.data
        self.viewer = activity_objects.data_viewer
        self.pb = activity_objects.personal_bests
        self.plot = activity_objects.plot
        self.addData = activity_objects.add_data

        # TODO handle this
        numTopSessions = self.settings.value("pb/numSessions", 5, int)
        monthCriterion = self.settings.value("pb/bestMonthCriterion", "distance")

        
        self.pb.bestMonth.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.pb.bestSessions.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.viewer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.addData.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        
        self.addData.newData.connect(self.data.append)
        self.data.dataChanged.connect(self._dataChanged)
        self.plot.point_selected.connect(self.viewer.highlightItem)
        self.viewer.itemSelected.connect(self.plot.set_current_point_from_date)
        self.viewer.selectedSummary.connect(self.statusBar().showMessage)
        self.pb.itemSelected.connect(self.plot.set_current_point_from_date)
        self.pb.numSessionsChanged.connect(self.setPbSessionsDockLabel)
        self.pb.monthCriterionChanged.connect(self.setPbMonthDockLabel)
        self.pb.statusMessage.connect(self.statusBar().showMessage)
        
        dockWidgets = [(self.pb.bestMonth, Qt.LeftDockWidgetArea, 
                        f"Best month ({monthCriterion})", "PB month"),
                       (self.pb.bestSessions, Qt.LeftDockWidgetArea, 
                        f"Top {intToStr(numTopSessions)} sessions", "PB sessions"),
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
        
        p = Path(__file__).parents[1].joinpath("images/icon.png")
        icon = QIcon(str(p))
        self.setWindowIcon(icon)
        
    @property
    def current_activity(self):
        return self._activity_manager.current_activity
    
    @Slot()
    def save(self, activity=None):
        self._activity_manager.save_activity(activity)
        save_time = datetime.now().strftime("%H:%M:%S")
        self.statusBar().showMessage(f"Last saved at {save_time}")
        
    @Slot()
    def backup(self, activity=None):
        self._activity_manager.backup_activity(activity)
        
    @Slot(str)
    def startTimer(self, file):
        self._fileChanged = file
        self.fileChangedTimer.start()
        
    @Slot(object)
    def _dataChanged(self, idx):
        self.viewer.newData(idx)
        self.plot.new_data(idx)
        self.pb.newData(idx)
        self.save()
        
    @Slot()
    def _summaryValueChanged(self):
        self.viewer.updateTopLevelItems()
        self.pb.newData()
        
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
        
    def closeEvent(self, *args, **kwargs):
        self.backup()
        state = self.saveState()
        geometry = self.saveGeometry()
        self.settings.setValue("window/state", state)
        self.settings.setValue("window/geometry", geometry)
        
        for key, value in self.pb.state().items():
            self.settings.setValue(f"pb/{key}", value)
            
        for key, value in self.plot.state().items():
            self.settings.setValue(f"plot/{key}", value)
        
    def createActions(self):
        self.exitAct = QAction(
            "E&xit", self, shortcut="Ctrl+Q", statusTip="Exit the application", 
            triggered=self.close)
            
        self.saveAct = QAction(
            "&Save", self, shortcut="Ctrl+S", statusTip="Save data", 
            triggered=self.save)
        
        self.preferencesAct = QAction(
            "&Preferences", self, shortcut="F12", statusTip="Edit preferences",
            triggered=self.prefDialog.show)
        
    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)
        
        self.editMenu = self.menuBar().addMenu("&Edit")
        self.editMenu.addAction(self.preferencesAct)
        
        self.viewMenu = self.menuBar().addMenu("&View")
        self.panelMenu = self.viewMenu.addMenu("&Panels")
        for key in sorted(self.dockWidgets):
            dock = self.dockWidgets[key]
            self.panelMenu.addAction(dock.toggleViewAction())
    
