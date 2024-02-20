#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Object to manage loading activities and their related widgets etc.
"""

from datetime import datetime
import json
import pandas as pd
from .activities import Activity
from tracks import get_data_path
from tracks.plot import PlotWidget
from tracks.data import Data, DataViewer, PersonalBests, AddData
from tracks.preferences import DataPreferences, PlotPreferences
from tracks.util import parse_month_range
from qtpy.QtCore import QObject, Signal, Slot

def default_current_activity(func):
    def wrapped(self, activity_name=None, **kwargs):
        if activity_name is None:
            activity_name = self.current_activity.name
        return func(self, activity_name, **kwargs)
    return wrapped

class ActivityObjects(QObject):
    
    request_save_activity = Signal(str)
    
    status_message = Signal(str)
    
    def __init__(self, activity, data, data_viewer, add_data, personal_bests, plot):
        super().__init__()
        
        self.activity = activity
        self.data = data
        self.data_viewer = data_viewer
        self.add_data = add_data
        self.personal_bests = personal_bests
        self.plot = plot
        self.preferences = {
            "data": DataPreferences(activity, personal_bests),
            "plot": PlotPreferences(activity, plot),
        }
        
        self._connect_signals()
        
    def _connect_signals(self):
        self.add_data.newData.connect(self.data.append)
        self.plot.point_selected.connect(self.data_viewer.highlightItem)
        self.data_viewer.itemSelected.connect(self.plot.set_current_point_from_date)
        self.personal_bests.itemSelected.connect(self.plot.set_current_point_from_date)
        
        self.data.dataChanged.connect(self._data_changed)
        self.data_viewer.selectedSummary.connect(self.status_message)
        self.personal_bests.statusMessage.connect(self.status_message)
        
        self.preferences["data"].applied.connect(self._apply_data_pref)
        self.preferences["plot"].applied.connect(self._apply_plot_pref)
        
    @Slot(object)
    def _data_changed(self, idx):
        self.data_viewer.new_data(idx)
        self.plot.new_data(idx)
        self.personal_bests.new_data(idx)
        self.request_save_activity.emit(self.activity.name)
        
    def _apply_data_pref(self, summary_changed):
        if summary_changed:
            self.data_viewer.updateTopLevelItems()
            self.request_save_activity.emit(self.activity.name)
            # self.personal_bests.new_data() ## is this necessary?
            
    def _apply_plot_pref(self, *args, **kwargs):
        self.request_save_activity.emit(self.activity.name)


class ActivityManager(QObject):
    
    status_message = Signal(str)
    
    csv_sep = ","
    
    def __init__(self):
        super().__init__()
        
        p = get_data_path()
        if not p.exists():
            raise FileNotFoundError(f"ActivityManager directory '{p}' does not exist")
        self._data_path = p
        self._json_path = self._data_path.joinpath("activities.json")
        self._activities = {}
        self._current_activity = None
        
    def _activities_json(self) -> dict:
        """ Return dict of all activity info """
        if not self._json_path.exists():
            all_activities = {}
        else:
            with open(self._json_path, 'r') as fileobj:
                all_activities = json.load(fileobj)
        return all_activities
    
    def _write_activities_json(self, all_activities):
        """ Write dict of data for all activities to json """
        with open(self._json_path, 'w') as fileobj:
            json.dump(all_activities, fileobj, indent=4)
        
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
                    
        activity_json = self._activities_json().get(name, None)
        if activity_json is None:
            msg = f"No such activity '{name}'\n"
            msg += f"Valid activities are: {', '.join(self.list_activities())}"
            raise ValueError(msg)
            
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
        pref = self._get_activity_preferences(activity.name)
        
        data = Data(df, activity)

        add_data = AddData(activity)
        
        pb_pref = pref.get("personal_bests", {})
        num_best_sessions = pb_pref.get("num_best_sessions", 5) 
        sessions_key = pb_pref.get("sessions_key", "speed")
        pb = PersonalBests(
            data, 
            activity,
            num_sessions=num_best_sessions, 
            sessions_key=sessions_key,
        )
        
        viewer = DataViewer(data, activity)
        
        plot_pref = pref.get("plot", {})
        plot_style = plot_pref.get("style", "dark")
        month_range = plot_pref.get("default_months", "All")
        if isinstance(month_range, str):
            month_range = parse_month_range(month_range)
        y_series = plot_pref.get("current_series", "time")
        plot = PlotWidget(
            data, 
            activity,
            style=plot_style, 
            months=month_range,
            y_series=y_series)
        
        activity_objects = ActivityObjects(activity, data, viewer, add_data, pb, plot)
        activity_objects.status_message.connect(self.status_message)
        activity_objects.request_save_activity.connect(self.save_activity)
        
        return activity_objects
    
    def list_activities(self):
        all_activities = self._activities_json()
        return list(all_activities.keys())
            
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
    
    @default_current_activity
    def save_activity(self, activity_name: str=None):
        """ Save activity data to csv and backup """
        # save csv
        activity = self._activities[activity_name]
        filepath = self._activity_csv_file(activity.activity)
        
        # backup csv
        activity.data.df.to_csv(filepath, sep=self.csv_sep, index=False)
        self.backup_activity(activity_name)
        
        # save settings for this activity
        self._activity_to_json()
        
        save_time = datetime.now().strftime("%H:%M:%S")
        msg = f"Last saved at {save_time}"
        self.status_message.emit(msg)
        
    @default_current_activity
    def backup_activity(self, activity_name: str=None):
        """ Backup activity csv file """
        activity = self._activities[activity_name]
        filepath = self._activity_csv_file(activity.activity)
        
        bak = filepath.with_suffix('.bak')
        
        activity.data.df.to_csv(bak, sep=self.csv_sep, index=False)
        
    @default_current_activity
    def _activity_to_json(self, activity_name: str=None):
        """ Update `activity_name` in json file. """
        activity_objects = self._activities[activity_name]
        
        activity_json = activity_objects.activity.to_json()
        
        preferences_json = {}
        preferences_json["plot"] = activity_objects.plot.state()
        preferences_json["personal_bests"] = activity_objects.personal_bests.state()
        
        activity_json.update(
            {
                "preferences":preferences_json,
            }
        )
        
        all_activities = self._activities_json()
        all_activities[activity_name] = activity_json
        self._write_activities_json(all_activities)
        
    @default_current_activity
    def _get_activity_preferences(self, activity_name: str=None) -> dict:
        """ Read preferences for `activity_name` from json """
        all_activities = self._activities_json()
        try:
            pref = all_activities[activity_name]["preferences"]
        except KeyError:
            pref = {}
        return pref
        