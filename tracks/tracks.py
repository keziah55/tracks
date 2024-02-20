#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main window for Tracks.
"""

from pathlib import Path
from functools import partial
from qtpy.QtWidgets import QMainWindow, QDockWidget, QAction, QSizePolicy, QLabel, QToolBar
from qtpy.QtCore import Qt, Slot, QTimer
from qtpy.QtGui import QIcon, QKeyEvent
from .activities import ActivityManager
from .preferences import PreferencesDialog
from .util import intToStr
from customQObjects.widgets import StackedWidget, ListSelector
from customQObjects.core import Settings


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
        self._best_sessions_stack = StackedWidget()
        self._add_data_stack = StackedWidget()
        self._plot_stack = StackedWidget()
        
        self._best_sessions_stack.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self._viewer_stack.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self._add_data_stack.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        
        self._stack_attrs = {
            self._viewer_stack: "data_viewer",
            self._best_sessions_stack: ("personal_bests", "bestSessions"),
            self._add_data_stack: "add_data",
            self._plot_stack: "plot",
        }
        
        self.prefDialog = PreferencesDialog(self)
        
        self._load_activity(activity)
        
        _dock_widgets = [
            (
                self._best_sessions_stack,
                Qt.LeftDockWidgetArea, 
                "Top sessions", 
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
        
        for args in _dock_widgets:
            self._create_dock_widget(*args)
        self.setCentralWidget(self._plot_stack)
        
        pb = self._activity_manager.get_activity_objects(self.current_activity.name).personal_bests
        state = pb.state()
        self._set_pb_sessions_dock_label(state["num_best_sessions"])
        
        state = self.settings.value("window/state", None)
        if state is not None:
            self.restoreState(state)
            
        geometry = self.settings.value("window/geometry", None)    
        if geometry is not None:
            self.restoreGeometry(geometry)
        
        self._create_actions()
        self._create_menus()
        self._create_toolbars()
        
        self.activity_switcher = ListSelector(
            parent=self, values=self._activity_manager.list_activities(), style="font-size:24pt")
        self.activity_switcher.resize(200, 300)
        self.activity_switcher.hide()
        
        # self.installEventFilter(self)
        self._activity_switcher_timer = QTimer()
        self._activity_switcher_timer.setInterval(150)
        self._activity_switcher_timer.setSingleShot(True)
        
        p = Path(__file__).parents[1].joinpath("images/icon.png")
        icon = QIcon(str(p))
        self.setWindowIcon(icon)
            
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
            
            pb = activity_objects.personal_bests
            pb.numSessionsChanged.connect(self._set_pb_sessions_dock_label)
            
        self.setWindowTitle(f"Tracks - {name}")
    
    @Slot()
    def save(self, activity=None):
        self._activity_manager.save_activity(activity)
        
    @Slot()
    def backup(self, activity=None):
        self._activity_manager.backup_activity(activity)
        
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
    
    def closeEvent(self, *args, **kwargs):
        self.backup()
        state = self.saveState()
        geometry = self.saveGeometry()
        self.settings.setValue("window/state", state)
        self.settings.setValue("window/geometry", geometry)
        self.settings.setValue("activity/current", self.current_activity.name)
        
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
        
        # self._switch_activity_act = QAction(
        #     "Switch &activity",
        #     self,
        #     shortcut="Ctrl+A",
        #     triggered=self._activate_activity_switcher
        # )
        
    def _create_menus(self):
        self._file_menu = self.menuBar().addMenu("&File")
        self._file_menu.addAction(self._save_act)
        self._activities_menu = self._file_menu.addMenu("&Activities")
        for activity in self._activity_manager.list_activities():
            callback = partial(self._load_activity, activity)
            self._activities_menu.addAction(activity.capitalize(), callback)
        self._file_menu.addSeparator()
        self._file_menu.addAction(self._exit_act)
        
        self._edit_menu = self.menuBar().addMenu("&Edit")
        self._edit_menu.addAction(self._preferences_act)
        
        self._view_menu = self.menuBar().addMenu("&View")
        self._panel_menu = self._view_menu.addMenu("&Panels")
        for key in sorted(self._dock_widgets):
            dock = self._dock_widgets[key]
            self._panel_menu.addAction(dock.toggleViewAction())
    
    def _create_toolbars(self):
        return
        # self._options_toolsbar = QToolBar("Options")
        
        # actions = [self.saveAct, self._load_activity_act, self.preferencesAct, self.exitAct]
        # self._options_toolsbar.addActions(actions)
        
        # self.addToolBar(Qt.LeftToolBarArea, self._options_toolsbar)
        
    
    def _activate_activity_switcher(self):
        self._keys_pressed = ["A", "ctrl", "shift"]
        if self.activity_switcher.isVisible():
            self.activity_switcher.next()
        else:
            self.activity_switcher.show()
            
    def _accept_activity_switcher(self):
        new_activity = self.activity_switcher.current_text
        self.activity_switcher.hide()
        self._load_activity(new_activity)
        
    def _reject_activity_switcher(self):
        self.activity_switcher.hide()
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_A and event.modifiers()==Qt.ControlModifier|Qt.ShiftModifier:
            self._activate_activity_switcher()
            # event.accept()
        elif event.key() in [Qt.Key_Return, Qt.Key_Enter] and self.activity_switcher.isVisible():
            self._accept_activity_switcher()
            # event.accept()
        elif event.key() == Qt.Key_Escape and self.activity_switcher.isVisible():
            self._reject_activity_switcher()
            # event.accept()
        else:
            super().keyPressEvent(event)
            
    def keyReleaseEvent(self, event):
        # print(f"{event.key()}, {event.modifiers()}, {event.modifiers()|Qt.ControlModifier}, {event.modifiers()|Qt.ShiftModifier}")
        if self.activity_switcher.isVisible():
            if event.key() == Qt.Key_A:
                if "A" in self._keys_pressed:
                    print("remove A")
                    self._keys_pressed.remove("A")
            if event.modifiers()==Qt.ControlModifier|Qt.ShiftModifier:
                if "ctrl" in self._keys_pressed:
                    print("remove ctrl")
                    self._keys_pressed.remove("ctrl")
                if "shift" in self._keys_pressed:
                    print("remove shift")
                    self._keys_pressed.remove("shift")
            if event.modifiers()==Qt.ControlModifier:
                
                if "ctrl" in self._keys_pressed:
                    print("remove ctrl")
                    self._keys_pressed.remove("ctrl")
            if event.modifiers()==Qt.ShiftModifier:
                if "shift" in self._keys_pressed:
                    print("remove shift")
                    self._keys_pressed.remove("shift")
            
            if len(self._keys_pressed) == 0:
                self._reject_activity_switcher()
            # event.accept()
        else:
            super().keyPressEvent(event)
            
    def resizeEvent(self, event):
        
        x = event.size().width()
        y = event.size().height()
        
        x -= self.activity_switcher.size().width()
        y -= self.activity_switcher.size().height()
        
        x //= 2
        y //= 2
        
        self.activity_switcher.move(x, y)
        
        return super().resizeEvent(event)