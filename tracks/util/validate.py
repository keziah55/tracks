""" 
Some functions for type checking/checking if a string can be converted
to a float, date or time string.
"""

from .convertfuncs import (monthYearToFloat, hourMinSecToFloat, dayMonthYearToFloat, 
                           parseDate, parseDuration)

def isInt(value):
    """ Return True if string `value` only contains digits (i.e. represents an int). """
    return value.isdigit()

def isFloat(value):
    """ Return True if `value` can be cast to a float. """
    try:
        float(value)
        return True
    except ValueError:
        return False
    
def isDate(value, allowEmpty=True):
    """ Return True if `value` can be cast to a valid date. 
    
        If `value` is an empty string, by default this will return True, as
        parseDate returns the current date. To disable this, pass allowEmpty=False.
    """
    if not allowEmpty and not value:
        return False
    try:
        parseDate(value)
        return True
    except (ValueError, TypeError):
        return False

def isDuration(value):
    """ Return True if `value` can be cast to a valid time. """
    try:
        parseDuration(value)
        return True
    except ValueError:
        return False

def checkDayMonthYearFloat(value):
    """ Return True if `value` is a 'month year' string that can be converted 
        to a float.
    """
    try:
        dayMonthYearToFloat(value)
        return True
    except ValueError:
        return False

def checkMonthYearFloat(value):
    """ Return True if `value` is a 'month year' string that can be converted 
        to a float.
    """
    try:
        monthYearToFloat(value)
        return True
    except ValueError:
        return False
    
def checkHourMinSecFloat(value):
    """ Return True if `value` is a 'hh:mm:ss' string that can be converted 
        to a float.
    """
    try:
        hourMinSecToFloat(value)
        return True
    except ValueError:
        return False