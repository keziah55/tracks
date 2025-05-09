from .. import PersonalBests
from ..personalbests import NewPBDialog
from tracks.util import parseDate, parseDuration, hourMinSecToFloat
from tracks.test import MockParent
from qtpy.QtWidgets import QWidget, QVBoxLayout, QDialog
import pytest

pytest_plugin = "pytest-qt"


# parameters for test_new_data
def get_new_data(key):
    new_data_params = {
        "best session": (
            {
                "date": [parseDate("6 April 2021")],
                "time": [hourMinSecToFloat(parseDuration("00:42:15"))],
                "distance": [25.1],
                "calories": [375.4],
                "gear": [6],
            },
            "<center><span>New #2 speed - </span><span style='color: #f7f13b'>35.64 km/h</span>!<br><span>Congratulations!</span></center>",
            "<b>April 2021</b>: <b>155.93</b> km, <b>04:27:03</b> hours, <b>2332.1</b> calories",
        )
    }
    return new_data_params[key]


class TestPersonalBests:
    @pytest.fixture
    def setup(self, qtbot):
        # make Data object with known data
        self.parent = MockParent(random=False)
        self.pb = PersonalBests(self.parent.data, self.parent.activity)
        self.pb.newPBdialog.timer.setInterval(100)  # don't need 3 seconds for tests
        self.widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.pb)
        self.widget.setLayout(layout)

        qtbot.addWidget(self.widget)
        self.widget.setGeometry(100, 100, 500, 600)

        self.parent.data.data_changed.connect(self.pb.new_data)
        self.widget.show()

    @pytest.mark.parametrize("key", ["best session"])
    def test_new_data(self, setup, qtbot, key):
        new, expected_dialog, expected_label = get_new_data(key)

        signals = [
            (self.parent.data.data_changed, "data.data_changed"),
            (self.pb.newPBdialog.accepted, "dialog.accepted"),
        ]
        with qtbot.waitSignals(signals):
            self.parent.data.append(new)

        assert self.pb.newPBdialog.label.text() == expected_dialog

    def test_new_data_different_column(self, setup, qtbot, monkeypatch, variables):
        # test dialog message when table is sorted by Time
        new = {
            "date": [parseDate("7 April 2021")],
            "time": [hourMinSecToFloat(parseDuration("01:05:03"))],
            "distance": [25.08],
            "calories": [375.1],
            "gear": [6],
        }

        self.pb.horizontalHeader().sectionClicked.emit(1)
        qtbot.wait(variables.shortWait)

        # don't need dialog to pop up
        monkeypatch.setattr(NewPBDialog, "exec_", lambda *args: QDialog.Accepted)
        with qtbot.waitSignal(self.parent.data.data_changed):
            self.parent.data.append(new)

        expected = "<center><span>New #1 time - </span><span style='color: #f7f13b'>01:05:03</span>!<br><span>Congratulations!</span></center>"
        assert self.pb.newPBdialog.label.text() == expected

    def test_tied_data(self, setup, qtbot, monkeypatch):
        new = {
            "date": [parseDate("7 May 2021")],
            "time": [hourMinSecToFloat(parseDuration("00:42:11"))],
            "distance": [25.08],
            "calories": [375.1],
            "gear": [6],
        }

        # don't need dialog to pop up
        monkeypatch.setattr(NewPBDialog, "exec_", lambda *args: QDialog.Accepted)
        with qtbot.waitSignal(self.parent.data.data_changed):
            self.parent.data.append(new)

        rowNums = [self.pb.verticalHeaderItem(i).text() for i in range(self.pb.rowCount())]
        assert rowNums == ["1=", "1=", "3", "4", "5"]

        date0 = self.pb.item(0, 0).text()
        assert date0 == "07 May 2021"

        date1 = self.pb.item(1, 0).text()
        assert date1 == "04 May 2021"

    def test_sort_column(self, setup, qtbot, variables):
        # dict of sortable columns and list of expected dates
        columns = {
            "time": [
                "26 Apr 2021",
                "05 May 2021",
                "01 May 2021",
                "29 Apr 2021",
                "03 May 2021",
            ],
            "distance": [
                "26 Apr 2021",
                "29 Apr 2021",
                "03 May 2021",
                "27 Apr 2021",
                "02 May 2021",
            ],
            "speed": [
                "04 May 2021",
                "02 May 2021",
                "30 Apr 2021",
                "29 Apr 2021",
                "28 Apr 2021",
            ],
            "calories": [
                "26 Apr 2021",
                "29 Apr 2021",
                "03 May 2021",
                "27 Apr 2021",
                "02 May 2021",
            ],
        }

        for column, expected in columns.items():
            idx = self.pb._activity.measure_slugs.index(column)

            self.pb.horizontalHeader().sectionClicked.emit(idx)
            qtbot.wait(variables.shortWait)
            items = [self.pb.item(idx, 0).text() for idx in range(self.pb.rowCount())]
            assert items == expected

    def test_get_best_sessions(self, setup, qtbot):
        pb = self.pb._get_best_sessions(num=2, key="distance", order="ascending")
        expected = [
            {
                "date": "04 May 2021",
                "time": "00:42:11",
                "distance": "25.08",
                "gear": "6",
                "calories": "375.1",
            },
            {
                "date": "01 May 2021",
                "time": "00:43:19",
                "distance": "25.08",
                "gear": "6",
                "calories": "375.1",
            },
        ]

        for n, pb_data in enumerate(pb):
            for key, value in expected[n].items():
                assert pb_data[key] == value

        with pytest.raises(ValueError):
            self.pb._get_best_sessions(order="acsending")
