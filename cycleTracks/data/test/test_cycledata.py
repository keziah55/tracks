from cycleTracks.data import CycleData
from cycleTracks.util import parseDuration, hourMinSecToFloat, floatToHourMinSec
from cycleTracks.test import makeDataFrame
import pandas as pd
import numpy as np
import tempfile
import pytest

pytest_plugin = "pytest-qt"

class TestCycleData:
    
    @pytest.fixture
    def setup(self):
        self.tmpfile = tempfile.NamedTemporaryFile()
        makeDataFrame(1000, path=self.tmpfile.name)
        self.df = pd.read_csv(self.tmpfile.name, parse_dates=['Date'])
        self.data = CycleData(self.df)
    
    def test_properties(self, setup):
        for name in self.df.columns:
            assert name in self.data.propertyNames.keys()
            data = list(self.data[name])
            assert data == list(self.df[name])
            
    @pytest.mark.parametrize("value,expected", [("1:23:45", 5025), ("20:05", 1205), 
                                                ("45", None), ("65:12", None), ("invalid", None)])
    def test_time_to_secs(self, setup, value, expected):
        if expected is None:
            with pytest.raises(ValueError):
                self.data._timeToSecs(value)
        else:
            assert self.data._timeToSecs(value) == expected
            
    @pytest.mark.parametrize("value,expected", [(12, 0.2), (60, 1), (630, 10.5), (12345, 205.75)])
    @pytest.mark.parametrize("mode", ['invalid', 'm', 'min', 'mins', 'minutes', 'h', 'hr', 'hour', 'hours'])
    def test_convert_secs(self, setup, value, expected, mode):
        if mode == 'invalid':
            with pytest.raises(ValueError):
                self.data._convertSecs(value, mode=mode)
        else:
            if mode.startswith('h'):
                expected /= 60
            assert np.isclose(self.data._convertSecs(value, mode=mode), expected)
            
    def test_group_months(self, setup):
        dfs = self.data.splitMonths()
        for _, df in dfs:
            if not df.empty:
                dates = df['Date']
                monthyear = [(date.month, date.year) for date in dates]
                assert len(set(monthyear)) == 1
             
                
    def test_combine_rows(self, setup, qtbot):
        
        rng = np.random.default_rng()
        row = rng.integers(0, len(self.df))
        
        while True:        
            replace = rng.integers(0, len(self.df), size=3)
            if row not in replace:
                break
            
        names = self.df.columns
            
        expected = {name:self.df.iloc[row][name] for name in names}
        expected['Time'] = hourMinSecToFloat(parseDuration(expected['Time']))
        
        for idx in replace:
            self.df.at[idx, 'Date'] = expected['Date']
            self.df.at[idx, 'Gear'] = expected['Gear']
            expected['Distance (km)'] += self.df.at[idx, 'Distance (km)']
            expected['Calories'] += self.df.at[idx, 'Calories']
            expected['Time'] += hourMinSecToFloat(parseDuration(self.df.at[idx, 'Time']))
        expected['Time'] = floatToHourMinSec(expected['Time'])
            
        data = CycleData(self.df)
        date = expected['Date'].strftime("%d %b %Y")
        
        with qtbot.waitSignal(data.dataChanged):
            data.combineRows(date)
        
        df = data.df[data.df['Date'] == expected['Date']]
        assert len(df) == 1
        
        for name in names:
            try:
                float(df.iloc[0][name])
            except:
                assert df.iloc[0][name] == expected[name]
            else:
                assert np.isclose(df.iloc[0][name], expected[name])
        
             
    def test_monthly_odometer(self, setup):
        
        tmpfile = tempfile.NamedTemporaryFile()
        makeDataFrame(100, path=tmpfile.name)
        df = pd.read_csv(tmpfile.name, parse_dates=['Date'])
        data = CycleData(df)
        
        dts, odo = data.getMonthlyOdometer()
        
        dfIdx = 0
        expectedDist = 0
        
        for i in range(len(dts)):
            dt = dts[i]
            dist = odo[i]
            
            if i == 0 or dt.day == 1 and dts[i-1] != dt:
                # new month
                expectedDist = 0
            else:
                row = df.iloc[dfIdx]
                print(f"row: {row}")
                assert row['Date'] == dt
                expectedDist += row['Distance (km)']
                dfIdx += 1
            assert dist == expectedDist
        