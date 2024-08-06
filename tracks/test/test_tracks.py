# from tracks.tracks import Tracks
import tracks.tracks
import tracks.activities
from tracks.util import parseDuration, hourMinSecToFloat
from qtpy.QtCore import Qt, QPoint
import random
from . import make_dataframe
import tempfile
from datetime import datetime, date
from pathlib import Path
import polars as pl
import pytest

pytest_plugin = "pytest-qt"


class TracksSetupTeardown:
    @pytest.fixture
    def setup(self, qtbot, monkeypatch, patch_settings):
        self.tmpfile = tempfile.NamedTemporaryFile()
        self.size = 100
        make_dataframe(random=True, size=self.size, path=self.tmpfile.name)

        def mockGetFile(*args, **kwargs):
            return Path(self.tmpfile.name)

        monkeypatch.setattr(tracks.activities.ActivityManager, "_activity_csv_file", mockGetFile)

        self._setup()
        qtbot.addWidget(self.app)

        yield
        self.extraTeardown()
        self.app.close()

        # can't do this with a fixture in conf file, as it's called when this method is called
        # presumably, qt has a lock on the file, so wouldn't be deleted in that case
        self._removeTmpConfig()

    @pytest.fixture
    def setupKnownData(self, qtbot, monkeypatch, patch_settings):
        self.tmpfile = tempfile.NamedTemporaryFile()
        make_dataframe(random=False, path=self.tmpfile.name)

        def mockGetFile(*args, **kwargs):
            return Path(self.tmpfile.name)

        monkeypatch.setattr(tracks.activities.ActivityManager, "_activity_csv_file", mockGetFile)
        # monkeypatch.setattr(tracks.tracks, "get_activity_csv", mockGetFile)
        # monkeypatch.setattr(tracks.activities, "get_activity_csv", mockGetFile)

        self._setup()
        qtbot.addWidget(self.app)

        yield
        self.extraTeardown()
        self.app.close()

        # can't do this with a fixture in conf file, as it's called when this method is called
        # presumably, qt has a lock on the file, so wouldn't be deleted in that case
        self._removeTmpConfig()

    def _setup(self):
        self.app = tracks.tracks.Tracks()
        activity_name = "cycling"
        ao = self.app._activity_manager.get_activity_objects(activity_name)

        self.addData = ao.add_data
        self.viewer = ao.data_viewer
        self.plot = ao.plot
        self.plotWidget = self.plot.plotWidget
        self.pb = ao.personal_bests
        self.pbTable = self.pb
        self.prefDialog = self.app.prefDialog
        self.data = ao.data

        self.app.showMaximized()
        # self.app.prefDialog.ok() # see https://github.com/keziah55/cycleTracks/commit/9e0c05f7d19b33a61a52a959adcdc7667cd7b924

        self.extraSetup()

    def _removeTmpConfig(self):
        appName = "Tracks"
        orgName = "Tracks"
        confFile = Path(__file__).parent.joinpath(".config", orgName, appName + ".conf")
        if confFile.exists():
            confFile.unlink()

    def extraSetup(self):
        self.pb.newPBdialog.setTimeout(100)

    def extraTeardown(self):
        pass


