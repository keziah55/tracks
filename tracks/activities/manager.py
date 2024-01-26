#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Object to manage loading activities and their related widgets etc.
"""

from datetime import datetime
import json
from pathlib import Path
import pandas as pd
from .activities import Activity
from tracks.plot import PlotWidget
from tracks.data import Data, DataViewer, PersonalBests, AddData
from tracks.util import parse_month_range
from qtpy.QtCore import QObject, Signal, Slot
from customQObjects.core import Settings


class ActivityObjects(QObject):
    
    request_save_activity = Signal(str)
    
    def __init__(self, activity, data, data_viewer, add_data, personal_bests, plot):
        super().__init__()
        
        self.activity = activity
        self.data = data
        self.data_viewer = data_viewer
        self.add_data = add_data
        self.personal_bests = personal_bests
        self.plot = plot
        
        self._connect_signals()
        
    def _connect_signals(self):
        self.add_data.newData.connect(self.data.append)
        self.plot.point_selected.connect(self.data_viewer.highlightItem)
        self.data_viewer.itemSelected.connect(self.plot.set_current_point_from_date)
        self.personal_bests.itemSelected.connect(self.plot.set_current_point_from_date)
        self.data.dataChanged.connect(self._data_changed)
        
    @Slot(object)
    def _data_changed(self, idx):
        self.data_viewer.newData(idx)
        self.plot.new_data(idx)
        self.personal_bests.newData(idx)
        self.request_save_activity.emit(self.activity.name)


class ActivityManager(QObject):
    
    status_message = Signal(str)
    
    csv_sep = ","
    
    def __init__(self, p: Path, settings: Settings):
        super().__init__()
        
        if not p.exists():
            raise FileNotFoundError(f"ActivityManager directory '{p}' does not exist")
        self._data_path = p
        self._settings = settings
        self._activities = {}
        self._current_activity = None
        
    @property
    def current_activity(self) -> Activity:
        """ Return current `Activity` """
        return self._current_activity
    
    def get_activity_objects(self, name: str) -> ActivityObjects:
        """ Return namedtuple of objects associated with `name` """
        try:
            return self._activities[name]
        except KeyError: 
            msg = f"No activity '{name}'. \n"
            msg += f"Available activities are: {','.join(self._activities.keys())}"
            raise KeyError(msg)
    
    def load_activity(self, name: str) -> ActivityObjects:
        """ 
        Load activity `name` and set as `current_activity`. 
        
        Return objects associated with `name`
        """
        if name in self._activities:
            return self._activities[name]
        
        p = self._data_path.joinpath(f"{name}.json")
        if not p.exists():
            msg = f"No such activity '{name}'\n"
            msg += f"Valid activities are: {', '.join(self.list_activities())}"
            raise ValueError(msg)
        
        with open(p, "r") as fileobj:
            activity_json = json.load(fileobj)
            
        activity = Activity(activity_json['name'])
        for measure in activity_json['measures'].values():
            activity.add_measure(**measure)
            
        activity_objects = self._initialise_activity(activity)
        self._activities[name] = activity_objects
        self._current_activity = activity_objects.activity
        
        self.save_activity(name)
            
        return activity_objects
    
    def _initialise_activity(self, activity: Activity) -> ActivityObjects:
        """ Initialise objects for the given activity and return `ActivityObjects` """
        
        df = self._load_actvity_df(activity)
        data = Data(df, activity)

        add_data = AddData(activity)
        
        numTopSessions = self._settings.value("pb/numSessions", 5, int)
        monthCriterion = self._settings.value("pb/bestMonthCriterion", "distance")
        sessionsKey = self._settings.value("pb/sessionsKey", "speed")
        pb = PersonalBests(
            data, 
            activity,
            numSessions=numTopSessions, 
            monthCriterion=monthCriterion,
            sessionsKey=sessionsKey)
        
        viewer = DataViewer(data, activity)
        
        plot_style = self._settings.value("plot/style", "dark")
        month_range = parse_month_range(self._settings.value("plot/range", "All"))
        y_series = self._settings.value("plot/current_series", "time")
        plot = PlotWidget(
            data, 
            activity,
            style=plot_style, 
            months=month_range,
            y_series=y_series)
        
        objects = ActivityObjects(activity, data, viewer, add_data, pb, plot)
        
        objects.request_save_activity.connect(self.save_activity)
        
        return objects
    
    def list_activities(self):
        json_files = [f.stem for f in self._data_path.iterdir() if f.suffix == ".json"]
        return  json_files
            
    def _load_actvity_df(self, activity: Activity) -> pd.DataFrame:
        """ Load dataframe for `activity` """
        
        filepath = self._activity_csv_file(activity)
        
        if not filepath.exists():
            header = activity.header
            s = self.csv_sep.join(header) + "\n"
            with open(filepath, 'w') as fileobj:
                fileobj.write(s)
                
        df = pd.read_csv(filepath, sep=self.csv_sep, parse_dates=['date'])
        
        return df
    
    def _activity_csv_file(self, activity: Activity, raise_not_exist=False):
        fname = f"{activity.name.lower()}.csv"
        filepath = self._data_path.joinpath(fname)
        if raise_not_exist and not filepath.exists():
            raise FileNotFoundError(f"csv file for activity '{activity.name}' not found")
        return filepath
    
    def save_activity(self, activity_name: str=None):
        """ Save activity data to csv and backup """
        if activity_name is None:
            activity_name = self.current_activity.name
            
        activity = self._activities[activity_name]
        filepath = self._activity_csv_file(activity.activity)
        
        activity.data.df.to_csv(filepath, sep=self.csv_sep, index=False)
        self.backup_activity(activity_name)
        
        save_time = datetime.now().strftime("%H:%M:%S")
        msg = f"Last saved at {save_time}"
        self.status_message.emit(msg)
        
    def backup_activity(self, activity_name: str=None):
        """ Backup activity csv file """
        if activity_name is None:
            activity_name = self.current_activity.name
            
        activity = self._activities[activity_name]
        filepath = self._activity_csv_file(activity.activity)
        
        bak = filepath.with_suffix('.bak')
        
        activity.data.df.to_csv(bak, sep=self.csv_sep, index=False)