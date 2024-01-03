from .. import Data
from tracks.test import make_dataframe
from tracks.activities import load_activity
import pandas as pd
import numpy as np
import tempfile
import pytest

pytest_plugin = "pytest-qt"

class TestData:
    
    @pytest.fixture
    def setup(self, activity_json_path):
        self.tmpfile = tempfile.NamedTemporaryFile()
        make_dataframe(500, path=self.tmpfile.name)
        self.df = pd.read_csv(self.tmpfile.name, parse_dates=['date'])
        self.activity = load_activity(activity_json_path)
        self.data = Data(self.df, activity=self.activity)
    
    def test_properties(self, setup):
        assert set(self.df.columns) == set(self.activity.measures.keys())
        for name in self.df.columns:
            data = list(self.data[name])
            assert data == list(self.df[name])
            
    def test_group_months(self, setup):
        dfs = self.data.splitMonths()
        for _, df in dfs:
            if not df.empty:
                dates = df['date']
                monthyear = [(date.month, date.year) for date in dates]
                assert len(set(monthyear)) == 1
                
    def test_combine_rows(self, setup, qtbot):
        df = self.df.copy()
        rng = np.random.default_rng()
        row = rng.integers(0, len(df))
        
        while True:        
            replace = rng.integers(0, len(df), size=3)
            if row not in replace:
                break
            
        names = self.df.columns
            
        expected = {name:self.df.iloc[row][name] for name in names}
        
        for idx in replace:
            df.at[idx, 'date'] = expected['date']
            df.at[idx, 'gear'] = expected['gear']
            expected['distance'] += df.at[idx, 'distance']
            expected['calories'] += df.at[idx, 'calories']
            expected['time'] += df.at[idx, 'time'] 
        expected['speed'] = expected['distance'] / expected['time']
        expected['time'] = expected['time']
        
        data = Data(df, self.activity)
        date = expected['date'].strftime("%d %b %Y")
        
        with qtbot.waitSignal(data.dataChanged):
            data.combineRows(date)
        
        tmp_df = data.df[data.df['date'] == expected['date']]
        assert len(tmp_df) == 1
        
        for name in names:
            measure = self.activity[name]
            assert measure.formatted(tmp_df.iloc[0][name]) == measure.formatted(expected[name])
             
    def test_monthly_odometer(self, setup):
        
        tmpfile = tempfile.NamedTemporaryFile()
        make_dataframe(100, path=tmpfile.name)
        df = pd.read_csv(tmpfile.name, parse_dates=['date'])
        data = Data(df)
        
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
                assert row['date'] == dt
                expectedDist += row['distance']
                dfIdx += 1
            assert dist == expectedDist
        