class TestTracks(TracksSetupTeardown):
    def test_add_data(self, setup, qtbot):
        numTopLevelItems = len(self.viewer.topLevelItems)
        pts = self.plotWidget.dataItem.scatter.data

        row = 0
        year = date.today().year + 1
        values = [f"5 Jan {year}", "40:23", "24.22", "361.2", "7"]
        for col in range(self.addData.table.columnCount()):
            value = values[col]
            self.addData.table.item(row, col).setText(str(value))

        with qtbot.waitSignal(self.addData.newData):
            qtbot.mouseClick(self.addData.okButton, Qt.LeftButton)

        assert len(self.viewer.topLevelItems) == numTopLevelItems + 1
        expected = [f"05 Jan {year}", "00:40:23", "24.22", "35.99", "361.2", "7"]
        item = self.viewer.topLevelItems[0].child(0)
        for idx in range(item.columnCount()):
            assert item.text(idx) == expected[idx]

        assert len(self.plotWidget.dataItem.scatter.data) == len(pts) + 1

    def test_plot_clicked(self, setup, qtbot, variables):
        # test that clicking on the plot highlights the nearest plot in the viewer

        self.plotWidget.set_x_axis_range(None)  # ensure all points visible in plotting area

        pts = self.plotWidget.dataItem.scatter.points()
        idx = random.randint(0, len(pts) - 1)

        pos = pts[idx].pos()
        scenePos = self.plotWidget.view_boxes[0].mapViewToScene(pos)
        scenePos = QPoint(*[int(round(x)) for x in [scenePos.x(), scenePos.y()]])

        size = pts[idx].size() // 2
        sizePad = 2  # don't know why this is necessary
        size += sizePad
        pos = QPoint(scenePos.x() + size, scenePos.y() + size)

        class MockMouseEvent:
            # mouse clicks aren't propagated into the pyqtgraph graphics scene
            # so make a mock one at the right point
            def __init__(self, scenePos):
                self.sp = scenePos

            def scenePos(self):
                return self.sp

        qtbot.wait(variables.wait)
        with qtbot.waitSignal(self.plotWidget.current_point_changed):
            qtbot.mouseMove(self.plot, pos=pos, delay=variables.mouseDelay)
        qtbot.wait(variables.wait)
        
        event = MockMouseEvent(scenePos)
        signals = [
            (self.plotWidget.point_selected, "point_selected"),
            (self.viewer.currentItemChanged, "currentItemChanged"),
        ]

        with qtbot.waitSignals(signals):
            self.plotWidget._plot_clicked(event)

    def test_viewer_clicked(self, setup, qtbot):
        # test that clicking on an item in the viewer highlights the corresponding point in the plot
        item = self.viewer.topLevelItems[0]
        with qtbot.waitSignal(self.viewer.itemExpanded):
            self.viewer.expandItem(item)
        signals = [
            (self.viewer.itemSelected, "viewer.itemSelected"),
            (self.plotWidget.current_point_changed, "plotWidget.current_point_changed"),
        ]
        with qtbot.waitSignals(signals):
            self.viewer.setCurrentItem(item.child(0))
        expectedIdx = self.size - 1
        assert self.plotWidget._current_point["index"] == expectedIdx
        assert self.plotWidget._highlight_point_item == self.plotWidget.dataItem.scatter.points()[expectedIdx]

    def test_pb_table_clicked(self, setup, qtbot):
        # similar to above, but for pb table
        item = self.pbTable.item(1, 0)
        signals = [
            (self.pb.itemSelected, "pbTable.itemSelected"),
            (self.plotWidget.current_point_changed, "plotWidget.current_point_changed"),
        ]
        with qtbot.waitSignals(signals):
            self.pbTable.setCurrentItem(item)

        expectedIdx = self.data.formatted("date").index(item.text())
        assert self.plotWidget._current_point["index"] == expectedIdx
        assert self.plotWidget._highlight_point_item == self.plotWidget.dataItem.scatter.points()[expectedIdx]

    def test_plot_update(self, setup, qtbot):
        # test that, when new data added, the plot auto-rescales so the new points are visible

        self.plot.set_x_axis_range(months=6)

        lastDate = self.data["date"][-1]
        year = lastDate.year
        month = lastDate.month
        day = 28  # latest date that appears in all months
        if month == 12:
            month = 0
            year += 1
        newDate = date(year=year, month=month + 1, day=day)

        newData = {
            "date": [newDate],
            "time": [hourMinSecToFloat(parseDuration("40:20"))],
            "distance": [25.08],
            "calories": [375.1],
            "gear": [6],
        }

        oldXRange = self.plot.plotWidget.plotItem.vb.xRange[1]

        with qtbot.waitSignal(self.data.dataChanged):
            self.data.append(newData)

        newXRange = self.plot.plotWidget.plotItem.vb.xRange[1]

        assert oldXRange != newXRange
        oldMonth = datetime.fromtimestamp(oldXRange).month
        if oldMonth == 12:
            oldMonth = 0
        # check newDate is visible
        assert newDate.month <= datetime.fromtimestamp(newXRange).month
