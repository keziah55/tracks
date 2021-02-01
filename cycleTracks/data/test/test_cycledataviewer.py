from cycleTracks.data import CycleDataViewer, CycleData
from . import makeDataFrame
from PyQt5.QtCore import Qt
from datetime import date
import random
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
        
        self.widget = CycleDataViewer(self.parent)
        qtbot.addWidget(self.widget)
        self.widget.show()
        
