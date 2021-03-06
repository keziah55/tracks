from cycleTracks.cycletracks import CycleTracks
from PyQt5.QtCore import Qt, QPoint, QPointF
from datetime import datetime, date
import random
from . import makeDataFrame
import tempfile
import pytest

pytest_plugin = "pytest-qt"
pytestmark = pytest.mark.filterwarnings("error")

class TestTracks:
    
    @pytest.fixture
    def setup(self, qtbot, monkeypatch):
        
        self.tmpfile = tempfile.NamedTemporaryFile()
        makeDataFrame(100, path=self.tmpfile.name)
        
        def mockGetFile(*args, **kwargs):
            return self.tmpfile.name
        monkeypatch.setattr(CycleTracks, "getFile", mockGetFile)
        
        self.app = CycleTracks()
        self.addData = self.app.addData
        self.viewer = self.app.viewer
        self.plot = self.app.plot
        self.plotWidget = self.plot.plotWidget
        
        
    @pytest.fixture
    def teardown(self):
        yield
        self.app.close()
    
    
    def test_add_data(self, setup, qtbot, teardown):
        
        numTopLevelItems = len(self.viewer.topLevelItems)
        pts = self.plotWidget.dataItem.scatter.data
        
        row = 0
        values = ["5 Jan 2022", "40:23", "24.22", "361.2", "7"]
        for col in range(self.addData.table.columnCount()):
            value = values[col]
            self.addData.table.item(row, col).setText(str(value))
        
        with qtbot.waitSignal(self.addData.newData):
            qtbot.mouseClick(self.addData.okButton, Qt.LeftButton)
            
        assert len(self.viewer.topLevelItems) == numTopLevelItems + 1 
        expected = ["05 Jan 2022", "00:40:23", "24.22", "35.99", "361.2", "7"]
        item = self.viewer.topLevelItems[0].child(0)
        for idx in range(item.columnCount()):
            assert item.text(idx) == expected[idx]
            
        assert len(self.plotWidget.dataItem.scatter.data) == len(pts) + 1
        

    def test_plot_clicked(self, setup, qtbot, teardown):
        # test that clicking on the plot highlights the nearest plot in the viewer
        
        pts = self.plotWidget.dataItem.scatter.points()
        idx = random.randint(0, len(pts)-1)
        
        pos = pts[idx].pos()
        scenePos = self.plotWidget.viewBoxes[0].mapViewToScene(pos)
        scenePos = QPoint(*[int(round(x)) for x in [scenePos.x(), scenePos.y()]])
        
        size = pts[idx].size() // 2
        sizePad = 2 # don't know why this is necessary
        size += sizePad
        pos = QPoint(scenePos.x()+size, scenePos.y()+size)
        
        class MockMouseEvent:
            # mouse clicks aren't propogated into the pyqtgraph graphicsscene
            # so make a mock one at the right point
            def __init__(self, scenePos):
                self.sp = scenePos
            def scenePos(self):
                return self.sp
            
        with qtbot.waitSignal(self.plotWidget.currentPointChanged):
            qtbot.mouseMove(self.plot, pos=pos)
            
        event = MockMouseEvent(scenePos)
        signals = [(self.plotWidget.pointSelected, 'pointSelected'),
                   (self.viewer.currentItemChanged, 'currentItemChanged')]
        
        with qtbot.waitSignals(signals):
            self.plotWidget.plotClicked(event)
        

    @pytest.mark.skip("test not yet written")
    def test_viewer_clicked(self, setup, qtbot, teardown):
        # test that clicking on an item in the viewer highlights the corresponding point in the plot
        pass