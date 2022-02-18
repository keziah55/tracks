from .test_cycletracks import TracksSetupTeardown
from cycleTracks.util import hourMinSecToFloat, parseDuration
import pytest
import random
import os.path
import re
import shutil
import numpy as np
from datetime import datetime, timedelta
from qtpy.QtWidgets import QDialogButtonBox
from qtpy.QtCore import Qt

pytest_plugin = "pytest-qt"

class TestPreferences(TracksSetupTeardown):
    
    def extraSetup(self):
        self.prefDialog.show()
    
    def extraTeardown(self):
        self.prefDialog.close()
    
    @staticmethod
    def _subtractMonths(dt, months):
        return dt-timedelta(days=months*365/12)
        
    def test_plot_range(self, setup, qtbot, variables):
        
        plotPref = self.prefDialog.pagesWidget.widget(0)
        plotPref.customRangeCheckBox.setChecked(False)
        
        rng = list(range(plotPref.plotRangeCombo.count()))
        random.shuffle(rng)
        default = 5
        if rng[0] == default:
            rng.pop(0)
            rng.append(default)
            
        signals = [(vb.sigXRangeChanged, f"vb{n}.sigXRangeChanged") 
                   for n, vb in enumerate(self.plot.plotWidget.viewBoxes)]
        
        lastDate = self.app.data.date[-1]
        
        numMonths = {"1 month":self._subtractMonths(lastDate, 1),
                     "3 months":self._subtractMonths(lastDate, 3),
                     "6 months":self._subtractMonths(lastDate, 6),
                     "1 year":self._subtractMonths(lastDate, 12),
                     "Current year":datetime(year=lastDate.year, month=1, day=1)}
 
        for n in rng:
            plotPref.plotRangeCombo.setCurrentIndex(n)
            
            with qtbot.waitSignals(signals, timeout=10000):
                button = self.prefDialog.buttonBox.button(QDialogButtonBox.Apply)
                qtbot.mouseClick(button, Qt.LeftButton)
                
            axis = self.plot.plotWidget.getAxis("bottom")
            
            qtbot.wait(variables.wait)
                
            assert axis.tickTimestamps[-1] >= lastDate.timestamp()
            text = plotPref.plotRangeCombo.currentText()
            if text == "All":
                dt = self.app.data.date[0]
            else:
                dt = numMonths[text]
                
            assert axis.tickTimestamps[0] <= dt.timestamp()
            
        with qtbot.waitSignal(plotPref.customRangeCheckBox.clicked):
            plotPref.customRangeCheckBox.click()
            
        plotPref.customRangeSpinBox.setValue(4)
        with qtbot.waitSignals(signals, timeout=10000):
            button = self.prefDialog.buttonBox.button(QDialogButtonBox.Apply)
            qtbot.mouseClick(button, Qt.LeftButton)
            
        assert axis.tickTimestamps[-1] >= lastDate.timestamp()
        dt = self._subtractMonths(lastDate, 4)
        qtbot.wait(variables.wait)
        assert axis.tickTimestamps[0] <= dt.timestamp()
        
        
    @pytest.mark.skip("test not yet written")
    def test_plot_style(self, setup, qtbot):
        plotPref = self.prefDialog.pagesWidget.widget(0)

    def test_num_pb_sessions(self, setup, qtbot):
        self.prefDialog.pagesWidget.setCurrentIndex(1)
        pbPref = self.prefDialog.pagesWidget.widget(1)
        
        num = random.randrange(2, len(self.data))
        while num == pbPref.numSessionsBox.value():
            num = random.randrange(2, len(self.data))
        pbPref.numSessionsBox.setValue(num)
        
        button = self.prefDialog.buttonBox.button(QDialogButtonBox.Apply)
        with qtbot.waitSignal(button.clicked, timeout=10000):
            qtbot.mouseClick(button, Qt.LeftButton)
        
        def sortKey(item):
            # round Avg Speed to two decimal places when sorting
            if isinstance(item, float):
                return np.around(item, decimals=2)
            else:
                # if it's a Date (pd.Timestamp) return directly
                return item
        
        df = self.data.df.sort_values(by=['Avg. speed (km/h)', 'Date'], ascending=False, key=sortKey)[:num]
        
        for row in range(self.pbTable.rowCount()):
            for colNum, colName in enumerate(self.pbTable.headerLabels):
                colName = re.sub(r"\s", " ", colName) # remove \n from avg speed
                text = self.pbTable.item(row, colNum).text()
                
                expected = df.iloc[row][colName]
                expected = self.data.fmtFuncs[colName](expected)
                expected = str(expected)
                
                # if text != expected:
                d = os.path.dirname(os.path.realpath(__file__))
                d = os.path.join(d, "test_data")
                if os.path.exists(d):
                    shutil.rmtree(d)
                os.mkdir(d)
                print(os.path.join(d, "test_num_pb_sessions_fail.csv"))
                df.to_csv(os.path.join(d, "test_num_pb_sessions_fail.csv"))
                
                assert text == expected
        
    def test_pb_month_criterion(self, setup, qtbot):
        self.prefDialog.pagesWidget.setCurrentIndex(1)
        pbPref = self.prefDialog.pagesWidget.widget(1)
        
        indices = list(range(pbPref.bestMonthCriteria.count()))
        random.shuffle(indices)
        if indices[0] == pbPref.bestMonthCriteria.currentIndex():
            val = indices.pop(0)
            indices.append(val)
            
        keys = {"Distance":"Distance (km)", "Avg. speed":"Avg. speed (km/h)"}
        
        for idx in indices:
            pbPref.bestMonthCriteria.setCurrentIndex(idx)
            
            button = self.prefDialog.buttonBox.button(QDialogButtonBox.Apply)
            with qtbot.waitSignal(button.clicked, timeout=10000):
                qtbot.mouseClick(button, Qt.LeftButton)
                
            criterion = pbPref.bestMonthCriteria.currentText()
            column = keys.get(criterion, criterion)
            
            months = self.data.splitMonths()
            if column in ["Distance (km)", "Calories"]:
                values = [(monthYear, sum(df[column])) for monthYear, df in months]
            elif column == "Time":
                values = [(monthYear, sum([hourMinSecToFloat(parseDuration(t)) for t in df[column]])) for monthYear, df in months]
            elif column == "Avg. speed (km/h)":
                values = [(monthYear, max(df[column])) for monthYear, df in months]
            else:
                values = [(monthYear, np.around(np.mean(df[column]))) for monthYear, df in months]
                
            values.sort(key=lambda item: item[1], reverse=True)
            best = values[0]
            
            assert self.app.pb.bestMonth.monthYear == best[0]
            
    @pytest.mark.skip("test not yet written")
    def test_set_summary_criteria(self, setup, qtbot):
        pass