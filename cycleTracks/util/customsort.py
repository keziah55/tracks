#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Functions used by CycleTreeWidgetItem and AddCycleData to sort data.
"""

import calendar

def isNumeric(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def isMonthYear(value):
    try:
        getMonthYear(value)
        return True
    except ValueError:
        return False
    
def isHourMinSec(value):
    try:
        getHourMinSec(value)
        return True
    except ValueError:
        return False
    
def getMonthYear(value):
    month, year = value.split(' ')
    try:
        idx = list(calendar.month_name).index(month)
    except ValueError:
        try:
            idx = list(calendar.month_abbr).index(month)
        except ValueError:
            raise ValueError(f"{month} is not valid month")
    year = float(year)
    
    value = year + (idx/12)
    
    return value

def getHourMinSec(value):
    hours, minssec = value.split(':')
    mins, secs = minssec.split('.')
    value = float(hours) + (float(mins)/60) + (float(secs)/3600)
    return value

def getDateMonthYear(value):
    date, month, year = value.split(' ')
    try:
        idx = list(calendar.month_name).index(month)
    except ValueError:
        try:
            idx = list(calendar.month_abbr).index(month)
        except ValueError:
            raise ValueError(f"{month} is not valid month")
    year = float(year)
    date = float(date)/31
    
    value = year + (idx/12) + date
    
    return value