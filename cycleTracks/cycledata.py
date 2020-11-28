#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 28 19:25:42 2020

@author: keziah
"""

from datetime import datetime
import numpy as np


class CycleData:
    
    def __init__(self, df):
        """ Object providing convenience functions for accessing data from 
            a given DataFrame of cycling data.
        """
        self.df = df
        
    @staticmethod
    def _timeToSecs(t):
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
    
    @staticmethod
    def _convertSecs(t, mode='hour'):
        valid = ['mins', 'hour']
        if mode not in valid:
            msg = f"Mode '{mode}' not in valid modes: {valid}"
            raise ValueError(msg)
        m = t / 60
        if mode == 'mins':
            return m
        h = m / 60
        if mode == 'hour':
            return h
        
    @property
    def distance(self):
        """ Return 'Distance (km)' column as numpy array. """
        return np.array(self.df['Distance (km)'])
    
    @property
    def time(self):
        return list(self.df['Time'])
    
    @property
    def date(self):
        return list(self.df['Date'])
    
    @property
    def calories(self):
        return np.array(self.df['Calories'])
    
    @property
    def timeSecs(self):
        """ Return numpy array of 'Time' column, where each value is converted
            to seconds.
        """
        time = [self._timeToSecs(t) for t in self.df['Time']]
        time = np.array([self._convertSecs(s) for s in time])
        return time
    
    @property
    def dateTimestamps(self):
        """ Return 'Date' column, converted to array of timestamps (time since 
            epoch).
    
            See also: :py:meth:`datetimes`.
        """
        return np.array([dt.timestamp() for dt in self.datetimes])

    @property
    def datetimes(self):
        """ Return 'Date' column, converted to list of datetime objects. """
        return [datetime.strptime(d, "%Y-%m-%d") for d in self.df['Date']]
    
    def _getMonthlyOdometer(self):
        """ Return list of datetime objects and list of floats.
            
            The datetime objects are required, as they add dummy 1st of the 
            month data points to reset the total to 0km.
        """
        
        odo = []
        dts = []
            
        for i, dt in enumerate(self.datetimes):
            if i == 0 or self.datetimes[i-1].month != dt.month:
                tmp = datetime(self.datetimes[i].year, self.datetimes[i].month, 1)
                dts.append(tmp)
                prev = 0
                odo.append(prev)
            else:
                prev = odo[-1]
            dts.append(dt)
            odo.append(prev + self.distance[i-1])
        
        return dts, odo
    