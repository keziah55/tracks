"""
Object providing convenient access to the contents of a DataFrame of cycling data.
"""
from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot
from cycleTracks.util import (parseDate, parseDuration, hourMinSecToFloat, 
                              floatToHourMinSec)
from functools import partial
from datetime import datetime
import calendar
import numpy as np
import pandas as pd

class CycleData(QObject):
    
    dataChanged = Signal(object)
    """ **signal** dataChanged(object `index`)
    
        Emitted when the data in the object is changed, with the pandas index
        of the new rows.
    """
    
    newMax = Signal(str, object)
    """ **signal** newMax(str `column`, object `value`)
        
        Emitted when newly added data contains a new max value for a given
        column.
    """
    
    def __init__(self, df):
        """ Object providing convenience functions for accessing data from 
            a given DataFrame of cycling data.
        """
        super().__init__()
        self.df = df
        self.propertyNames = {'Distance (km)':'distance', 
                              'Date':'date',
                              'Time':'time',
                              'Calories':'calories',
                              # 'Avg speed (km/h)':'avgSpeed',
                              'Avg. speed (km/h)':'avgSpeed',
                              'Gear':'gear',
                              'Time (hours)':'timeHours'}
        
        shortNames = ['distance', 'date', 'time', 'calories', 'speed', 'gear']
        self._quickNames = dict(zip(shortNames, self.propertyNames.keys()))
        
        sigFigs = {'Distance (km)':2, 
                   'Calories':1,
                   'Avg. speed (km/h)':2,
                   'Gear':0}
        self.fmtFuncs = {k:partial(self._formatFloat, digits=v) for k,v in sigFigs.items()}
        self.fmtFuncs['Date'] = partial(self._formatDate, dateFmt="%d %b %Y")
        self.fmtFuncs['Time'] = lambda t: t
        self.fmtFuncs['Time (hours)'] = floatToHourMinSec
        
    @staticmethod
    def _formatFloat(value, digits=2):
        fmt = "{" + f":.{digits}f" + "}"
        return fmt.format(value)
    
    @staticmethod
    def _formatDate(value, dateFmt="%d %b %Y"):
        return value.strftime(dateFmt)
    
    def formatted(self, key):
        return [self.fmtFuncs[key](v) for v in self[key]]
    
    def summaryString(self, key, func=sum):
        return self.fmtFuncs[key](func(self[key]))
        
    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, key):
        if key in self.propertyNames.keys():
            name = self.propertyNames[key]
            return getattr(self, name)
        else:
            raise NameError(f"{key} not a valid property name.")
         
    def __repr__(self):
        return self.toString(headTail=5)
        
    def toString(self, headTail=None):
        """ Return CycleData object as a string.
        
            Parameters
            ----------
            headTail : int, optional
                If provided, abridge the object to show only the first and last 
                `headTail` rows. By default, do not abridge and return the full object.
        """
        keys = ["Date", "Time", "Distance (km)", "Avg. speed (km/h)", "Calories", "Gear"]
        joinStr = "  "
        columns = {key: self.formatted(key) for key in keys}
        widths = {key: max(max([len(str(item)) for item in values]), len(key))#+len(joinStr))
                           for key, values in columns.items()}
        size = len(self)
        if headTail is not None:
            indices = list(range(headTail)) + list(range(size-headTail,size))
        else:
            indices = range(size)
        
        s = ""
        idxWidth = max(len(s), len(str(size)))
        header = [f"{s:<{idxWidth}}"]
        header += [f"{key:>{widths[key]}}" for key in columns]
        rows = [joinStr.join(header)]
            
        for n, idx in enumerate(indices):
            if n >= 1:
                if idx != indices[n-1] + 1:
                    rows.append("...")
            row = [f"{idx:>{idxWidth}}"]
            for key, lst in columns.items():
                value = lst[idx]
                width = widths[key]
                s = f"{value:>{width}}"
                row.append(s)
            rows.append(joinStr.join(row))
        
        return "\n".join(rows)
    
    @property
    def quickNames(self):
        return self._quickNames
         
    @Slot(dict)
    def append(self, dct):
        """ Append values in dict to DataFrame. """
        if not isinstance(dct, dict):
            msg = f"Can only append dict to CycleData, not {type(dct).__name__}"
            raise TypeError(msg)
        
        tmpDf = pd.DataFrame.from_dict(dct)
        tmpDf = self.df.append(tmpDf, ignore_index=True)
        index = tmpDf[~tmpDf.isin(self.df)].dropna().index
        self.df = tmpDf
        self.dataChanged.emit(index)
        
    def setDataFrame(self, df):
        self.df = df
        self.dataChanged.emit(self.df.index)
            
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
        
    @property
    def distance(self):
        """ Return 'Distance (km)' column as numpy array. """
        return np.array(self.df['Distance (km)'])
    
    @property
    def time(self):
        """ Return 'Time' column as list. """
        return list(self.df['Time'])
    
    @property
    def date(self):
        """ Return 'Date' column as list. """
        return list(self.df['Date'])
    
    @property
    def calories(self):
        """ Return 'Calories' column as numpy array. """
        return np.array(self.df['Calories'])
    
    @property
    def gear(self):
        """ Return 'Gear' column as numpy array. """
        return np.array(self.df['Gear'])
    
    @property
    def timeHours(self):
        """ Return numpy array of 'Time' column, where each value is converted
            to hours.
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
        fmt = "%Y-%m-%d"
        # 'strptime(d.strftime(fmt), fmt)' this is ugly and is required 
        # because the Date column is a pandas datetime object, but it adds an
        # empty time to the date, which we need to get rid of here, before
        # calling datetime.strptime
        return [datetime.strptime(d.strftime(fmt), fmt) for d in self.df['Date']]
    
    @property 
    def avgSpeed(self):
        """ Return average speeds as numpy array. """
        return self.distance/self.timeHours
    
    def splitMonths(self, includeEmpty=False, returnType='DataFrame'):
        """ Split `df` into months. 
        
            Parameters
            -----------
            includeEmpty : bool
                If True and if a month has no data, a monthYear string and empty 
                DataFrame or CycleData object will be included in the returned list. 
                Otherwise, it  will be ignored. Default is False.
            returnType : {'DataFrame', 'CycleData'}
                Type of object to return with each month's data. Default is 
                (pandas) 'DataFrame'
            
            Returns
            -------
            list of (monthYear string, DataFrame/CycleData) tuples
        """
        validReturnTypes = ['DataFrame', 'CycleData']
        if returnType not in validReturnTypes:
            msg = f"Invalid returnType '{returnType}'. Valid values are {', '.join(validReturnTypes)}"
            raise ValueError(msg)
        grouped = self.df.groupby(pd.Grouper(key='Date', freq='M'))
        dfs = [group for _,group in grouped]
        lst = []
        for df in dfs:
            if df.empty:
                if not includeEmpty:
                    continue
                else:
                    # go backwards until we find a non-empty dataframe
                    i = 0
                    while df.empty:
                        i += 1
                        df = lst[-i][1]
                    # get the first date
                    date = df['Date'].iloc[0]
                    # get the month and year and adjust to find the missing month and year
                    month = date.month + i
                    year = date.year
                    if month > 12:
                        month = 1
                        year += 1
                    # make empty dataframe to add to lst
                    df = pd.DataFrame()
            else:
                date = df['Date'].iloc[0]
                month = date.month
                year = date.year
            monthYear = f"{calendar.month_name[month]} {year}"
            if returnType == "CycleData":
                df = CycleData(df)
            lst.append((monthYear, df))
        return lst
    
    def getMonthlyOdometer(self):
        """ Return list of datetime objects and list of floats.
            
            The datetime objects are required, as they add dummy 1st of the 
            month data points to reset the total to 0km.
        """
        dfs = self.splitMonths(includeEmpty=True)
        odo = []
        dts = []
        for i, df in enumerate(dfs):
            monthYear, df = df
            # at the start of every month, insert 0km entry
            if df.empty:
                # if there's no data in the df, get the month and year from the
                # associated monthYear string
                month, year = monthYear.split(' ')
                month = list(calendar.month_name).index(month)
                year = int(year)
            else:
                month = df['Date'].iloc[0].month
                year = df['Date'].iloc[0].year
            tmp = datetime(year, month, 1)
            dts.append(tmp)
            odo.append(0)
            
            for _, row in df.iterrows():
                dt = row['Date'].to_pydatetime()
                dist = odo[-1] + row['Distance (km)']
                dts.append(dt)
                odo.append(dist)
        return dts, odo
 
    def combineRows(self, date):
        """ Combine all rows in the dataframe with the given data. """
        i0, *idx = self.df[self.df['Date'] == parseDate(date, pd_timestamp=True)].index
        
        combinable = ['Time', 'Distance (km)', 'Calories']
        
        for i in idx:
            for name in combinable:
                if name == 'Time':
                    t0 = hourMinSecToFloat(parseDuration(self.df.iloc[i0][name]))
                    t1 = hourMinSecToFloat(parseDuration(self.df.iloc[i][name]))
                    newValue = floatToHourMinSec(t0 + t1)
                    self.df.at[i0, name] = newValue
                else:
                    self.df.at[i0, name] += self.df.iloc[i][name]
                    
        self.df = self.df.drop(idx)
        self.dataChanged.emit(i0)
        