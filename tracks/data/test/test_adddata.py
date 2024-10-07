from .. import AddData
from tracks.util import hourMinSecToFloat
from tracks.test.mockparent import load_activity
from qtpy.QtCore import Qt
from datetime import date
import random
import pytest

pytest_plugin = "pytest-qt"


class TestAddData:
    @pytest.fixture
    def setup(self, qtbot, activity_json_path):
        act = load_activity(activity_json_path)

        self.widget = AddData(act)
        qtbot.addWidget(self.widget)
        self.widget.move(100, 100)
        self.widget.show()

        self.table = self.widget.table
        self.okButton = self.widget.okButton
        self.addLineButton = self.widget.addLineButton
        self.rmvLineButton = self.widget.rmvLineButton

    def test_empty_row(self, setup, qtbot):
        assert self.table.rowCount() == 1
        assert self.table.columnCount() == 5

        today = date.today()
        expected = f'{today.day} {today.strftime("%b %Y")}'
        assert self.table.item(0, 0).text() == expected

        for col in range(1, self.table.columnCount()):
            assert self.table.item(0, col).text() == ""

    def test_add_data(self, setup, qtbot):
        values = {
            "Date": ["1/1/21", "9 Feb 2021", "31/12/20", "15 Jan 21"],
            "Time": ["31:15", "21:36", "45:02", "36:04"],
            "Distance (km)": [17, 11.23, 22.5, 18.75],
            "Calories": [255.3, 165.3, 275.9, 300.4],
            "Gear": [6, 6, 7, 5],
        }

        expected = {
            "date": [
                date(year=2020, month=12, day=31),
                date(year=2021, month=1, day=1),
                date(year=2021, month=1, day=15),
                date(year=2021, month=2, day=9),
            ],
            "time": [
                hourMinSecToFloat("00:45:02"),
                hourMinSecToFloat("00:31:15"),
                hourMinSecToFloat("00:36:04"),
                hourMinSecToFloat("00:21:36"),
            ],
            "distance": [22.5, 17.0, 18.75, 11.23],
            "calories": [275.9, 255.3, 300.4, 165.3],
            "gear": [7, 6, 5, 6],
        }

        def check_values(newValues):
            return newValues == expected

        numRows = 0

        for row in range(4):
            if row != 0:
                with qtbot.waitSignal(self.addLineButton.clicked):
                    qtbot.mouseClick(self.addLineButton, Qt.LeftButton)
            numRows += 1
            assert self.table.rowCount() == numRows

            keys = iter(values.keys())
            for col in range(self.table.columnCount()):
                key = next(keys)
                value = values[key][row]
                self.table.item(row, col).setText(str(value))

        assert self.okButton.isEnabled()

        with qtbot.waitSignal(self.widget.new_data, check_params_cb=check_values):
            qtbot.mouseClick(self.okButton, Qt.LeftButton)

    def test_remove_line(self, setup, qtbot):
        num = 3
        for _ in range(num):
            with qtbot.waitSignal(self.addLineButton.clicked):
                qtbot.mouseClick(self.addLineButton, Qt.LeftButton)

        assert self.table.rowCount() == num + 1

        while self.table.rowCount() > 0:
            row = random.randrange(0, self.table.rowCount())
            col = random.randrange(0, self.table.columnCount())

            self.table.setCurrentCell(row, col)

            with qtbot.waitSignal(self.widget.row_removed):
                qtbot.mouseClick(self.rmvLineButton, Qt.LeftButton)

    def test_invalid(self, setup, qtbot, variables):
        valid = ["30 Jan 2021", "30:04", 16.05, 240.1, 6]
        invalid = ["blah", "not a time", "a string", "", 5.5]

        for col in range(self.table.columnCount()):
            # make row with valid data
            for idx in range(self.table.columnCount()):
                text = str(valid[idx])
                self.table.item(0, idx).setText(text)
            qtbot.wait(variables.shortWait)
            assert self.okButton.isEnabled()

            # set 'col' to invalid value
            signals = [
                (self.widget.validateTimer.timeout, "timeout"),
                (self.widget.invalid, "invalid"),
            ]
            callbacks = [None, lambda r, c: r == 0 and c == col]
            text = str(invalid[col])

            with qtbot.waitSignals(signals, check_params_cbs=callbacks, timeout=5000):
                self.table.item(0, col).setText(text)
                self.table.focusNextChild()

            assert self.okButton.isEnabled() is False
            assert self.table.item(0, col).background() == self.widget._invalid_brush
