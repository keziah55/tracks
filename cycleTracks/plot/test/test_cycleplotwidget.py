from cycleTracks.data import CycleData
from cycleTracks.plot import CyclePlotWidget
from cycleTracks.test import makeDataFrame
import tempfile
import pandas as pd
import pytest

pytest_plugin = "pytest-qt"

class DummyParent:
    def __init__(self):
        self.tmpfile = tempfile.NamedTemporaryFile()
        makeDataFrame(100, path=self.tmpfile.name)
        self.df = pd.read_csv(self.tmpfile.name, parse_dates=['Date'])
        self.data = CycleData(self.df)

class TestCycleDataViewer:
    
    @pytest.fixture
    def setup(self, qtbot):
        self.parent = DummyParent()
        
        self.widget = CyclePlotWidget(self.parent)
        qtbot.addWidget(self.widget)
        self.widget.setGeometry(100, 100, 1000, 1000)
        self.widget.show()
        
        
    def test_plot(self, setup, qtbot):
        pass