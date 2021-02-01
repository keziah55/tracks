from cycleTracks.data import CycleDataViewer, CycleData
from cycleTracks.util import monthYearToFloat, hourMinSecToFloat
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
        self.widget.setGeometry(100, 100, 500, 600)
        self.widget.show()
        
    def test_sort(self, setup, qtbot):
        
        columns = self.widget.headerLabels
        columns = random.sample(columns, k=len(columns))
        
        for column in columns:
            idx = self.widget.headerLabels.index(column)
            
            expected = [item.text(idx) for item in self.widget.topLevelItems]
            
            if column == 'Date':
                expected = sorted(expected, key=monthYearToFloat)
            elif column == 'Time':
                expected = sorted(expected, key=hourMinSecToFloat)
            else:
                expected = sorted(expected, key=float)
            
            for _ in range(2):
                expected.reverse()
                self.widget.header().sectionClicked.emit(idx)
                items = [item.text(idx) for item in self.widget.topLevelItems]
                assert items == expected
                
            
    def test_new_data(self, setup, qtbot):
        
        # expand some headers
        min_expanded = 3
        num = len(self.widget.topLevelItems) // 4
        num = max(min_expanded, num)
        expanded = random.sample(self.widget.topLevelItems, num)
        for item in expanded:
            self.widget.expandItem(item)
        expanded = [item.text(0) for item in expanded]
            
        # new data
        tmpfile = tempfile.NamedTemporaryFile()
        makeDataFrame(100, path=tmpfile.name)
        df = pd.read_csv(tmpfile.name, parse_dates=['Date'])
        data = CycleData(df)
        self.parent.data = data    
        
        self.widget.newData()
        
        for item in self.widget.topLevelItems:
            if item.isExpanded():
                assert item.text(0) in expanded
        
        
        