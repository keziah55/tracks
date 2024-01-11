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
        self.data.dataChanged.connect(self._data_changed)
        self.plot.point_selected.connect(self.viewer.highlightItem)
        self.viewer.itemSelected.connect(self.plot.set_current_point_from_date)
        self.viewer.selectedSummary.connect(self.statusBar().showMessage)
        self.pb.itemSelected.connect(self.plot.set_current_point_from_date)
        self.pb.numSessionsChanged.connect(self._set_pb_sessions_dock_label)
        self.pb.monthCriterionChanged.connect(self._set_pb_month_dock_label)
        self.pb.statusMessage.connect(self.statusBar().showMessage)
        
        _dock_widgets = [
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
        
        for args in _dock_widgets:
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
        
    @Slot(object)
    def _data_changed(self, idx):
        self.viewer.new_data(idx)
        self.plot.new_data(idx)
        self.pb.new_data(idx)
        self.save()
        
    @Slot()
    def _summary_value_changed(self):
        self.viewer.updateTopLevelItems()
        self.pb.new_data()
        
    def _create_dock_widget(self, widget, area, title, key=None):
        dock = QDockWidget()
        dock.setWidget(widget)
        dock.setWindowTitle(title)
        dock.setObjectName(title)
        self.addDockWidget(area, dock)
        if not hasattr(self, "_dock_widgets"):
            self._dock_widgets = {}
        if key is None:
            key = title
        self._dock_widgets[key] = dock
        
    def _set_pb_sessions_dock_label(self, num):
        label = f"Top {intToStr(num)} sessions"
        self._dock_widgets["PB sessions"].setWindowTitle(label)
    
    def _set_pb_month_dock_label(self, monthCriterion):
        label = f"Best month ({monthCriterion})"
        self._dock_widgets["PB month"].setWindowTitle(label)
        
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
        
    def _create_actions(self):
        self._exit_act = QAction(
            "E&xit", 
            self, 
            shortcut="Ctrl+Q", 
            statusTip="Exit the application", 
            triggered=self.close
        )
            
        self._save_act = QAction(
            "&Save", 
            self, 
            shortcut="Ctrl+S", 
            statusTip="Save data", 
            triggered=self.save
        )
        
        self._preferences_act = QAction(
            "&Preferences", 
            self, 
            shortcut="F12", 
            statusTip="Edit preferences",
            triggered=self.prefDialog.show
        )
        
    def _create_menus(self):
        self._file_menu = self.menuBar().addMenu("&File")
        self._file_menu.addAction(self._save_act)
        self._file_menu.addSeparator()
        self._file_menu.addAction(self._exit_act)
        
        self._edit_menu = self.menuBar().addMenu("&Edit")
        self._edit_menu.addAction(self._preferences_act)
        
        self._view_menu = self.menuBar().addMenu("&View")
        self._panel_menu = self._view_menu.addMenu("&Panels")
        for key in sorted(self._dock_widgets):
            dock = self._dock_widgets[key]
            self._panel_menu.addAction(dock.toggleViewAction())
