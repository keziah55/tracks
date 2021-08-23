from .test_cycletracks import TracksSetupTeardown
import pytest
import random
from datetime import datetime
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtCore import Qt

pytest_plugin = "pytest-qt"

class TestPreferences(TracksSetupTeardown):
    
    @staticmethod
    def _subtractMonths(dt, months):
        if months >= dt.month:
            year = dt.year - 1
        else:
            year = dt.year
        month = (dt.month - months) % 12
        month += 1
        
        d = datetime(year=year, month=month, day=1)
        return d
    
    def test_plot_range(self, setup, qtbot, teardown):
        self.prefDialog.show()
        
        plotPref = self.prefDialog.pagesWidget.widget(0)
        
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
        assert axis.tickTimestamps[0] <= dt.timestamp()
        
    @pytest.mark.skip("test not yet written")
    def test_plot_style(self, setup, qtbot, teardown):
        plotPref = self.prefDialog.pagesWidget.widget(0)

    @pytest.mark.skip("test not yet written")
    def test_num_pb_sessions(self, setup, qtbot, teardown):
        pbPref = self.prefDialog.pagesWidget.widget(1)
        
    @pytest.mark.skip("test not yet written")
    def test_pb_month(self, setup, qtbot, teardown):
        pbPref = self.prefDialog.pagesWidget.widget(1)