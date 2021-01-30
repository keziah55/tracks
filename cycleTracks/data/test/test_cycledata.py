from cycleTracks.data import CycleData
from . import makeDataFrame
import numpy as np
import pytest


class TestCycleData:
    
    @pytest.fixture
    def setup(self):
        self.df = makeDataFrame(100)
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