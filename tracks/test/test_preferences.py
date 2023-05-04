from .test_tracks import TracksSetupTeardown
from tracks.util import hourMinSecToFloat, floatToHourMinSec, parseDuration
import pytest
import random
import os.path
import re
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from qtpy.QtWidgets import QDialogButtonBox
from qtpy.QtCore import Qt

pytest_plugin = "pytest-qt"

class TestPreferences(TracksSetupTeardown):
    
    def extraSetup(self):
        self.dataIdx = 0
        self.plotIdx = 1
        self.prefDialog.show()
    
    def extraTeardown(self):
        self.prefDialog.close()
    
    @staticmethod
    def _subtractMonths(dt, months):
        return dt-timedelta(days=months*365/12)
        
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
        
    def test_plot_style(self, setup, qtbot):
        self.prefDialog.pagesWidget.setCurrentIndex(self.plotIdx)
        plotPref = self.prefDialog.pagesWidget.widget(self.plotIdx)
        
        with qtbot.waitSignal(plotPref.addPlotStyleButton.clicked):
             qtbot.mouseClick(plotPref.addPlotStyleButton, Qt.LeftButton)
            
        assert plotPref.customStyle.isEnabled()
        
        signals = [plotPref.customStyle.nameEdit.textChanged,
                   plotPref.customStyle.validateTimer.timeout]
        with qtbot.waitSignals(signals):
            plotPref.customStyle.setName("dark")
            
        assert plotPref.customStyle.saveButton.isEnabled() is False
        
        signals = [plotPref.customStyle.nameEdit.textChanged,
                   plotPref.customStyle.validateTimer.timeout]
        with qtbot.waitSignals(signals):
             qtbot.keyClick(plotPref.customStyle.nameEdit, "2")
            
        assert plotPref.customStyle.saveButton.isEnabled()
        
        newColours = {'speed':'#ff0000','distance':'#00ff00', 'time':'#0000ff', 
                      'calories':'#ffff00', 'odometer':'#00ffff', 'highlightPoint': '#ff00ff', 
                      'foreground':'#000000', 'background':'#ffffff'}
        newSymbols = {'speed': 'h', 'distance': 't3', 'time': '+', 'calories': 'star'}
        
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
        plotPref.customStyle._colourButtonWidgets['speed'].setColour('#000000')
        
        with qtbot.waitSignal(plotPref.customStyle.cancelButton.clicked):
            qtbot.mouseClick(plotPref.customStyle.cancelButton, Qt.LeftButton)
            assert plotPref.customStyle._colourButtonWidgets['speed'].colour != '#000000'
          
        plotPref.customStyle._colourButtonWidgets['speed'].setColour('#000000')
        
        with qtbot.waitSignal(plotPref.customStyle.saveStyle):
            qtbot.mouseClick(plotPref.customStyle.saveButton, Qt.LeftButton)
        
        assert plotPref.plotStyleList.currentText() == "Dark2"
        
        assert "dark2" in plotPref.mainWindow.plot.getValidStyles()
        
        with qtbot.waitSignal(plotPref.deletePlotStyleButton.clicked):
            qtbot.mouseClick(plotPref.deletePlotStyleButton, Qt.LeftButton)
            
        assert plotPref.plotStyleList.currentText() != "Dark2"
        assert "dark2" not in plotPref.mainWindow.plot.getValidStyles()
        assert ["dark", "light"] == plotPref.mainWindow.plot.getValidStyles()
        
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
        
        def sortKey(item):
            # round Speed to two decimal places when sorting
            if item.dtype == float:
                return np.around(item, decimals=2)
            else:
                # if it's a Date (pd.Timestamp) return directly
                return item
        
        df = self.data.df.sort_values(by=['Speed (km/h)', 'Date'], ascending=False, key=sortKey)
        
        for row in range(self.pbTable.rowCount()):
            for colNum, colName in enumerate(self.pbTable.headerLabels):
                text = self.pbTable.item(row, colNum).text()
                
                expected = df.iloc[row][colName]
                expected = self.data.fmtFuncs[colName](expected)
                expected = str(expected)
                
                if text != expected:
                    d = os.path.dirname(os.path.realpath(__file__))
                    d = os.path.join(d, "test_data")
                    os.makedirs(d, exist_ok=True)
                    df.to_csv(os.path.join(d, "test_num_pb_sessions_fail_sorted.csv"))
                    self.data.df.to_csv(os.path.join(d, "test_num_pb_sessions_fail_unsorted.csv"))
                    
                    h = [re.sub(r"\n", " ", name) for name in self.pbTable.headerLabels]
                    tmpText = ", ".join(h) + "\n"
                    for r in range(self.pbTable.rowCount()):
                        tmpRow = []
                        for c in range(len(self.pbTable.headerLabels)):
                            tmpRow.append(self.pbTable.item(r, c).text())
                        tmpText += ",".join(tmpRow) + "\n"
                    with open(os.path.join(d, "test_num_pb_sessions_fail_pbtable.csv"), "w") as fileobj:
                        fileobj.write(tmpText)
                
                assert text == expected
        
    def test_pb_month_criterion(self, setup, qtbot):
        self.prefDialog.pagesWidget.setCurrentIndex(self.dataIdx)
        pbPref = self.prefDialog.pagesWidget.widget(self.dataIdx)
        
        indices = list(range(pbPref.bestMonthCriteria.count()))
        random.shuffle(indices)
        if indices[0] == pbPref.bestMonthCriteria.currentIndex():
            val = indices.pop(0)
            indices.append(val)
            
        keys = {"Distance":"Distance (km)", "Speed":"Speed (km/h)"}
        
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
            elif column == "Speed (km/h)":
                values = [(monthYear, max(df[column])) for monthYear, df in months]
            else:
                values = [(monthYear, np.around(np.mean(df[column]))) for monthYear, df in months]
                
            values.sort(key=lambda item: item[1], reverse=True)
            best = values[0]
            
            assert self.app.pb.bestMonth.monthYear == best[0]
            
    def test_set_summary_criteria(self, setupKnownData, qtbot, variables):
        self.prefDialog.pagesWidget.setCurrentIndex(self.dataIdx)
        pbPref = self.prefDialog.pagesWidget.widget(self.dataIdx)
        
        aliases = {'Distance':'Distance (km)', 'Speed':'Speed (km/h)'}
        funcs = {'sum':sum, 'min':min, 'max':max, 'mean':np.mean}
        
        for name, comboBox in pbPref.summaryComboBoxes.items():
            num = comboBox.currentIndex()
            while num == comboBox.currentIndex():
                num = random.randrange(0, comboBox.count())
            comboBox.setCurrentIndex(num)
            
            with qtbot.waitSignal(self.viewer.viewerUpdated, timeout=variables.longWait):
                pbPref.apply()
                
            measure = comboBox.currentText()
            
            viewerName = aliases.get(name.capitalize(), name.capitalize())
            viewerNameNoNewline = re.sub(r"\n", " ", viewerName)
            col = self.viewer.headerLabels.index(viewerName)
            
            # known data is from April and May 2021
            groups = self.data.df.groupby(self.data.df['Date'] <= pd.Timestamp(year=2021, month=4, day=30))
            qtbot.wait(variables.shortWait)
            
            idx = 0
            for _, df in groups:
                
                data = df[viewerNameNoNewline]
                
                if name == 'time':
                    data = np.array([hourMinSecToFloat(t) for t in data])
                    
                expected = funcs[measure](data)
                
                if name == 'time':
                    expected = floatToHourMinSec(expected)
                
                expected = self.data.fmtFuncs[viewerNameNoNewline](expected)
                
                assert self.viewer.topLevelItems[idx].text(col) == expected
                idx += 1