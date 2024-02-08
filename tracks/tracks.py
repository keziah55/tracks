#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main window for Tracks.
"""

from pathlib import Path
from functools import partial
from qtpy.QtWidgets import QMainWindow, QDockWidget, QAction, QSizePolicy, QLabel, QToolBar
from qtpy.QtCore import Qt, Slot
from qtpy.QtGui import QIcon
from .activities import ActivityManager
from .preferences import PreferencesDialog
from .util import intToStr
from customQObjects.widgets import StackedWidget
from customQObjects.core import Settings

import inspect


class Tracks(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        self.settings = Settings()
        
        self._saveLabel = QLabel()
        self._summaryLabel = QLabel()
        
        activity = self.settings.value("activity/current", "cycling")
        
        self._activity_manager = ActivityManager()
        
        self._activity_manager.status_message.connect(self.statusBar().showMessage)
        
        self._viewer_stack = StackedWidget()
        self._best_month_stack = StackedWidget()
        self._best_sessions_stack = StackedWidget()
        self._add_data_stack = StackedWidget()
        self._plot_stack = StackedWidget()
        
        self._best_month_stack.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self._best_sessions_stack.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self._viewer_stack.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self._add_data_stack.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        
        self._stack_attrs = {
            self._viewer_stack: "data_viewer",
            self._best_month_stack: ("personal_bests", "bestMonth"),
            self._best_sessions_stack: ("personal_bests", "bestSessions"),
            self._add_data_stack: "add_data",
            self._plot_stack: "plot",
        }
        
        self.prefDialog = PreferencesDialog(self)
        
        self._load_activity(activity)
        
        # TODO handle this - TG-136
        numTopSessions = self.settings.value("pb/numSessions", 5, int)
        monthCriterion = self.settings.value("pb/bestMonthCriterion", "distance")
        
        dockWidgets = [
            (
                self._best_month_stack,
                Qt.LeftDockWidgetArea, 
                f"Best month ({monthCriterion})", 
                "PB month"
            ),
            (
                self._best_sessions_stack,
                Qt.LeftDockWidgetArea, 
                f"Top {intToStr(numTopSessions)} sessions", 
                "PB sessions"
            ),
            (
                self._viewer_stack,
                Qt.LeftDockWidgetArea, 
                "Monthly data"
            ),
            (
                self._add_data_stack,
                Qt.LeftDockWidgetArea, 
                "Add data"
            )
        ]
        
        for args in dockWidgets:
            self._create_dock_widget(*args)
        # self.setCentralWidget(self.plot)
        self.setCentralWidget(self._plot_stack)
        
        state = self.settings.value("window/state", None)
        if state is not None:
            self.restoreState(state)
            
        geometry = self.settings.value("window/geometry", None)    
        if geometry is not None:
            self.restoreGeometry(geometry)
        
        # self.prefDialog = PreferencesDialog(self)
        
        self._create_actions()
        self._create_menus()
        self._create_toolbars()
        
        p = Path(__file__).parents[1].joinpath("images/icon.png")
        icon = QIcon(str(p))
        self.setWindowIcon(icon)
        
    ###########################################################################
    # TG-136 these properties are used by plot and data preferences
    @property
    def data(self):
        # print(f"{inspect.stack()[0].function} called by {inspect.stack()[1].function} in {inspect.stack()[1].filename}, line {inspect.stack()[1].lineno}")
        ao = self._activity_manager.get_activity_objects(self.current_activity.name)
        return ao.data
    
    @property
    def viewer(self):
        # print(f"{inspect.stack()[0].function} called by {inspect.stack()[1].function} in {inspect.stack()[1].filename}, line {inspect.stack()[1].lineno}")
        ao = self._activity_manager.get_activity_objects(self.current_activity.name)
        return ao.data_viewer
    
    @property
    def pb(self):
        # print(f"{inspect.stack()[0].function} called by {inspect.stack()[1].function} in {inspect.stack()[1].filename}, line {inspect.stack()[1].lineno}")
        ao = self._activity_manager.get_activity_objects(self.current_activity.name)
        return ao.personal_bests
        
    @property
    def plot(self):
        # print(f"{inspect.stack()[0].function} called by {inspect.stack()[1].function} in {inspect.stack()[1].filename}, line {inspect.stack()[1].lineno}")
        ao = self._activity_manager.get_activity_objects(self.current_activity.name)
        return ao.plot
    
    @property
    def addData(self):
        # print(f"{inspect.stack()[0].function} called by {inspect.stack()[1].function} in {inspect.stack()[1].filename}, line {inspect.stack()[1].lineno}")
        ao = self._activity_manager.get_activity_objects(self.current_activity.name)
        return ao.add_data
    ###########################################################################
    
    @property
    def current_activity(self):
        return self._activity_manager.current_activity
    
    @Slot(str)
    def _load_activity(self, name):
        
        activity_objects = self._activity_manager.load_activity(name)
        
        new_widgets = False
        for stack, attr in self._stack_attrs.items():
            if name not in stack:
                new_widgets = True
                if isinstance(attr, str):
                    widget = getattr(activity_objects, attr)
                elif isinstance(attr, (list, tuple)):
                    widget = activity_objects
                    for at in attr:
                        widget = getattr(widget, at)
                stack.addWidget(widget, name)
            stack.setCurrentKey(name)
            
        if new_widgets:
            for page in activity_objects.preferences.values():
                self.prefDialog.add_page(name, page)
            
            activity_objects.personal_bests.numSessionsChanged.connect(self._set_pb_sessions_dock_label)
            activity_objects.personal_bests.monthCriterionChanged.connect(self._set_pb_month_dock_label)
    
    @Slot()
    def save(self, activity=None):
        self._activity_manager.save_activity(activity)
        
    @Slot()
    def backup(self, activity=None):
        self._activity_manager.backup_activity(activity)
        
    # @Slot()
    # def _summary_value_changed(self):
    #     # TG-136
    #     # called from data pref
    #     self.viewer.updateTopLevelItems()
    #     self.pb.newData()
        
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
        
        # TG-136
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
        
        self.preferencesAct = QAction(
            "&Preferences", self, shortcut="F12", statusTip="Edit preferences",
            triggered=self.prefDialog.show)
        
    def _create_menus(self):
        self._file_menu = self.menuBar().addMenu("&File")
        self._file_menu.addAction(self.saveAct)
        self._activities_menu = self._file_menu.addMenu("&Activities")
        for activity in self._activity_manager.list_activities():
            callback = partial(self._load_activity, activity)
            self._activities_menu.addAction(activity.capitalize(), callback)
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