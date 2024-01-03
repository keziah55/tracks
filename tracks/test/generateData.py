#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Make a pandas DataFrame of random cycling data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from tracks.util import hourMinSecToFloat

def time_to_secs(t):
    msg = ''
    # don't actually need the datetime objects returned by strptime, but 
    # this is probably the easist way to check the format
    try:
        datetime.strptime(t, "%H:%M:%S")
        hr, mins, sec = [int(s) for s in t.split(':')]
    except ValueError:
        try:
            datetime.strptime(t, "%M:%S")
            mins, sec = [int(s) for s in t.split(':')]
            hr = 0
        except ValueError:
            msg = f"Could not format time '{t}'"
    if msg:
        raise ValueError(msg)
    
    total = sec + (60*mins) + (60*60*hr)
    return total

def convert_secs(t, mode='hour'):
    minutes = ['m', 'min', 'mins', 'minutes']
    hours = ['h', 'hr', 'hour', 'hours']
    valid = minutes + hours
    if mode not in valid:
        msg = f"Mode '{mode}' not in valid modes: {valid}"
        raise ValueError(msg)
    m = t / 60
    if mode in minutes:
        return m
    h = m / 60
    if mode in hours:
        return h

def make_dataframe(random=True, size=100, path=None):
    """ Return DataFrame of random cycling data.
    
        Parameters
        ----------
        random : bool
            If True, generate random data. Otherwise use pre-set data. Default 
            is True.
        size : int, optional
            Length of DataFrame to generate. The default is 100.
        path : str, optional
            If provided, the DataFrame will be written to file at `path`. 
            The default is None.
    
        Returns
        -------
        df : pandas.DataFrame
            DataFrame of random data
    """
    if random:
        d = random_data(size)
    else:
        d = known_data()
    
    df = pd.DataFrame.from_dict(d)
    
    if path is not None:
        df.to_csv(path, index=False)
    
    return df
    
def random_data(size):
    d = {'Date':make_dates(size),
         'Time':make_times(size),
         'Distance (km)':make_floats(size, 3, 80, ".2f"),
         'Calories':make_floats(size, 50, 1200, ".1f"),
         'Gear':np.random.default_rng().integers(1, 8, size=size)}
    
    speed = d['Distance (km)'] / np.array([convert_secs(time_to_secs(t)) for t in d['Time']])
    d['Speed (km/h)'] = speed
    
    return d

def known_data():
    dates = [f"2021-04-{i:02}" for i in range(26, 31)]
    dates += [f"2021-05-{i:02}" for i in range(1, 6)] 
    dct = {'Date':dates,
            'Time':["00:53:27", "00:43:04", "00:42:40", "00:43:09", "00:42:28",
                    "00:43:19", "00:42:21", "00:43:04", "00:42:11", "00:43:25"],
            'Distance (km)':[30.1, 25.14, 25.08, 25.41, 25.1, 25.08, 25.13, 
                            25.21, 25.08, 25.12],
            'Gear':[6]*10}
    dct['Calories'] = [d*14.956 for d in dct['Distance (km)']]
    times = np.array([hourMinSecToFloat(t) for t in dct['Time']])
    dct['Speed (km/h)'] = dct['Distance (km)'] / times
    return dct

def make_dates(size, start_date=None, end_date=None, fmt="%Y-%m-%d", include_bounds=True):
    """ Return list of `size` random dates, between `start_date` and `end_date`.
    
        Parameters
        ----------
        size : int
            Number of random dates to generate
        start_date : str, optional
            Start of range of random dates. If provided, should be string in 
            format `fmt`. Default is current date minus two years.
        end_date : str, optional
            End of range of random dates. If provided, should be string in 
            format `fmt`. Default is current date.
        fmt : str, optional
            If `start_date` and `end_date` strings are provided, this arg should
            give their format. Default is "%Y-%m-%d".
        include_bounds : bool
            If True (default), `start_date` and `end_date` will always be included.
        Returns
        -------
        dates : list
            list of datetime objects
    """
    if end_date is None:
        end_date = date.today().strftime(fmt)
    if start_date is None:
        today = date.today()
        d = date(year=today.year-2, month=today.month, day=today.day)
        start_date = d.strftime(fmt)
    
    start = datetime.strptime(start_date, fmt)
    dt = datetime.strptime(end_date, fmt) - datetime.strptime(start_date, fmt)
    diff = dt.days
    
    if include_bounds:
        size -= 2
    rng = np.random.default_rng()
    days = rng.choice(np.arange(diff), size=size, replace=False, shuffle=False)
    days = np.sort(days)
    dates = [start + timedelta(days=int(d)) for d in days]
    if include_bounds:
        dates.insert(0, start_date)
        dates.append(end_date)
    return dates

def make_times(size, min_minutes=10, max_minutes=150):
    """ Return list of `size` random times, between `min_minutes` and `max_minutes`. 
    
        Times will be returned as strings in the format "%H:%M:%S" or "%M:%S", if
        hours is 0.
        
        Parameters
        ----------
        size : int
            Number of random times to generate
        min_minutes : int
            Lower value of minutes to generate times between. Default is 10.
        max_minutes : int
            Upper value of minutes to generate times between. Default is 150.
            
        Returns
        -------
        times : list
            list of time strings
    """
    def _make_time_string(s):
        mins, secs = divmod(s, 60)
        hours, mins = divmod(mins, 60)
        t = f"{hours:02d}:" if hours != 0 else ""
        t += f"{mins:02d}:{secs:02d}"
        return t
        
    rng = np.random.default_rng()
    seconds = rng.integers(min_minutes*60, high=max_minutes*60, size=size)
    times = [_make_time_string(s) for s in seconds]
    return times

def make_floats(size, min_value, max_value, fmt):
    """ Return list of random floats, as formatted strings. 
    
        Parameters
        ----------
        size : int
            Number of random times to generate
        min_value : float
            Lower limit to generate numbers between
        max_value : float
            Upper limit to generate numbers between
        fmt : str
            String format specifier for the floats.
            
        Returns
        -------
        floats : list
            list of formatted float strings
    """
    diff = max_value - min_value
    rng = np.random.default_rng()
    floats = [min_value + r*diff for r in rng.random(size)]
    floats = [float(f"{value:{fmt}}") for value in floats]
    return floats
    