#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""

from collections import namedtuple
import json
from pathlib import Path
import pandas as pd
from .activities import Activity
from .plot import PlotWidget
from .data import Data, DataViewer, PersonalBests
from tracks.util import parse_month_range

ActivityObjects = namedtuple(
    "ActivityObjects", 
    ["activity", "data", "data_viewer", "personal_bests", "plot"]
)

class ActivityManager:
    
    csv_sep = ","
    
    def __init__(self, p: Path):
        
        if not p.exists():
            raise FileNotFoundError(f"ActivityManager directory '{p}' does not exist")
        self._data_path = p
        self._activities = {}
        self._current_activity = None
        
    @property
    def current_activity(self):
        return self._current_activity
    
    def load_activity(self, name, settings):
        """ Load activity `name` and set as `current_activity` """
        
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
            
        activity_objects = self._initialise_activity(activity, settings)
        self._activities[name] = activity_objects
        self._current_activity = name
        
        self._save_activity(name)
            
        return activity_objects
    
    def _initialise_activity(self, activity, settings) -> ActivityObjects:
        """ Initialise objects for the given activity and return in named tuple """
        
        df = self._load_actvity_df(activity)
        data = Data(df, activity)
        # TODO save
        
        numTopSessions = settings.value("pb/numSessions", 5, int)
        monthCriterion = settings.value("pb/bestMonthCriterion", "distance")
        sessionsKey = settings.value("pb/sessionsKey", "speed")
        pb = PersonalBests(
            data, 
            activity,
            numSessions=numTopSessions, 
            monthCriterion=monthCriterion,
            sessionsKey=sessionsKey)
        
        viewer = DataViewer(data, activity)
        
        plot_style = settings.value("plot/style", "dark")
        month_range = parse_month_range(settings.value("plot/range", "All"))
        y_series = settings.value("plot/current_series", "time")
        plot = PlotWidget(
            data, 
            activity,
            style=plot_style, 
            months=month_range,
            y_series=y_series)
        
        objects = ActivityObjects(activity, data, viewer, pb, plot)
        return objects
    
    def list_activities(self):
        # TODO
        with open(self._data_path.joinpath("all_activities.json")) as fileobj:
            activity_json = json.load(fileobj)
            
    def _load_actvity_df(self, activity) -> pd.DataFrame:
        """ Load dataframe for `activity` """
        
        filepath = self._activity_csv_file(activity)
        
        if not filepath.exists():
            header = activity.header
            s = self.csv_sep.join(header) + "\n"
            with open(filepath, 'w') as fileobj:
                fileobj.write(s)
                
        df = pd.read_csv(filepath, sep=self.csv_sep, parse_dates=['date'])
        
        return df
    
    def _activity_csv_file(self, activity, raise_not_exist=False):
        fname = f"{activity.name.lower()}.csv"
        filepath = self._data_path.joinpath(fname)
        if raise_not_exist and not filepath.exists():
            raise FileNotFoundError(f"csv file for activity '{activity.name}' not found")
        return filepath
    
    def save_activity(self, activity_name:str=None):
        """ Save activity data to csv and backup """
        if activity_name is None:
            activity_name = self.current_activity
            
        activity = self._activities[activity_name]
        filepath = self._activity_csv_file(activity)
        
        activity.data.df.to_csv(filepath, sep=self._csv_sep, index=False)
        self._backup_activity(activity_name)
        
    def backup_activity(self, activity_name:str=None):
        """ Backup activity csv file """
        if activity_name is None:
            activity_name = self.current_activity
            
        activity = self._activities[activity_name]
        filepath = self._activity_csv_file(activity)
        
        bak = filepath.with_suffix('.bak')
        
        activity.data.data.df.to_csv(bak, sep=self.csv_sep, index=False)