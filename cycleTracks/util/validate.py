""" 
Some functions for type checking/checking if a string can be converted
to a float, date or time string.
"""

from .convertfuncs import monthYearToFloat, hourMinSecToFloat, parseDate, parseTime

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
    
def isDate(value):
    """ Return True if `value` can be cast to a valid date. """
    try:
        parseDate(value)
        return True
    except (ValueError, TypeError):
        return False

def isTime(value):
    """ Return True if `value` can be cast to a valid time. """
    try:
        parseTime(value)
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