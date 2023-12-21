"""
Object providing convenient access to the contents of a DataFrame.
"""

from qtpy.QtCore import QObject
from qtpy.QtCore import Signal, Slot
from tracks.util import parseDate, parseDuration, hourMinSecToFloat, floatToHourMinSec
from functools import partial
from datetime import datetime
import calendar
import numpy as np
import pandas as pd
import functools

def check_empty(func):
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        if self.df.empty:
            return []
        else:
            return func(self, *args, **kwargs)
    return wrapped

class Data(QObject):
    
    dataChanged = Signal(object)
    """ 
    **signal** dataChanged(object `index`)
    
    Emitted when the data in the object is changed, with the pandas index
    of the new rows.
    """
    
    newMax = Signal(str, object)
    """ 
    **signal** newMax(str `column`, object `value`)
        
    Emitted when newly added data contains a new max value for a given column.
    """
    
    def __init__(self, df, activity=None):
        """ 
        Object providing convenience functions for accessing data from a given DataFrame.
        """
        super().__init__()
        self.df = self._makeSpeedColumn(df)
        
        if activity is None:
            # temporary workaround for when we create Data objects on the fly
            from tracks.activities import load_activity
            from pathlib import Path
            p = Path.home().joinpath(".tracks", "cycling.json")
            activity = load_activity(p)
        
        self.propertyNames = {}
        self._quickNames = {}
        self.fmtFuncs = {}
        
        for slug, measure in activity.measures.items():
            self.propertyNames[measure.full_name] = slug
            self._quickNames[slug] = measure.full_name
            if measure.sig_figs is not None:
                self.fmtFuncs[measure.full_name] = partial(self._formatFloat, digits=measure.sig_figs)
            elif slug == "date":
                self.fmtFuncs[measure.full_name] = partial(self._formatDate, dateFmt="%d %b %Y")
            elif slug == "time":
                self.fmtFuncs[measure.full_name] = lambda t: t
            else:
                # assume int/no sig figs
                self.fmtFuncs[measure.full_name] = lambda value: self._formatFloat(np.around(value), 0)
        
        self.propertyNames['Time (hours)'] = 'timeHours'
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
    
    def row(self, idx, formatted=False):
        row = {key:self[key][idx] for key in self.propertyNames}
        if formatted:
            for key, value in row.items():
                row[key] = self.fmtFuncs[key](value)
        return row
    
    def toString(self, headTail=None):
        """ 
        Return Data object as a string.
        
        Parameters
        ----------
        headTail : int, optional
            If provided, abridge the object to show only the first and last 
            `headTail` rows. By default, do not abridge and return the full object.
        """
        keys = ["Date", "Time", "Distance (km)", "Speed (km/h)", "Calories", "Gear"]
        joinStr = "  "
        columns = {key: self.formatted(key) for key in keys}
        widths = {key: max(max([len(str(item)) for item in values]), len(key))#+len(joinStr))
                           for key, values in columns.items()}
        size = len(self)
        if headTail is not None and size > 2*headTail:
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
            pdIdx = self.df.index[idx]
            row = [f"{pdIdx:>{idxWidth}}"]
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
            msg = f"Can only append dict to Data, not {type(dct).__name__}"
            raise TypeError(msg)
            
        times = np.array([hourMinSecToFloat(t) for t in dct['Time']])
        dct['Speed (km/h)'] = dct['Distance (km)'] / times
        
        tmpDf = pd.DataFrame.from_dict(dct)
        tmpDf = pd.concat([self.df, tmpDf], ignore_index=True)
        index = tmpDf[~tmpDf.isin(self.df)].dropna().index
        self.df = tmpDf
        self.df.sort_values('Date', inplace=True)
        self.dataChanged.emit(index)
        
    def update(self, values):
        """ 
        Update items in the underlying DataFrame. 
        
        `values` should be a dict; the keys should be indices and values 
        should be dicts of column:value. If the value currently at the 
        given column and index is different from that supplied in the 
        dictionary, it will be updated.
        
        If changes are made, `dataChanged` is emitted.
        
        Example `values` structure:
            {10: {'Distance (km)':25, 'Calories':375}}
        """
        changed = []
        for index, dct in values.items():
            for col, value in dct.items():
                if self.df.at[index, col] != value:
                    self.df.at[index, col] = value
                    changed.append(index)
        if changed:
            for index in changed:
                # update the speed for the changed indices
                # (simpler to do this for all changed indices than also track whether
                # distance and/or time have changed)
                distance = self.df['Distance (km)'][index]
                time = hourMinSecToFloat(self.df['Time'][index])
                self.df.at[index, 'Speed (km/h)'] = distance / time
            self.dataChanged.emit(changed)
        
    def _makeSpeedColumn(self, df):
        ## speed was not always included in csv file
        ## If user does not have this column, create it
        if 'Speed (km/h)' not in df.columns:
            times = np.array([hourMinSecToFloat(t) for t in df['Time']])
            df['Speed (km/h)'] = df['Distance (km)'] / times
        return df
        
    def setDataFrame(self, df):
        self.df = df
        self.dataChanged.emit(self.df.index)
            
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
    def speed(self):
        """ Return average speeds as numpy array. """
        return np.array(self.df['Speed (km/h)'])
    
    @property
    def timeHours(self):
        """ 
        Return numpy array of 'Time' column, where each value is converted to hours.
        """
        time = np.array([hourMinSecToFloat(t, strict=False) for t in self.df['Time']])
        return time
    
    @property
    def dateTimestamps(self):
        """ 
        Return 'Date' column, converted to array of timestamps (time since epoch).
    
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
    
    def getMonth(self, month, year, returnType='DataFrame'):
        """ Return DataFrame or Data of data from the given month and year. """
        ts0 = pd.Timestamp(day=1, month=month, year=year)
        month += 1
        if month > 12:
            month %= 12
            year += 1
        ts1 = pd.Timestamp(day=1, month=month, year=year)
        df = self.df[(self.df['Date'] >= ts0) & (self.df['Date'] < ts1)]
        if returnType == "Data":
            df = Data(df)
        return df
    
    @check_empty
    def splitMonths(self, includeEmpty=False, returnType='DataFrame'):
        """ 
        Split `df` into months. 
        
        Parameters
        -----------
        includeEmpty : bool
            If True and if a month has no data, a monthYear string and empty 
            DataFrame or Data object will be included in the returned list. 
            Otherwise, it  will be ignored. Default is False.
        returnType : {'DataFrame', 'Data'}
            Type of object to return with each month's data. Default is 
            (pandas) 'DataFrame'
        
        Returns
        -------
        list of (monthYear string, DataFrame/Data) tuples
        """
        validReturnTypes = ['DataFrame', 'Data']
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
            if returnType == "Data":
                df = Data(df)
            lst.append((monthYear, df))
        return lst
    
    def getMonthlyOdometer(self):
        """ 
        Return list of datetime objects and list of floats.
            
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
    
    @check_empty
    def getPBs(self, column, pbCount):
        """ 
        Return indices where the value in `column` was a PB (at the time).
    
        Parameters
        ----------
        column : str
            Column :attr:`quickName` to look through
        pbCount : int
            Number of sessions that can be PBs simultaneously
            
        Returns
        -------
        idx : List[int]
            list of indicies of PBs
        """
        key = self.quickNames[column]
        if key == 'Time':
            series = self.timeHours
        else:
            series = self[key]
        if pbCount > len(series):
            pbCount = len(series)
        best = series[:pbCount]
        idx = list(range(pbCount)) # first pbCount values will be PBs
        for n in range(pbCount, len(series)):
            if series[n] >= np.min(best):
                idx.append(n)
                # replace value in best array
                minIdx = np.argmin(best)
                best[minIdx] = series[n]
        return idx
 
    def combineRows(self, date):
        """ Combine all rows in the dataframe with the given data. """
        i0, *idx = self.df[self.df['Date'] == parseDate(date, pd_timestamp=True)].index
        
        combinable = ['Time', 'Distance (km)', 'Calories', 'Speed (km/h)']
        
        for i in idx:
            for name in combinable:
                if name == 'Time':
                    t0 = hourMinSecToFloat(parseDuration(self.df.iloc[i0][name]))
                    t1 = hourMinSecToFloat(parseDuration(self.df.iloc[i][name]))
                    newValue = floatToHourMinSec(t0 + t1)
                    self.df.at[i0, name] = newValue
                elif name == 'Speed (km/h)':
                    self.df.at[i0, name] = self.df['Distance (km)'][i0] / hourMinSecToFloat(self.df['Time'][i0])
                else:
                    self.df.at[i0, name] += self.df.iloc[i][name]
                    
        self.df.drop(idx, inplace=True)
        self.dataChanged.emit(i0)
        
    def removeRows(self, **kwargs):
        """ 
        Remove row(s) from the DataFrame by date or index. 
        
        Pass either 'dates' or 'index' kwarg.
    
        Note that this assumes dates are unique in the object.
        """
        dates = kwargs.get("dates", None)
        if dates is not None:
            if isinstance(dates, str):
                dates = [dates]
            if not isinstance(dates, list):
                raise TypeError("Data.removeRows takes list of dates")
                
            idx = []
            for date in dates:
                idx += list(self.df[self.df['Date'] == parseDate(date, pd_timestamp=True)].index)
                
            self.df.drop(idx, inplace=True)
            self.dataChanged.emit(None)
        
        index = kwargs.get("index", None)
        if index is not None:
            self.df.drop(index, inplace=True)
            self.dataChanged.emit(None)