"""
Preferences for personal bests and data viewer.
"""

from datetime import date
from qtpy.QtWidgets import QSpinBox, QComboBox, QLabel, QVBoxLayout, QWidget, QCheckBox
from customQObjects.widgets import GroupBox
from customQObjects.core import Settings

class FuncComboBox(QComboBox):
    def __init__(self, *args, default=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.addItems(["sum", "max", "min", "mean"])
        if default is not None:
            self.setCurrentText(default)

class DataPreferences(QWidget):
    
    name = "Data"
    
    def __init__(self, mainWindow):
        super().__init__()
        self.mainWindow = mainWindow
        
        bestMonthGroup = GroupBox("Best month", layout="grid")
        self.bestMonthCriteria = QComboBox()
        self.bestMonthCriteria.addItems([
            "Time", "Distance", "Speed",  "Calories", "Gear"])
        
        self.bestMonthPB = QCheckBox()
        self.bestMonthPB.setToolTip("Find best month by number of PBs in the chosen category")
        
        self.pbRangeCombo = QComboBox()
        ranges = ["1 month", "3 months", "6 months", "1 year", "Current year", "All"]
        self.pbRangeCombo.addItems(ranges)
        self.bestMonthPB.clicked.connect(self.pbRangeCombo.setEnabled)
        
        bestMonthLabel = QLabel("Criterion")
        bestMonthGroup.addWidget(bestMonthLabel, 0, 0)
        bestMonthGroup.addWidget(self.bestMonthCriteria, 0, 1)
        usePBLabel = QLabel("Use PB count")
        bestMonthGroup.addWidget(usePBLabel, 1, 0)
        bestMonthGroup.addWidget(self.bestMonthPB, 1, 1)
        pbRangeLabel = QLabel("PB range")
        bestMonthGroup.addWidget(pbRangeLabel, 2, 0)
        bestMonthGroup.addWidget(self.pbRangeCombo, 2, 1)
        
        topSessionsGroup = GroupBox("Top sessions", layout="grid")
        self.numSessionsBox = QSpinBox()
        self.numSessionsBox.setMinimum(1)
        numSessionsLabel = QLabel("Number of top sessions")
        
        topSessionsGroup.addWidget(numSessionsLabel, 0, 0)
        topSessionsGroup.addWidget(self.numSessionsBox, 0, 1)
        
        summaryCriteriaGroup = GroupBox("Summary criteria", layout="grid")
        names = ["Time", "Distance", "Calories", "Speed", "Gear"]
        self.summaryComboBoxes = {}
        for row, name in enumerate(names):
            summaryCriteriaGroup.addWidget(QLabel(name), row, 0)
            box = FuncComboBox()
            self.summaryComboBoxes[name.lower()] = box
            summaryCriteriaGroup.addWidget(box, row, 1)
        
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(summaryCriteriaGroup)
        mainLayout.addWidget(bestMonthGroup)
        mainLayout.addWidget(topSessionsGroup)
        mainLayout.addStretch(1)

        self.setLayout(mainLayout)
        self.setCurrentValues()
        
        # apply initial state
        self.apply()
        
    def setCurrentValues(self):
        self.settings = Settings()
        self.settings.beginGroup("pb")
        
        bestMonthCriterion = self.settings.value("bestMonthCriterion", "distance").capitalize()
        self.bestMonthCriteria.setCurrentText(bestMonthCriterion)
        
        usePBcount = self.settings.value("usePBcount", False)
        self.bestMonthPB.setChecked(usePBcount)
        self.pbRangeCombo.setEnabled(usePBcount)
        
        numSessions = self.settings.value("numSessions", 5, int)
        self.numSessionsBox.setValue(numSessions)
        
        rng = self.settings.value("range", "All")
        items = [self.pbRangeCombo.itemText(idx) for idx in range(self.pbRangeCombo.count())]
        idx = items.index(rng)
        self.pbRangeCombo.setCurrentIndex(idx)
    
        for name, widget in self.summaryComboBoxes.items():
            funcName = self.settings.value(f"summary/{name}", None)
            if funcName is None:
                funcName = self.mainWindow.summary.getFunc(name)
            widget.setCurrentText(funcName)
        
        self.settings.endGroup()
        
    def apply(self):
        
        self.mainWindow.pb.emitStatusMessage()
        
        numSessions = self.numSessionsBox.value()
        self.mainWindow.pb.bestSessions.setNumRows(numSessions)
        
        bestMonthCriterion = self.bestMonthCriteria.currentText().lower()
        if self.bestMonthPB.isChecked():
            bestMonthPB = numSessions
        else:
            bestMonthPB = None
            
        months = self.pbRangeCombo.currentText()
        months = self.mainWindow.parseMonthRange(months)
            
        self.mainWindow.pb.bestMonth.setColumn(bestMonthCriterion, bestMonthPB, months)
        
        self.settings.beginGroup("pb")
        self.settings.setValue("bestMonthCriterion", bestMonthCriterion)
        self.settings.setValue("numSessions", numSessions)
        
        self.settings.setValue("usePBcount", self.bestMonthPB.isChecked())
        self.settings.setValue("range", self.pbRangeCombo.currentText())
        
        # make dict to pass to `setFunc` so it doesn't remake the viewer five times
        summaryFuncs = {}
        for name, widget in self.summaryComboBoxes.items():
            funcName = widget.currentText()
            self.settings.setValue(f"summary/{name}", funcName)
            summaryFuncs[name] = funcName
        self.mainWindow.summary.setFunc(summaryFuncs)
        
        self.settings.endGroup()
        
        self.mainWindow.statusBar().clearMessage()
    