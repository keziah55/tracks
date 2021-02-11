#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Make a pandas DataFrame of random cycling data.
"""

import pandas as pd
import numpy as np
import time

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
    
    
def makeDates(size, startDate="2018-01-01", endDate="2021-12-31", fmt="%Y-%m-%d"):
    
    startDate += " 00:00"
    endDate += " 23:59"
    tfmt = fmt + " %H:%M"
    start = time.mktime(time.strptime(startDate, tfmt))
    end = time.mktime(time.strptime(endDate, tfmt))
    
    diff = end-start
    
    rng = np.random.default_rng()
    times = [start + r*diff for r in rng.random(size)]
    dates = [time.strftime(fmt, time.localtime(t)) for t in sorted(times)]
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
    