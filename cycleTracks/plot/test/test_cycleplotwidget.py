from cycleTracks.plot import CyclePlotWidget
from cycleTracks.test import MockParent
from qtpy.QtCore import Qt, QPoint
from datetime import datetime
import random
import pytest

pytest_plugin = "pytest-qt"

class Click:
    def __init__(self, pos, double):
        self._double = double
        self._pos = pos
        
    def double(self):
        return self._double
    
    def pos(self):
        return self._pos
    
    def button(self):
        return Qt.LeftButton


class TestCyclePlotWidget:
    
    @pytest.fixture
    def setup(self, qtbot):
        self.parent = MockParent()
        
        self.widget = CyclePlotWidget(self.parent)
        qtbot.addWidget(self.widget)
        self.widget.showMaximized()
        
    @pytest.fixture
    def setup_reduced_points(self, qtbot):
        self.parent = MockParent(size=50)
        
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
            # make sure 'distance' ins't first, as nothing will change in that case
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
                
    def test_month_zoom(self, setup, qtbot, variables):
    
        qtbot.wait(variables.wait)
    
        axis = self.widget.plotWidget.plotItem.getAxis('bottom')
        
        geom = axis.geometry()
        middleX = geom.x() + (geom.width()//2)
        middleY = geom.y() + (geom.height()//2)
        pos = QPoint(int(middleX), int(middleY))
        
        click = Click(pos=pos, double=True)
        with qtbot.waitSignal(axis.axisDoubleClicked):
            axis.mouseClickEvent(click)
            
        qtbot.wait(variables.wait)
            
        # random data always generated current date and current date - 2 years
        # so midpoint should be current month - 1 year
        # but in practice month is one past this
        # don't really know why
        now = datetime.now()
        dt0 = datetime.fromtimestamp(axis.tickVals[0])
        dt1 = datetime.fromtimestamp(axis.tickVals[-1])
        assert dt0.month == now.month + 1
        assert dt0.year == now.year - 1
        assert dt1.month == dt0.month + 1
        
        
    def test_mouse_hover(self, setup_reduced_points, qtbot, variables):
        qtbot.wait(variables.shortWait) # wait for widget to be maximized so we can get the right size
        
        size = self.widget.size()
        y = size.height() // 2

        idx = None
        plotWidget = self.widget.plotWidget
        plotLabel = self.widget.plotLabel
        
        for x in range(0, size.width(), 5):
            pos = QPoint(x, y)
            qtbot.mouseMove(plotWidget, pos)
        
            if plotWidget.currentPoint and idx != plotWidget.currentPoint['index']:
                idx = plotWidget.currentPoint['index']
                pt = plotWidget.dataItem.scatter.data[idx]
                
                dateLabel = plotLabel.data['date']['widget']
                expected = f"<div style='font-size: {dateLabel.fontSize}pt'>"
                expected += f"{self.widget.plotWidget.currentPoint['date']}</div>"
                assert dateLabel.text() == expected
                
                distLabel = plotLabel.data['distance']['widget']
                expected = f"<div style='font-size: {distLabel.fontSize}pt; "
                expected += f"color: {distLabel.colour}'>"
                expected += f"Distance: {self.widget.plotWidget.currentPoint['distance']} km</div>"
                assert distLabel.text() == expected
                
        # move mouse back to middle before next test
        pos = QPoint(size.width()//2, y)
        qtbot.mouseMove(plotWidget, pos)