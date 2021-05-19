#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Make a pandas DataFrame of random cycling data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date

def makeDataFrame(size=100, path=None):
    
    d = {'Date':makeDates(size),
         'Time':makeTimes(size),
         'Distance (km)':makeFloats(size, 3, 80, ".2f"),
         'Calories':makeFloats(size, 50, 1200, ".1f"),
         'Gear':np.random.default_rng().integers(1, 8, size=size)}
    
    df = pd.DataFrame.from_dict(d)
    
    if path is not None:
        df.to_csv(path, index=False)
    
    return df
    
    
def makeDates(size, startDate=None, endDate=None, fmt="%Y-%m-%d"):
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
    
    diff = maxValue - minValue
    rng = np.random.default_rng()
    floats = [minValue + r*diff for r in rng.random(size)]
    floats = [float(f"{value:{fmt}}") for value in floats]
    return floats
    