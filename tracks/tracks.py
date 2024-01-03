#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main window for Tracks.
"""

from pathlib import Path
from datetime import datetime, date
import warnings
from qtpy.QtWidgets import (QMainWindow, QDockWidget, QAction, QSizePolicy, 
                             QMessageBox, QLabel)
from qtpy.QtCore import Qt, QFileSystemWatcher, QTimer, Slot
from qtpy.QtGui import QIcon
import pandas as pd
from pandas._testing import assert_frame_equal
from .activities import load_activity, Activity
from .plot import PlotWidget
from .data import Data, DataViewer, AddData, PersonalBests
from .preferences import PreferencesDialog
from .util import intToStr
from customQObjects.core import Settings


class Tracks(QMainWindow):
    
    _csv_sep = ","
    
    def __init__(self):
        super().__init__()
        
        self.settings = Settings()
        
        self._saveLabel = QLabel()
        self._summaryLabel = QLabel()
        
        activity = self.settings.value("activity/current", "cycling")
        
        self.activities = []
        act = load_activity(self.get_data_path().joinpath(f"{activity}.json"))
        self.activities.insert(0, act)
        
        df = self.load_df(act)

        self.data = Data(df, act)
        self.save()
        
        numTopSessions = self.settings.value("pb/numSessions", 5, int)
        monthCriterion = self.settings.value("pb/bestMonthCriterion", "distance")
        sessionsKey = self.settings.value("pb/sessionsKey", "Speed (km/h)")
        self.pb = PersonalBests(
            self, 
            act,
            numSessions=numTopSessions, 
            monthCriterion=monthCriterion,
            sessionsKey=sessionsKey)
        
        self.viewer = DataViewer(self, act)
        
        self.addData = AddData(act)
        
        plot_style = self.settings.value("plot/style", "dark")
        month_range = self.parse_month_range(self.settings.value("plot/range", "All"))
        y_series = self.settings.value("plot/current_series", "time")
        self.plot = PlotWidget(
            self, 
            act,
            style=plot_style, 
            months=month_range,
            y_series=y_series)
        
        self.pb.bestMonth.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.pb.bestSessions.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.viewer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.addData.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        
        self.addData.newData.connect(self.data.append)
        self.data.dataChanged.connect(self._dataChanged)
        self.plot.pointSelected.connect(self.viewer.highlightItem)
        self.viewer.itemSelected.connect(self.plot.setCurrentPointFromDate)
        self.viewer.selectedSummary.connect(self.statusBar().showMessage)
        self.pb.itemSelected.connect(self.plot.setCurrentPointFromDate)
        self.pb.numSessionsChanged.connect(self.setPbSessionsDockLabel)
        self.pb.monthCriterionChanged.connect(self.setPbMonthDockLabel)
        self.pb.statusMessage.connect(self.statusBar().showMessage)
        
        self.fileChangedTimer = QTimer()
        self.fileChangedTimer.setInterval(100)
        self.fileChangedTimer.setSingleShot(True)
        self.fileChangedTimer.timeout.connect(self.csvFileChanged)
        self.fileWatcher = QFileSystemWatcher([str(self.current_activity.csv_file)])
        self.fileWatcher.fileChanged.connect(self.startTimer)
        
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
        
    @staticmethod
    def parse_month_range(s) -> int:
        """ 
        Parse string into int number of months.
        
        |        s       |            Return           |
        |:--------------:|:---------------------------:|
        |  "[X] months"  |              X              |
        |    "1 year"    |              12             |
        | "current year" | datetime.date.today().month |
        |      "all"     |             None            |
        """
        s = s.lower()
        if s == "1 year":
            s = "12 months"
        elif s == "current year":
            s = f"{date.today().month} months"
        months = None if s == 'all' else int(s.strip(' months'))
        return months
        
    @staticmethod
    def get_data_path():
        p = Path.home().joinpath('.tracks')
        if not p.exists():
            p.mkdir(parents=True)
        return p
    
    @classmethod
    def getFile(cls):
        warnings.warn("Tracks.getFile is deprecated", DeprecationWarning)
        p = cls.get_data_path()
        file = p.joinpath('tracks.csv')
        return file
    
    @classmethod
    def get_activity_csv(cls, activity):
        p = cls.get_data_path()
        filepath = p.joinpath(activity.csv_file)
        return filepath
    
    @property
    def current_activity(self):
        if len(self.activities) == 0:
            return None
        else:
            return self.activities[0]
    
    @classmethod
    def load_df(cls, activity) -> pd.DataFrame:
        """ Load dataframe for `activity` """
        
        filepath = cls.get_activity_csv(activity)
        
        if not filepath.exists():
            header = activity.header
            s = cls._csv_sep.join(header) + "\n"
            with open(filepath, 'w') as fileobj:
                fileobj.write(s)
                
        df = pd.read_csv(filepath, sep=cls._csv_sep, parse_dates=['Date'])
        
        return df
    
    def load_current_df(self):
        """ Load dataframe for current activity """
        activity = self.current_activity
        return self.load_df(activity)
    
    @Slot()
    def save(self, activity=None):
        if activity is None:
            activity = self.current_activity
        filepath = self.get_activity_csv(activity)
        
        self.data.df.to_csv(filepath, sep=self._csv_sep, index=False)
        self.backup()
        save_time = datetime.now().strftime("%H:%M:%S")
        self.statusBar().showMessage(f"Last saved at {save_time}")
        
    @Slot()
    def backup(self, activity=None):
        if activity is None:
            activity = self.current_activity
        p = self.get_data_path()
        filepath = p.joinpath(activity.csv_file)
        
        bak = filepath.with_suffix('.bak')
        self.data.df.to_csv(bak, sep=self._csv_sep, index=False)
        
    @Slot(str)
    def startTimer(self, file):
        self._fileChanged = file
        self.fileChangedTimer.start()
        
    @Slot()
    def csvFileChanged(self):
        df = pd.read_csv(self._fileChanged, sep=self._csv_sep, parse_dates=['Date'])
        try: 
            assert_frame_equal(self.data.df, df, check_exact=False)
        except AssertionError:
            msg = "Tracks csv file changed on disk. Do you want to reload?"
            btn = QMessageBox.question(self, "File changed on disk", msg)
            if btn == QMessageBox.Yes:
                self.loadCsvFile()
            
    def loadCsvFile(self):
        df = pd.read_csv(self.file, sep=self._csv_sep, parse_dates=['Date'])
        self.backup()
        self.data.setDataFrame(df)
        
    @Slot(object)
    def _dataChanged(self, idx):
        self.viewer.newData(idx)
        self.plot.newData(idx)
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
    
