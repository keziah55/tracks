"""
Preferences for personal bests and data viewer.
"""

from qtpy.QtWidgets import QSpinBox, QComboBox, QLabel, QVBoxLayout, QWidget, QCheckBox
from customQObjects.widgets import GroupBox
from customQObjects.core import Settings
from tracks.util import parse_month_range

class FuncComboBox(QComboBox):
    def __init__(self, *args, default=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.addItems(["sum", "max", "min", "mean"])
        if default is not None:
            self.setCurrentText(default)

class DataPreferences(QWidget):
    
    name = "Data"
    
    def __init__(self, _main_window):
        super().__init__()
        self._main_window = _main_window
        
        bestMonthGroup = GroupBox("Best month", layout="grid")
        self.bestMonthCriteria = QComboBox()
        items = self._main_window.current_activity.filter_measures("summary", lambda s: s is not None)
        items = [item.name for item in items.values()]
        self.bestMonthCriteria.addItems(items)
        
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
        
        names = [(m.slug, m.name) 
                 for m in self._main_window.current_activity.measures.values() 
                 if m.summary is not None]
        self.summaryComboBoxes = {}
        for row, (slug, name) in enumerate(names):
            summaryCriteriaGroup.addWidget(QLabel(name), row, 0)
            box = FuncComboBox()
            self.summaryComboBoxes[slug] = box
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
            func_name = self.settings.value(f"summary/{name}", None)
            if func_name is None:
                m = self._main_window.current_activity.get_measure(name)
                func_name = m.summary.__name__
                
            widget.setCurrentText(func_name)
        
        self.settings.endGroup()
        
    def apply(self):
        
        self._main_window.pb.emitStatusMessage()
        
        numSessions = self.numSessionsBox.value()
        self._main_window.pb.bestSessions.setNumRows(numSessions)
        
        bestMonthCriterion = self.bestMonthCriteria.currentText().lower()
        if self.bestMonthPB.isChecked():
            bestMonthPB = numSessions
        else:
            bestMonthPB = None
            
        months = self.pbRangeCombo.currentText()
        months = parse_month_range(months)
            
        self._main_window.pb.bestMonth.setColumn(bestMonthCriterion, bestMonthPB, months)
        
        self.settings.beginGroup("pb")
        self.settings.setValue("bestMonthCriterion", bestMonthCriterion)
        self.settings.setValue("numSessions", numSessions)
        
        self.settings.setValue("usePBcount", self.bestMonthPB.isChecked())
        self.settings.setValue("range", self.pbRangeCombo.currentText())
        
        # make dict to pass to `setFunc` so it doesn't remake the viewer five times
        # summaryFuncs = {}
        changed = False
        for name, widget in self.summaryComboBoxes.items():
            func_name = widget.currentText()
            self.settings.setValue(f"summary/{name}", func_name)
            # summaryFuncs[name] = funcName
            m = self._main_window.current_activity.get_measure(name)
            if m.summary.__name__ != func_name:
                changed = True
                m.set_summary(func_name)
        if changed:
            self._main_window._summary_value_changed()
        # self._main_window.summary.setFunc(summaryFuncs)
        
        self.settings.endGroup()
        
        self._main_window.statusBar().clearMessage()
    