from .. import DataViewer, Data
from ..edititemdialog import EditItemDialog
from tracks.util import monthYearToFloat, hourMinSecToFloat
from tracks.test import make_dataframe, MockParent
from qtpy.QtWidgets import QMessageBox, QDialog
from qtpy.QtCore import Qt
import random
from datetime import date, datetime
import numpy as np
import polars as pl
import pytest

pytest_plugin = "pytest-qt"


class TestDataViewer:
    @pytest.fixture
    def setup(self, qtbot):
        self.parent = MockParent()
        self._setup(qtbot)

    @pytest.fixture
    def setup_known_data(self, qtbot):
        self.parent = MockParent(random=False)
        self._setup(qtbot)

        for item in self.widget.top_level_items:
            self.widget.expandItem(item)

    def _setup(self, qtbot):
        self.widget = DataViewer(self.parent.data, self.parent.activity)
        self.parent.data.data_changed.connect(self.widget.new_data)
        qtbot.addWidget(self.widget)
        self.widget.setGeometry(100, 100, 500, 600)
        self.widget.show()

    def test_sort(self, setup, qtbot):
        columns = self.widget._activity.header
        columns = random.sample(columns, k=len(columns))
        if columns[0] == "Date":
            # should already be sorted by Date, so make sure this isn't the first
            # column to be clicked here
            item = columns.pop(0)
            columns.append(item)

        for column in columns:
            idx = self.widget._activity.header.index(column)

            expected = [item.text(idx) for item in self.widget.top_level_items]

            if column == "Date":
                expected = sorted(expected, key=monthYearToFloat)
            elif column == "Time":
                expected = sorted(expected, key=hourMinSecToFloat)
            else:
                expected = sorted(expected, key=float)

            for _ in range(2):
                expected.reverse()
                with qtbot.waitSignal(self.widget.viewer_sorted):
                    self.widget.header().sectionClicked.emit(idx)
                items = [item.text(idx) for item in self.widget.top_level_items]
                assert items == expected

    def test_new_data(self, setup, qtbot):
        # expand some headers
        min_expanded = 3
        num = len(self.widget.top_level_items) // 4
        num = max(min_expanded, num)
        expanded = random.sample(self.widget.top_level_items, num)
        for item in expanded:
            self.widget.expandItem(item)
        expanded = [item.text(0) for item in expanded]

        # new data
        df = make_dataframe(100)
        data = Data(df, self.parent.activity)
        self.parent.data = data

        self.widget.new_data()

        for item in self.widget.top_level_items:
            if item.isExpanded():
                assert item.text(0) in expanded

    def test_combine_data(self, setup, qtbot, monkeypatch):
        ret = self.widget.combine_rows()
        assert ret is None

        # pick a top-level item
        item = random.sample(self.widget.top_level_items, k=1)[0]
        idx = random.sample(range(item.childCount()), k=1)[0]
        item = item.child(idx)
        self.widget.setCurrentItem(item)

        ret = self.widget.combine_rows()
        assert ret is None

        # pick another
        item = random.sample(self.widget.top_level_items, k=1)[0]
        idx = random.sample(range(item.childCount()), k=1)[0]
        item = item.child(idx)
        item.setSelected(True)

        assert len(self.widget.selectedItems()) == 2

        date0, date1 = [item.text(0) for item in self.widget.selectedItems()]

        assert date0 != date1

        monkeypatch.setattr(QMessageBox, "warning", lambda *args: QMessageBox.Yes)
        with qtbot.assertNotEmitted(self.widget.data.data_changed):
            self.widget.combine_rows()

        gears = [item.text(5) for item in self.widget.selectedItems()]

        while len(set(gears)) == 1:
            # gears are the same, so select more items until gears differ
            item = random.sample(self.widget.top_level_items, k=1)[0]
            idx = random.sample(range(item.childCount()), k=1)[0]
            item = item.child(idx)
            item.setSelected(True)
            gears = [item.text(5) for item in self.widget.selectedItems()]

        for item in self.widget.selectedItems():
            # set the same date on all selected items, so only gears differ
            item.setText(0, date0)

        monkeypatch.setattr(QMessageBox, "warning", lambda *args: QMessageBox.Yes)
        with qtbot.assertNotEmitted(self.widget.data.data_changed):
            self.widget.combine_rows()

    def test_edit_remove_rows(self, setup_known_data, qtbot, monkeypatch):
        edit = ["2021-04-26", "2021-04-28", "2021-05-04"]
        remove = ["2021-04-30", "2021-05-03"]
        selectDates = ["26 Apr 2021", "28 Apr 2021", "04 May 2021", "30 Apr 2021", "03 May 2021"]

        for topLevelItem in self.widget.top_level_items:
            for idx in range(topLevelItem.childCount()):
                item = topLevelItem.child(idx)
                if item.text(0) in selectDates:
                    item.setSelected(True)

        dialogEdit = {
            0: {
                "calories": 450.2,
                "date": date(2021, 4, 16),
                "distance": 30.1,
                "gear": 6,
                "time": hourMinSecToFloat("00:53:27"),
            },
            2: {
                "calories": 375.1,
                "date": date(2021, 4, 28),
                "distance": 42.3,
                "gear": 6,
                "time": hourMinSecToFloat("01:00:05"),
            },
            8: {
                "calories": 375.1,
                "date": date(2021, 5, 4),
                "distance": 25.08,
                "gear": 6,
                "time": hourMinSecToFloat("00:42:11"),
            },
        }

        dialogRemove = [7, 4]
        monkeypatch.setattr(EditItemDialog, "exec_", lambda *args: QDialog.Accepted)
        monkeypatch.setattr(EditItemDialog, "get_values", lambda *args: (dialogEdit, dialogRemove))

        with qtbot.waitSignals([self.parent.data.data_changed] * 2):
            self.widget._edit_items()

        for d in remove:
            year, month, day = d.split("-")
            d = date(int(year), int(month), int(day))
            assert d not in self.parent.data["date"]

        for dct in dialogEdit.values():
            row = self.parent.data.df.filter(pl.col("date") == dct["date"])
            for col in dct.keys():
                assert row[col][0] == dct[col]

        # check that speed has updated for row where time and distance were changed
        dct = dialogEdit[2]
        expected = dct["distance"] / dct["time"]
        row = self.parent.data.df.filter(pl.col("date") == dct["date"])
        speed = row["speed"]
        assert np.isclose(speed, expected)

    def test_edititemdialog(self, setup_known_data, qtbot):
        # like above test, but make the EditItemDialog directly, so we can test user input
        # edit = ["2021-04-26", "2021-04-28", "2021-05-04"]
        # remove = ["2021-04-30", "2021-05-03"]

        # editDates = [
        #     datetime.strptime(d, "%Y-%m-%d").strftime("%d %b %Y") for d in edit
        # ]
        # removeDates = [
        #     datetime.strptime(d, "%Y-%m-%d").strftime("%d %b %Y") for d in remove
        # ]

        editDates = ["26 Apr 2021", "28 Apr 2021", "04 May 2021"]
        removeDates = ["30 Apr 2021", "03 May 2021"]

        selectDates = editDates + removeDates

        for topLevelItem in self.widget.top_level_items:
            for idx in range(topLevelItem.childCount()):
                item = topLevelItem.child(idx)
                if item.text(0) in selectDates:
                    item.setSelected(True)

        newValues = [
            {
                "calories": 450.2,
                "date": "16-04-2021",
                "distance": 30.1,
                "gear": 6,
                "time": "00:53:27",
            },
            {
                "calories": 375.1,
                "date": "28-04-2021",
                "distance": 42.3,
                "gear": 6,
                "time": "01:00:05",
            },
            {
                "calories": 375.1,
                "date": "04-05-2021",
                "distance": 25.08,
                "gear": 6,
                "time": "00:42:11",
            },
        ]
        newValues = dict(zip(editDates, newValues))

        dialog = EditItemDialog(
            self.widget._activity,
            self.widget.selectedItems(),
            self.widget._activity.header,
        )
        dialog.show()

        # pick a check box and toggle it off then on
        idx = random.randrange(0, len(dialog.rows))
        for n in range(2):
            with qtbot.waitSignal(dialog.rows[idx].checkBox.clicked):
                qtbot.mouseClick(dialog.rows[idx].checkBox, Qt.LeftButton)
            for i, row in enumerate(dialog.rows):
                for tableItem in row.tableItems.values():
                    if i == idx and n == 0:
                        expectedFlags = Qt.ItemIsSelectable
                    else:
                        expectedFlags = Qt.ItemIsEditable | Qt.ItemIsEnabled
                    assert tableItem.flags() == expectedFlags

        for row in dialog.rows:
            if row.tableItems["date"].text() in removeDates:
                with qtbot.waitSignal(row.checkBox.clicked):
                    qtbot.mouseClick(row.checkBox, Qt.LeftButton)
                for tableItem in row.tableItems.values():
                    assert tableItem.flags() == Qt.ItemIsSelectable

            if row.tableItems["date"].text() in editDates:
                new = newValues[row.tableItems["date"].text()]
                for key, value in new.items():
                    row.tableItems[key].setText(str(value))

        values, remove = dialog.get_values()
        assert set(remove) == {4, 7}
        expected = {
            0: {
                "calories": 450.2,
                "date": date(2021, 4, 16),  # pd.Timestamp("2021-04-16 00:00:00"),
                "distance": 30.1,
                "gear": 6,
                "time": hourMinSecToFloat("00:53:27"),
            },
            2: {
                "calories": 375.1,
                "date": date(2021, 4, 28),  # pd.Timestamp("2021-04-28 00:00:00"),
                "distance": 42.3,
                "gear": 6,
                "time": hourMinSecToFloat("01:00:05"),
            },
            8: {
                "calories": 375.1,
                "date": date(2021, 5, 4),  # pd.Timestamp("2021-05-04 00:00:00"),
                "distance": 25.08,
                "gear": 6,
                "time": hourMinSecToFloat("00:42:11"),
            },
        }
        assert values == expected
