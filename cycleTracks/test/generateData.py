#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Make a pandas DataFrame of random cycling data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date

def timeToSecs(t):
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

def convertSecs(t, mode='hour'):
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

def makeDataFrame(size=100, path=None):
    """ Return DataFrame of random cycling data.
    
        Parameters
        ----------
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
    d = {'Date':makeDates(size),
         'Time':makeTimes(size),
         'Distance (km)':makeFloats(size, 3, 80, ".2f"),
         'Calories':makeFloats(size, 50, 1200, ".1f"),
         'Gear':np.random.default_rng().integers(1, 8, size=size)}
    
    times = np.array([convertSecs(timeToSecs(t)) for t in d['Time']])
    d['Avg. speed (km/h)'] = d['Distance (km)'] / times
    
    df = pd.DataFrame.from_dict(d)
    
    if path is not None:
        df.to_csv(path, index=False)
    
    return df
    
    
def makeDates(size, startDate=None, endDate=None, fmt="%Y-%m-%d"):
    """ Return list of `size` random dates, between `startDate` and `endDate`.
    
        Parameters
        ----------
        size : int
            Number of random dates to generate
        startDate : str, optional
            Start of range of random dates. If provided, should be string in 
            format `fmt`. Default is current date minus two years.
        endDate : str, optional
            End of range of random dates. If provided, should be string in 
            format `fmt`. Default is current date.
        fmt : str, optional
            If `startDate` and `endDate` strings are provided, this arg should
            give their format. Default is "%Y-%m-%d".
            
        Returns
        -------
        dates : list
            list of datetime objects
    """
    if endDate is None:
        endDate = date.today().strftime(fmt)
    if startDate is None:
        today = date.today()
        d = date(year=today.year-2, month=today.month, day=today.day)
        startDate = d.strftime(fmt)
    
    start = datetime.strptime(startDate, fmt)
    dt = datetime.strptime(endDate, fmt) - datetime.strptime(startDate, fmt)
    diff = dt.days
    
    rng = np.random.default_rng()
    days = rng.choice(np.arange(diff), size=size, replace=False, shuffle=False)
    days = np.sort(days)
    dates = [start + timedelta(days=int(d)) for d in days]
    return dates


def makeTimes(size, minMinutes=10, maxMinutes=150):
    """ Return list of `size` random times, between `minMinutes` and `maxMinutes`. 
    
        Times will be returned as strings in the format "%H:%M:%S" or "%M:%S", if
        hours is 0.
        
        Parameters
        ----------
        size : int
            Number of random times to generate
        minMinutes : int
            Lower value of minutes to generate times between. Default is 10.
        maxMinutes : int
            Upper value of minutes to generate times between. Default is 150.
            
        Returns
        -------
        times : list
            list of time strings
    """
    def _makeTimeString(s):
        mins, secs = divmod(s, 60)
        hours, mins = divmod(mins, 60)
        t = f"{hours:02d}:" if hours != 0 else ""
        t += f"{mins:02d}:{secs:02d}"
        return t
        
    rng = np.random.default_rng()
    seconds = rng.integers(minMinutes*60, high=maxMinutes*60, size=size)
    times = [_makeTimeString(s) for s in seconds]
    return times


def makeFloats(size, minValue, maxValue, fmt):
    """ Return list of random floats, as formatted strings. 
    
        Parameters
        ----------
        size : int
            Number of random times to generate
        minValue : float
            Lower limit to generate numbers between
        maxValue : float
            Upper limit to generate numbers between
        fmt : str
            String format specifier for the floats.
            
        Returns
        -------
        floats : list
            list of formatted float strings
    """
    diff = maxValue - minValue
    rng = np.random.default_rng()
    floats = [minValue + r*diff for r in rng.random(size)]
    floats = [float(f"{value:{fmt}}") for value in floats]
    return floats
    