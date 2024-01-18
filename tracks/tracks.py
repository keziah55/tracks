#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main window for Tracks.
"""

from pathlib import Path
from datetime import datetime
from functools import partial
from qtpy.QtWidgets import QMainWindow, QDockWidget, QAction, QSizePolicy, QLabel, QToolBar
from qtpy.QtCore import Qt, Slot
from qtpy.QtGui import QIcon
from .activities import ActivityManager
from .preferences import PreferencesDialog
from .util import intToStr
from . import get_data_path
from customQObjects.widgets import StackedWidget
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
        
        self._viewer_stack = StackedWidget()
        self._best_month_stack = StackedWidget()
        self._best_sessions_stack = StackedWidget()
        self._add_data_stack = StackedWidget()
        self._plot_stack = StackedWidget()
        
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
        self.data.dataChanged.connect(self._data_changed)
        self.plot.point_selected.connect(self.viewer.highlightItem)
        self.viewer.itemSelected.connect(self.plot.set_current_point_from_date)
        self.viewer.selectedSummary.connect(self.statusBar().showMessage)
        self.pb.itemSelected.connect(self.plot.set_current_point_from_date)
        self.pb.numSessionsChanged.connect(self._set_pb_sessions_dock_label)
        self.pb.monthCriterionChanged.connect(self._set_pb_month_dock_label)
        self.pb.statusMessage.connect(self.statusBar().showMessage)
        
        dockWidgets = [
            (
                self.pb.bestMonth, 
                Qt.LeftDockWidgetArea, 
                f"Best month ({monthCriterion})", 
                "PB month"
            ),
            (
                self.pb.bestSessions, 
                Qt.LeftDockWidgetArea, 
                f"Top {intToStr(numTopSessions)} sessions", 
                "PB sessions"
            ),
            (
                self.viewer, 
                Qt.LeftDockWidgetArea, 
                "Monthly data"
            ),
            (
                self.addData, 
                Qt.LeftDockWidgetArea, 
                "Add data"
            )
        ]
        
        for args in dockWidgets:
            self._create_dock_widget(*args)
        self.setCentralWidget(self.plot)
        
        state = self.settings.value("window/state", None)
        if state is not None:
            self.restoreState(state)
            
        geometry = self.settings.value("window/geometry", None)    
        if geometry is not None:
            self.restoreGeometry(geometry)
        
        self.prefDialog = PreferencesDialog(self)
        
        self._create_actions()
        self._create_menus()
        self._create_toolbars()
        
        p = Path(__file__).parents[1].joinpath("images/icon.png")
        icon = QIcon(str(p))
        self.setWindowIcon(icon)
        
    @property
    def current_activity(self):
        return self._activity_manager.current_activity
    
    @Slot(str)
    def _load_activity(self, name):
        self._activity_manager.load_activity(name)
    
    @Slot()
    def save(self, activity=None):
        self._activity_manager.save_activity(activity)
        save_time = datetime.now().strftime("%H:%M:%S")
        self.statusBar().showMessage(f"Last saved at {save_time}")
        
    @Slot()
    def backup(self, activity=None):
        self._activity_manager.backup_activity(activity)
        
    @Slot(object)
    def _data_changed(self, idx):
        self.viewer.newData(idx)
        self.plot.new_data(idx)
        self.pb.newData(idx)
        self.save()
        
    @Slot()
    def _summary_value_changed(self):
        self.viewer.updateTopLevelItems()
        self.pb.newData()
        
    def _create_dock_widget(self, widget, area, title, key=None):
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
        
    def _set_pb_sessions_dock_label(self, num):
        label = f"Top {intToStr(num)} sessions"
        self.dockWidgets["PB sessions"].setWindowTitle(label)
    
    def _set_pb_month_dock_label(self, monthCriterion):
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
            
        self.settings.setValue("activity/current", self.current_activity.name)
        
    def _create_actions(self):
        self.exitAct = QAction(
            "E&xit", self, shortcut="Ctrl+Q", statusTip="Exit the application", 
            triggered=self.close)
            
        self.saveAct = QAction(
            "&Save", self, shortcut="Ctrl+S", statusTip="Save data", 
            triggered=self.save)
        
        # self._load_activity_act = QAction(#icon, text)
        #     "Choose &Activity", self, shortcut="Ctrl+A", statusTip="Choose activity",
        #     triggered=self._load_activity)
        
        self.preferencesAct = QAction(
            "&Preferences", self, shortcut="F12", statusTip="Edit preferences",
            triggered=self.prefDialog.show)
        
    def _create_menus(self):
        self._file_menu = self.menuBar().addMenu("&File")
        self._file_menu.addAction(self.saveAct)
        self._activities_menu = self._file_menu.addMenu("&Activities")
        for activity in self._activity_manager.list_activities():
            callback = partial(self._load_activity, activity)
            self._activities_menu.addAction(activity, callback)
        self._file_menu.addSeparator()
        self._file_menu.addAction(self.exitAct)
        
        self._edit_menu = self.menuBar().addMenu("&Edit")
        self._edit_menu.addAction(self.preferencesAct)
        
        self._view_menu = self.menuBar().addMenu("&View")
        self._panel_menu = self._view_menu.addMenu("&Panels")
        for key in sorted(self.dockWidgets):
            dock = self.dockWidgets[key]
            self._panel_menu.addAction(dock.toggleViewAction())
    
    def _create_toolbars(self):
        return
        self._options_toolsbar = QToolBar("Options")
        
        actions = [self.saveAct, self._load_activity_act, self.preferencesAct, self.exitAct]
        self._options_toolsbar.addActions(actions)
        
        self.addToolBar(Qt.LeftToolBarArea, self._options_toolsbar)