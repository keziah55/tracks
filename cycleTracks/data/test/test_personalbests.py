from cycleTracks.data import PersonalBests, CycleData
from cycleTracks.util import monthYearToFloat, hourMinSecToFloat
from cycleTracks.test import makeDataFrame
from PyQt5.QtWidgets import QMessageBox
import random
import tempfile
import pandas as pd
import pytest

pytest_plugin = "pytest-qt"

class DummyParent:
    def __init__(self):
        self.tmpfile = tempfile.NamedTemporaryFile()
        makeDataFrame(500, path=self.tmpfile.name)
        self.df = pd.read_csv(self.tmpfile.name, parse_dates=['Date'])
        self.data = CycleData(self.df)
        self.dataAnalysis = None

class TestPersonalBests:
    
    @pytest.fixture
    def setup(self, qtbot):
        self.parent = DummyParent()
        
        self.widget = PersonalBests(self.parent)
        qtbot.addWidget(self.widget)
        self.widget.setGeometry(100, 100, 500, 600)
        self.widget.show()
        
    @pytest.mark.skip("test not yet written")
    def test_new_data(self, setup, qtbot):
        pass
    
    @pytest.mark.skip("test not yet written")
    def test_tied_data(self, setup, qtbot):
        pass
    
    @pytest.mark.skip("test not yet written")
    def test_sort_column(self, setup, qtbot):
        pass