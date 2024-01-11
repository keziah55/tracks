#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
`parseDuration` and `parseDate` convert a given string into a 'hh:mm:ss' string
and a datetime.date/pandas.Timestamp object, respectively.

The remaining three functions convert time or date strings into floats, so values
can be sorted.
"""

from datetime import date, datetime
import calendar
import re
import pandas as pd

def parse_month_range(s) -> int:
    """ 
    Parse string into int number of months.
    
    |        s       |            Return           |
    |:--------------:|:---------------------------:|
    |  "[X] months"  |              X              |
    |    "1 year"    |              12             |
    | "current year" | datetime.date.today().month |
    |      "all"     |             None            |
    """
    s = s.lower()
    if s == "1 year":
        s = "12 months"
    elif s == "current year":
        s = f"{date.today().month} months"
    months = None if s == 'all' else int(s.strip(' months'))
    return months

def parseDuration(value):
    """ Convert string `value`, which should be a time in [hh]:mm:[ss] format,
        into hh:mm:ss format.
    """
    values = value.split(':')
    if not all([v.isdigit() for v in values]) or len(values) > 3:
        raise ValueError(f"{value} is not a time in [hh]:mm:[ss] format.")
    if len(values) == 1:
        mins = int(values[0])
        hours, secs = 0, 0
    elif len(values) == 2:
        mins, secs = [int(v) for v in values]
        hours, mins = divmod(mins, 60)
    else:
        hours, mins, secs = [int(v) for v in values]
        
    s = f"{hours:02.0f}:{mins:02.0f}:{secs:02.0f}"
    return s

def parseDate(value, pd_timestamp=False):
    """ Convert string to datetime.date object (or pandas.Timestamp, if 
    `pd_timestamp` is True).
    
    Will take any reasonable date string (in Day-Month-Year order) and convert
    it to a datetime.date object (in Year-Month-Day order). 
    If incomplete information is given, the current day/month/year/century will
    be used by default.
    
    * If an empty/whitespace string is provided, the current date will be
      returned.

    * 'Year' can be either two or four digits. If two digits, 21st century will 
      be assumed.
    
    * The string can have no delimiters (i.e. 'DDMMYY' or 'DDMMYYYY') or can 
      use '-', '/', '.' or a space. 
    
    * The month can be given as a name or number. The name can the the full 
      name or three letter abbreviation.
    
    * If only one number is provided, it is taken to be the day and the
      current month and year will be assumed. Similarly, two numbers
      will be taken to be day and month and current year will be assumed.
      (Note that this only works if a delimiter is used.)
    
    Examples
    --------
    >>> parseDate('02 Mar 17')
    datetime.date(2017, 3, 2)
    
    >>> parseDate('04 April 17')
    datetime.date(2017, 4, 4)
    
    >>> parseDate('4/8/15')
    datetime.date(2015, 8, 4)
    
    >>> parseDate('4-8-2015')
    datetime.date(2015, 8, 4)
    
    >>> parseDate('')
    datetime.date(2017, 9, 28)   # current date at time of writing
    
    >>> parseDate('3')
    datetime.date(2017, 9, 3)    # time of writing was September 2017
    
    >>> parseDate('5.5')
    datetime.date(2017, 5, 5)    # time of writing was September 2017
    
    >>> parseDate('020312')
    datetime.date(12, 3, 2)
    
    >>> parseDate('02032012')
    datetime.date(2012, 3, 2)
    """
    
    if not isinstance(value, str):
        raise TypeError(f"Cannot format '{value}' as date. Input should be a string.")
    
    # make dictionary of month names and abbreviations : number
    c_abbr = {v: k for k,v in enumerate(calendar.month_abbr)}
    c_full = {v: k for k,v in enumerate(calendar.month_name)}
    months = {**c_abbr, **c_full}
    
    # remove {'':0} from dictionary
    del months['']
    
    # get current date and use as default output
    today = date.today()
    d = [today.year, today.month, today.day]
    
    # if input is empty string, return current date
    value = value.strip()
    if not value:
        ret = today
        if pd_timestamp:
            # cast to pandas.Timestamp, if requested
            ret = pd.Timestamp(ret)
        return ret
    
    l = re.split(r'[\s/.-]', value)
    
    # if a single value was given as input...
    if len(l) == 1:
        # ... if value is DDMMYY or DDMMYYYY, split into parts
        if len(value) == 6 or len(value) == 8:
            l = [value[:2], value[2:4], value[4:]]
        # ... if value is none of the above, raise exception
        elif len(value) not in [1,2]: # ... if value is Day, nothing needs to be done
            raise ValueError('Cannot format given date.')
    
    # substitute given input values (l) into list with current date (d)
    for n in range(len(l)):
        try:
            # input in Day-Month-Year order, which needs to be reversed
            d[-(n+1)] = int(l[n])
        except ValueError:
            msg = 'Please check given string.'
            
            # if month isn't a number, check if it's in the dictionary
            try:
                d[-(n+1)] = months[l[n]]
            except KeyError:
                msg = 'Please check given month.'
                raise ValueError(f'Cannot format "{value}" as date. {msg}')
    
    # if only two digits were given for the year, assume current century    
    if len(str(d[0])) == 2:
        d[0] += today.year - (today.year % 100)
        
    # return value
    ret = date(*d)
    if pd_timestamp:
        # cast to pandas.Timestamp, if requested
        ret = pd.Timestamp(ret)
        
    return ret

def floatToHourMinSec(value) -> str:
    """ Convert a float of hours into hh:mm:ss. 
    
        Inverse of `hourMinSecToFloat`.
    """
    hours, minssecs = divmod((value*60), 60)
    mins, secs = divmod((minssecs*60), 60)
    s = f"{hours:02.0f}:{mins:02.0f}:{secs:02.0f}"
    return s

def hourMinSecToFloat(value, mode='hour', strict=True) -> float:
    """ Convert a string of hh:mm:ss to a float. Useful if you want to
        compare or sort many values.
        
        If strict is False, mm:ss will be parsed. Otherwise, ValueError will be 
        raised. Default is True.
        
        Inverse of `floatToHourMinSec`.
    """
    # hours, mins, secs = value.split(':')
    # value = float(hours) + (float(mins)/60) + (float(secs)/3600)
    
    seconds = ['s', 'sec', 'secs', 'seconds']
    minutes = ['m', 'min', 'mins', 'minutes']
    hours = ['h', 'hr', 'hour', 'hours']
    valid = seconds + minutes + hours
    if mode not in valid:
        msg = f"Mode '{mode}' not in valid modes: {valid}"
        raise ValueError(msg)

    msg = ''    
    try:
        # datetime.strptime(value, "%H:%M:%S")
        hr, mins, sec = [int(s) for s in value.split(':')]
    except ValueError:
        msg = f"Could not read format of time '{value}'"
        if not strict:
            try:
                # datetime.strptime(value, "%M:%S")
                mins, sec = value.split(':')
                mins, sec = [int(s) for s in value.split(':')]
                hr = 0
            except ValueError:
                pass
            else:
                msg = ""
    if msg:
        raise ValueError(msg)
        
    value = float(hr) + (float(mins)/60) + (float(sec)/3600)
        
    if mode in hours:
        return value
    elif mode in minutes:
        return value * 60
    else:
        return value * 3600

def monthYearToFloat(value) -> float:
    """ Convert a string of 'month year' to a float. Useful if you want to
        compare or sort many values.
    """
    month, year = value.split(' ')
    try:
        idx = list(calendar.month_name).index(month)
    except ValueError:
        try:
            idx = list(calendar.month_abbr).index(month)
        except ValueError:
            raise ValueError(f"{month} is not valid month")
    if len(year) != 4:
        raise ValueError("'year' should be four digits")
    year = float(year)
    
    value = year + ((idx-1)/12)
    
    return value

def dayMonthYearToFloat(value) -> float:
    """ Convert a string of 'day month year' to a float. Useful if you want to
        compare or sort many values.
    """
    day, month, year = value.split(' ')
    try:
        idx = list(calendar.month_name).index(month)
    except ValueError:
        try:
            idx = list(calendar.month_abbr).index(month)
        except ValueError:
            raise ValueError(f"{month} is not valid month")
    if len(year) != 4:
        raise ValueError("'year' should be four digits")
    if float(day) > 31 or float(day) < 1:
        raise ValueError("'day' should be between 1 and 31")
        
    year = int(year)
    day = int(day)
    value = day + (idx*31) + (year*12*31)
    
    return value

# def convertSecs(value, mode='hour') -> float:
#     """ Convert seconds to minutes or hours. 
    
#         If `mode` is 'm', 'min', 'mins' or 'minutes', convert to minutes.
#         If `mode` is 'h', 'hr', 'hour' or 'hours', convert to hours.
#     """
#     minutes = ['m', 'min', 'mins', 'minutes']
#     hours = ['h', 'hr', 'hour', 'hours']
#     valid = minutes + hours
#     if mode not in valid:
#         msg = f"Mode '{mode}' not in valid modes: {valid}"
#         raise ValueError(msg)
#     m = value / 60
#     if mode in minutes:
#         return m
#     h = m / 60
#     if mode in hours:
#         return h