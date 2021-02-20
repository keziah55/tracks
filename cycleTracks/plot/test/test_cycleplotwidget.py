from cycleTracks.data import CycleData
from cycleTracks.plot import CyclePlotWidget
from cycleTracks.test import makeDataFrame
from PyQt5.QtCore import Qt
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

class TestCyclePlotWidget:
    
    @pytest.fixture
    def setup(self, qtbot):
        self.parent = DummyParent()
        
        self.widget = CyclePlotWidget(self.parent)
        qtbot.addWidget(self.widget)
        self.widget.showMaximized()
        
        
    def test_switch_series(self, setup, qtbot):
        
        plotLabel = self.widget.plotLabel
        
        def callback(name):
            return name == key
        
        keys = list(plotLabel.data.keys())
        random.shuffle(keys)
        if keys[0] == 'distance':
            name = keys.pop(0)
            keys.append(name)
        
        for key in keys:
            dct = plotLabel.data[key]
            label = dct['widget']
            
            with qtbot.waitSignal(plotLabel.labelClicked, check_params_cb=callback):
                qtbot.mouseClick(label, Qt.LeftButton)
                
            if key != 'date':
                axis = self.widget.plotWidget.plotItem.getAxis('left')
                axisLabel = axis.labelText
                assert axisLabel == self.parent.data.quickNames[key]
                
