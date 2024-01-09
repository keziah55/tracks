#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""
import pandas as pd

class ActivityManager:
    def load_activity(p):
        """ Load activity from pickled file `p` """
        with open(p, "r") as fileobj:
            activity_json = json.load(fileobj)
            
        activity = Activity(activity_json['name'])
        for name, measure in activity_json['measures'].items():
            activity.add_measure(**measure)
            
        return activity
    
    def list_activities(p):
        with open(p.joinpath("all_activities.json")) as fileobj:
            activity_json = json.load(fileobj)
            
    def get_activity_csv(activity):
        """ Return path for csv file of data for `activity` """
        p = get_data_path()
        filepath = p.joinpath(activity.csv_file)
        return filepath
    
    def load_actvity_df(activity, csv_sep=",") -> pd.DataFrame:
        """ Load dataframe for `activity` """
        
        filepath = get_activity_csv(activity)
        
        if not filepath.exists():
            header = activity.header
            s = csv_sep.join(header) + "\n"
            with open(filepath, 'w') as fileobj:
                fileobj.write(s)
                
        df = pd.read_csv(filepath, sep=csv_sep, parse_dates=['date'])
        
        return df