#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Object to manage loading activities and their related widgets etc.
"""

from collections import namedtuple
import json
from pathlib import Path
import pandas as pd
from .activities import Activity
from tracks.plot import PlotWidget
from tracks.data import Data, DataViewer, PersonalBests, AddData
from tracks.util import parse_month_range
from customQObjects.core import Settings


ActivityObjects = namedtuple(
    "ActivityObjects", 
    ["activity", "data", "data_viewer", "add_data", "personal_bests", "plot"]
)

class ActivityManager:
    
    csv_sep = ","
    
    def __init__(self, p: Path, settings: Settings):
        
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
    
    def get_activity_objects(self, name) -> ActivityObjects:
        """ Return namedtuple of objects associated with `name` """
        try:
            return self._activities[name]
        except KeyError: 
            msg = f"No activity '{name}'. \n"
            msg += f"Available activities are: {','.join(self._activities.keys())}"
            raise KeyError(msg)
    
    def load_activity(self, name) -> ActivityObjects:
        """ 
        Load activity `name` and set as `current_activity`. 
        
        Return namedtuple of objects associated with `name`
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
    
    def _initialise_activity(self, activity) -> ActivityObjects:
        """ Initialise objects for the given activity and return in named tuple """
        
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
        
        add_data.newData.connect(data.append)
        plot.point_selected.connect(viewer.highlightItem)
        viewer.itemSelected.connect(plot.set_current_point_from_date)
        pb.itemSelected.connect(plot.set_current_point_from_date)
        
        objects = ActivityObjects(activity, data, viewer, add_data, pb, plot)
        return objects
    
    def list_activities(self):
        json_files = [f.stem for f in self._data_path.iterdir() if f.suffix == ".json"]
        return  json_files
            
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
            activity_name = self.current_activity.name
            
        activity = self._activities[activity_name]
        filepath = self._activity_csv_file(activity.activity)
        
        activity.data.df.to_csv(filepath, sep=self.csv_sep, index=False)
        self.backup_activity(activity_name)
        
    def backup_activity(self, activity_name:str=None):
        """ Backup activity csv file """
        if activity_name is None:
            activity_name = self.current_activity.name
            
        activity = self._activities[activity_name]
        filepath = self._activity_csv_file(activity.activity)
        
        bak = filepath.with_suffix('.bak')
        
        activity.data.df.to_csv(bak, sep=self.csv_sep, index=False)