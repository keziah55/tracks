"""
Object providing convenient access to the contents of a DataFrame of cycling
data.
"""
from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5.QtCore import pyqtSignal as Signal
from cycleTracks.util import parseDate, hourMinSecToFloat, floatToHourMinSec
from datetime import datetime
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
                              'Avg speed (km/h)':'avgSpeed',
                              'Avg. speed (km/h)':'avgSpeed',
                              'Gear':'gear'}
        
        shortNames = ['distance', 'date', 'time', 'calories', 'speed', 'gear']
        self._quickNames = dict(zip(shortNames, self.propertyNames.keys()))
        
    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, key):
        if key in self.propertyNames.keys():
            name = self.propertyNames[key]
            return getattr(self, name)
        else:
            raise NameError(f"{key} not a valid property name.")
         
    def __repr__(self):
        return repr(self.df)
    
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
    def dateFmt(self, fmt="%a %d %b %Y"):
        return [dt.strftime(fmt) for dt in self.datetimes]
    
    @property 
    def avgSpeed(self):
        """ Return average speeds as numpy array. """
        return self.distance/self.timeHours
    
    def splitMonths(self):
        """ Split `df` into list of DataFrames, split by month. """
        grouped = self.df.groupby(pd.Grouper(key='Date', freq='M'))
        return [group for _,group in grouped]
    
    def getMonthlyOdometer(self):
        """ Return list of datetime objects and list of floats.
            
            The datetime objects are required, as they add dummy 1st of the 
            month data points to reset the total to 0km.
        """
        
        dfs = self.splitMonths()
        odo = []
        dts = []
        for i, df in enumerate(dfs):
            # at the start of every month, insert 0km entry
            if df.empty:
                # if there's no data in the df, need to get month and year from
                # previous df
                prevDate = dfs[-1]['Date'].iloc[0]
                month = prevDate.month - 1
                if month == 0:
                    month = 12
                year = prevDate.year
                if month == 12:
                    year -= 1
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
                    t0 = hourMinSecToFloat(self.df.iloc[i0][name])
                    t1 = hourMinSecToFloat(self.df.iloc[i][name])
                    newValue = floatToHourMinSec(t0 + t1)
                    self.df.at[i0, name] = newValue
                else:
                    self.df.at[i0, name] += self.df.iloc[i][name]
                    
        self.df = self.df.drop(idx)
        self.dataChanged.emit(i0)