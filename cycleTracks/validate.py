from datetime import date
import calendar
import re
import pandas as pd


def validateInt(value):
    """ Return True if string `value` only contains digits (i.e. represents an int). """
    return value.isdigit()

def validateFloat(value):
    """ Return True if `value` can be cast to a float. """
    try:
        float(value)
        return True
    except ValueError:
        return False
    
def validateDate(value):
    """ Return True if `value` can be cast to a valid date. """
    try:
        parseDate(value)
        return True
    except (ValueError, TypeError):
        return False

def validateTime(value):
    """ Return True if `value` can be cast to a valid time. """
    try:
        parseTime(value)
        return True
    except ValueError:
        return False
    
def parseTime(value):
    """ Convert string `value`, which should be a time in [hh]:mm:[ss] format,
        into hh:mm:ss format.
    """
    values = value.split(':')
    if not all([validateInt(v) for v in values]) or len(values) > 3:
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
    >>> str_to_date('02 Mar 17')
    datetime.date(2017, 3, 2)
    
    >>> str_to_date('04 April 17')
    datetime.date(2017, 4, 4)
    
    >>> str_to_date('4/8/15')
    datetime.date(2015, 8, 4)
    
    >>> str_to_date('4-8-2015')
    datetime.date(2015, 8, 4)
    
    >>> str_to_date('')
    datetime.date(2017, 9, 28)   # current date at time of writing
    
    >>> str_to_date('3')
    datetime.date(2017, 9, 3)    # time of writing was September 2017
    
    >>> str_to_date('5.5')
    datetime.date(2017, 5, 5)    # time of writing was September 2017
    
    >>> str_to_date('020312')
    datetime.date(12, 3, 2)
    
    >>> str_to_date('02032012')
    datetime.date(2012, 3, 2)
    """
    
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
        return today
    
    try:
        l = re.split(r'[\s/.-]', value)
    except TypeError:
        raise TypeError(f"Cannot format '{value}' as date. Input should be a string.")
    
    # if a single value was given as input...
    if len(l) == 1:
        # ... if value is Day, nothing needs to be done
        if 1 <= len(value) <= 2:
            pass
        # ... if value is DDMMYY or DDMMYYYY, split into parts
        elif len(value) == 6 or len(value) == 8:
            l = [value[:2], value[2:4], value[4:]]
        # ... if value is none of the above, raise exception
        else:
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
