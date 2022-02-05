from .test_cycletracks import TracksSetupTeardown
import pytest
import random
import re
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtCore import Qt

pytest_plugin = "pytest-qt"

class TestPreferences(TracksSetupTeardown):
    
    def extraSetup(self):
        self.prefDialog.show()
    
    def extraTeardown(self):
        self.prefDialog.close()
    
    @staticmethod
    def _subtractMonths(dt, months):
        return dt-timedelta(days=months*365/12)
        
    def test_plot_range(self, setup, qtbot, teardown):
        
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
            
            qtbot.wait(100)
                
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
        qtbot.wait(100)
        assert axis.tickTimestamps[0] <= dt.timestamp()
        
        
    @pytest.mark.skip("test not yet written")
    def test_plot_style(self, setup, qtbot, teardown):
        plotPref = self.prefDialog.pagesWidget.widget(0)

    def test_num_pb_sessions(self, setupKnownData, qtbot, teardown):
        self.prefDialog.pagesWidget.setCurrentIndex(1)
        pbPref = self.prefDialog.pagesWidget.widget(1)
        
        num = random.randrange(0, len(self.data))
        while num == pbPref.numSessionsBox.value():
            num = random.randrange(2, len(self.app.data))
        pbPref.numSessionsBox.setValue(num)
        
        button = self.prefDialog.buttonBox.button(QDialogButtonBox.Apply)
        with qtbot.waitSignal(button.clicked, timeout=10000):
            qtbot.mouseClick(button, Qt.LeftButton)
        
        df = self.data.df.sort_values('Avg. speed (km/h)', ascending=False)[:num]
        
        for row in range(self.pbTable.rowCount()):
            for colNum, colName in enumerate(self.pbTable.headerLabels):
                colName = re.sub(r"\s", " ", colName) # remove \n from avg speed
                text = self.pbTable.item(row, colNum).text()
                
                expected = df.iloc[row][colName]
                expected = self.data.fmtFuncs[colName](expected)
                expected = str(expected)
                
                assert text == expected
        
    def test_pb_month(self, setupKnownData, qtbot, teardown):
        self.prefDialog.pagesWidget.setCurrentIndex(1)
        pbPref = self.prefDialog.pagesWidget.widget(1)
        
        qtbot.wait(2500)