from .test_tracks import TracksSetupTeardown
import pytest
import random
from pathlib import Path
import re
from pprint import pformat
import numpy as np
import polars as pl
from datetime import datetime, timedelta, date
from qtpy.QtWidgets import QDialogButtonBox
from qtpy.QtCore import Qt

pytest_plugin = "pytest-qt"


# @pytest.mark.skip("Don't test preferences")
class TestPreferences(TracksSetupTeardown):
    def extraSetup(self):
        self.dataIdx = 0
        self.plotIdx = 1
        self.prefDialog.show()

    def extraTeardown(self):
        self.prefDialog.close()

    @staticmethod
    def _subtractMonths(dt, months):
        return dt - timedelta(days=months * 365 / 12)

    def test_plot_range(self, setup, qtbot, variables):
        self.prefDialog.pagesWidget.setCurrentIndex(self.plotIdx)
        plotPref = self.prefDialog.pagesWidget.widget(self.plotIdx)
        plotPref.customRangeCheckBox.setChecked(False)

        rng = list(range(plotPref.plotRangeCombo.count()))
        random.shuffle(rng)
        default = 5
        if rng[0] == default:
            rng.pop(0)
            rng.append(default)

        signals = [
            (vb.sigXRangeChanged, f"vb{n}.sigXRangeChanged") for n, vb in enumerate(self.plot.plotWidget.view_boxes)
        ]

        lastDate = self.data.date[-1]

        numMonths = {
            "1 month": self._subtractMonths(lastDate, 1),
            "3 months": self._subtractMonths(lastDate, 3),
            "6 months": self._subtractMonths(lastDate, 6),
            "1 year": self._subtractMonths(lastDate, 12),
            "Current year": datetime(year=lastDate.year, month=1, day=1),
        }

        for n in rng:
            plotPref.plotRangeCombo.setCurrentIndex(n)

            with qtbot.waitSignals(signals, timeout=10000):
                button = self.prefDialog.buttonBox.button(QDialogButtonBox.Apply)
                qtbot.mouseClick(button, Qt.LeftButton)

            axis = self.plot.plotWidget.getAxis("bottom")

            qtbot.wait(variables.wait)

            # `date` has no `.timestamp()` method, so convert to datetime to get ts
            late_date_ts = datetime(lastDate.year, lastDate.month, lastDate.day).timestamp()

            assert axis.tickTimestamps[-1] >= late_date_ts
            text = plotPref.plotRangeCombo.currentText()
            if text == "All":
                dt = self.data.date[0]
            else:
                dt = numMonths[text]
            dt_ts = datetime(dt.year, dt.month, dt.day).timestamp()

            assert axis.tickTimestamps[0] <= dt_ts

        with qtbot.waitSignal(plotPref.customRangeCheckBox.clicked):
            plotPref.customRangeCheckBox.click()

        plotPref.customRangeSpinBox.setValue(4)
        with qtbot.waitSignals(signals, timeout=10000):
            button = self.prefDialog.buttonBox.button(QDialogButtonBox.Apply)
            qtbot.mouseClick(button, Qt.LeftButton)

        assert axis.tickTimestamps[-1] >= late_date_ts
        dt = self._subtractMonths(lastDate, 4)
        qtbot.wait(variables.wait)
        assert axis.tickTimestamps[0] <= dt_ts

    def test_plot_style(self, setup, qtbot):
        self.prefDialog.pagesWidget.setCurrentIndex(self.plotIdx)
        plotPref = self.prefDialog.pagesWidget.widget(self.plotIdx)

        with qtbot.waitSignal(plotPref.addPlotStyleButton.clicked):
            qtbot.mouseClick(plotPref.addPlotStyleButton, Qt.LeftButton)

        assert plotPref.customStyle.isEnabled()

        signals = [
            plotPref.customStyle.nameEdit.textChanged,
            plotPref.customStyle.validateTimer.timeout,
        ]
        with qtbot.waitSignals(signals):
            plotPref.customStyle.setName("dark")

        assert plotPref.customStyle.saveButton.isEnabled() is False

        signals = [
            plotPref.customStyle.nameEdit.textChanged,
            plotPref.customStyle.validateTimer.timeout,
        ]
        with qtbot.waitSignals(signals):
            qtbot.keyClick(plotPref.customStyle.nameEdit, "2")

        assert plotPref.customStyle.saveButton.isEnabled()

        newColours = {
            "speed": "#ff0000",
            "distance": "#00ff00",
            "time": "#0000ff",
            "calories": "#ffff00",
            "odometer": "#00ffff",
            "highlight_point": "#ff00ff",
            "foreground": "#000000",
            "background": "#ffffff",
        }
        newSymbols = {"speed": "h", "distance": "t3", "time": "+", "calories": "star"}

        for key, value in newColours.items():
            plotPref.customStyle._colourButtonWidgets[key].setColour(value)

        for key, value in newSymbols.items():
            symbolName = plotPref.customStyle.symbols[value].capitalize()
            plotPref.customStyle._symbolListWidgets[key].setCurrentText(symbolName)

        button = self.prefDialog.buttonBox.button(QDialogButtonBox.Apply)
        qtbot.mouseClick(button, Qt.LeftButton)
        qtbot.wait(200)
        assert plotPref.plotStyleList.currentText() == "Dark2"

        with qtbot.waitSignal(plotPref.editPlotStyleButton.clicked):
            qtbot.mouseClick(plotPref.editPlotStyleButton, Qt.LeftButton)
        assert plotPref.customStyle.isEnabled()
        assert plotPref.customStyle.nameEdit.text() == "dark2"
        plotPref.customStyle._colourButtonWidgets["speed"].setColour("#000000")

        with qtbot.waitSignal(plotPref.customStyle.cancelButton.clicked):
            qtbot.mouseClick(plotPref.customStyle.cancelButton, Qt.LeftButton)
            assert plotPref.customStyle._colourButtonWidgets["speed"].colour != "#000000"

        plotPref.customStyle._colourButtonWidgets["speed"].setColour("#000000")

        with qtbot.waitSignal(plotPref.customStyle.saveStyle):
            qtbot.mouseClick(plotPref.customStyle.saveButton, Qt.LeftButton)

        assert plotPref.plotStyleList.currentText() == "Dark2"

        assert "dark2" in plotPref._plot_widget.get_valid_styles()

        with qtbot.waitSignal(plotPref.deletePlotStyleButton.clicked):
            qtbot.mouseClick(plotPref.deletePlotStyleButton, Qt.LeftButton)

        assert plotPref.plotStyleList.currentText() != "Dark2"
        assert "dark2" not in plotPref._plot_widget.get_valid_styles()
        assert ["dark", "light"] == plotPref._plot_widget.get_valid_styles()

    def test_num_pb_sessions(self, setup, qtbot):
        self.prefDialog.pagesWidget.setCurrentIndex(self.dataIdx)
        pbPref = self.prefDialog.pagesWidget.widget(self.dataIdx)

        num = random.randrange(2, len(self.data))
        while num == pbPref.numSessionsBox.value():
            num = random.randrange(2, len(self.data))
        pbPref.numSessionsBox.setValue(num)

        button = self.prefDialog.buttonBox.button(QDialogButtonBox.Apply)
        with qtbot.waitSignal(button.clicked, timeout=10000):
            qtbot.mouseClick(button, Qt.LeftButton)

        df = self.data.df.sort("date")
        df = self.data.df.sort("speed", descending=True, maintain_order=True)

        for row in range(self.pbTable.rowCount()):
            for colNum, colName in enumerate(self.pbTable._activity.measure_slugs):
                text = self.pbTable.item(row, colNum).text()

                expected = df[row, colName]
                expected = self.pbTable._activity.get_measure(colName).formatted(expected)
                expected = str(expected)

                if text != expected:
                    p = Path(__file__).parent.joinpath("failed_test_data")
                    p.mkdir(parents=True, exist_ok=True)
                    df.to_csv(p.joinpath("test_num_pb_sessions_fail_sorted.csv"))
                    self.data.df.to_csv(p.joinpath("test_num_pb_sessions_fail_unsorted.csv"))

                    h = [re.sub(r"\n", " ", name) for name in self.pbTable._activity.header]
                    tmpText = ", ".join(h) + "\n"
                    for r in range(self.pbTable.rowCount()):
                        tmpRow = []
                        for c in range(len(self.pbTable._activity.header)):
                            tmpRow.append(self.pbTable.item(r, c).text())
                        tmpText += ",".join(tmpRow) + "\n"
                    with open(p.joinpath("test_num_pb_sessions_fail_pbtable.csv"), "w") as fileobj:
                        fileobj.write(tmpText)

                assert text == expected, "see test_num_pb_sessions_fail_*.csv files"

    def test_set_summary_criteria(self, setupKnownData, qtbot, variables):
        self.prefDialog.pagesWidget.setCurrentIndex(self.dataIdx)
        pbPref = self.prefDialog.pagesWidget.widget(self.dataIdx)

        aliases = {"Distance": "Distance (km)", "Speed": "Speed (km/h)"}

        def _mean(series):
            return series.mean()

        funcs = {"sum": sum, "min": min, "max": max, "mean": _mean}

        for name, comboBox in pbPref.summaryComboBoxes.items():
            num = comboBox.currentIndex()
            while num == comboBox.currentIndex():
                num = random.randrange(0, comboBox.count())
            num = 3
            comboBox.setCurrentIndex(num)

            with qtbot.waitSignal(self.viewer.viewerUpdated, timeout=variables.longWait):
                pbPref.apply()

            measure = comboBox.currentText()

            viewerName = aliases.get(name.capitalize(), name.capitalize())
            col = self.viewer._activity.header.index(viewerName)

            # known data is from April and May 2021
            ts = date(year=2021, month=5, day=1)
            groups = [self.data.df.filter(pl.col("date") >= ts), self.data.df.filter(pl.col("date") < ts)]

            qtbot.wait(variables.shortWait)

            for idx, df in enumerate(groups):
                data = df[name]
                expected = funcs[measure](data)
                expected = self.pbTable._activity.get_measure(name).formatted(expected)
                assert self.viewer.topLevelItems[idx].text(col) == expected
