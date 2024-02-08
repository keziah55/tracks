"""
Preferences for personal bests and data viewer.
"""

from qtpy.QtWidgets import QSpinBox, QComboBox, QLabel, QVBoxLayout, QWidget, QCheckBox
from qtpy.QtCore import Signal
from customQObjects.widgets import GroupBox
from tracks.util import parse_month_range, list_reduce_funcs

class FuncComboBox(QComboBox):
    def __init__(self, *args, default=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.addItems(list_reduce_funcs())
        if default is not None:
            self.setCurrentText(default)

class DataPreferences(QWidget):
    
    name = "Data"
    
    applied = Signal(bool)
    
    def __init__(self, activity, personal_bests_widget):
        super().__init__()
        self._activity = activity
        self._personal_bests_widget = personal_bests_widget
        
        bestMonthGroup = GroupBox("Best month", layout="grid")
        self.bestMonthCriteria = QComboBox()
        items = self._activity.filter_measures("summary", lambda s: s is not None)
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
                 for m in self._activity.measures.values() 
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
        
        pref = self._personal_bests_widget.state()
        
        bestMonthCriterion = pref.get("best_month_criterion", "distance").capitalize()
        self.bestMonthCriteria.setCurrentText(bestMonthCriterion)
        
        usePBcount = pref.get("pb_count", False)
        self.bestMonthPB.setChecked(False)#usePBcount)
        self.pbRangeCombo.setEnabled(False)#usePBcount)
        
        numSessions = pref.get("num_best_sessions", 5)
        self.numSessionsBox.setValue(numSessions)
        
        rng = pref.get("pb_month_range", None)
        if rng is None:
            rng = "All"
        items = [self.pbRangeCombo.itemText(idx) for idx in range(self.pbRangeCombo.count())]
        idx = items.index(rng)
        self.pbRangeCombo.setCurrentIndex(idx)
    
        for name, widget in self.summaryComboBoxes.items():
            m = self._activity.get_measure(name)
            func_name = m.summary.__name__
            widget.setCurrentText(func_name)
        
    def apply(self):
        
        num_sessions = self.numSessionsBox.value()
        
        bestMonthCriterion = self.bestMonthCriteria.currentText().lower()
        if self.bestMonthPB.isChecked():
            bestMonthPB = num_sessions
        else:
            bestMonthPB = None
            
        months = self.pbRangeCombo.currentText()
        months = parse_month_range(months)
        
        pb_month_args = (bestMonthCriterion, bestMonthPB, months)
        self._personal_bests_widget.update_values(num_sessions, pb_month_args)
            
        # make dict so it doesn't remake the viewer five times
        changed = False
        for name, widget in self.summaryComboBoxes.items():
            func_name = widget.currentText()
            m = self._activity.get_measure(name)
            if m.summary.__name__ != func_name:
                changed = True
                m.set_summary(func_name)
        
        self.applied.emit(changed)