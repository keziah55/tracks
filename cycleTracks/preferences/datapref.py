"""
Preferences for personal bests and data viewer.
"""

from qtpy.QtWidgets import QSpinBox, QComboBox, QLabel, QVBoxLayout, QWidget
from customQObjects.widgets import GroupWidget
from customQObjects.core import Settings

class FuncComboBox(QComboBox):
    def __init__(self, *args, default=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.addItems(["sum", "max", "min", "mean"])
        if default is not None:
            self.setCurrentText(default)

class DataPreferences(QWidget):
    
    def __init__(self, mainWindow):
        super().__init__()
        self.mainWindow = mainWindow
        
        bestMonthGroup = GroupWidget("Best month", layout="grid")
        self.bestMonthCriteria = QComboBox()
        self.bestMonthCriteria.addItems(["Time", "Distance", "Speed", 
                                         "Calories", "Gear"])
        
        bestMonthLabel = QLabel("Criterion:")
        bestMonthGroup.addWidget(bestMonthLabel, 0, 0)
        bestMonthGroup.addWidget(self.bestMonthCriteria, 0, 1)
        
        topSessionsGroup = GroupWidget("Top sessions", layout="grid")
        self.numSessionsBox = QSpinBox()
        self.numSessionsBox.setMinimum(1)
        numSessionsLabel = QLabel("Number of top sessions:")
        
        topSessionsGroup.addWidget(numSessionsLabel, 0, 0)
        topSessionsGroup.addWidget(self.numSessionsBox, 0, 1)
        
        summaryCriteriaGroup = GroupWidget("Summary criteria", layout="grid")
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
        
        numSessions = self.settings.value("numSessions", 5, int)
        self.numSessionsBox.setValue(numSessions)
        
        for name, widget in self.summaryComboBoxes.items():
            funcName = self.settings.value(f"summary/{name}", None)
            if funcName is None:
                funcName = self.mainWindow.summary.getFunc(name)
            widget.setCurrentText(funcName)
        
        self.settings.endGroup()
        
    def apply(self):
        
        bestMonthCriterion = self.bestMonthCriteria.currentText().lower()
        self.mainWindow.pb.bestMonth.setColumn(bestMonthCriterion)
        
        numSessions = self.numSessionsBox.value()
        self.mainWindow.pb.bestSessions.setNumRows(numSessions)
        
        self.settings.beginGroup("pb")
        self.settings.setValue("bestMonthCriterion", bestMonthCriterion)
        self.settings.setValue("numSessions", numSessions)
        
        # make dict to pass to `setFunc` so it doesn't remake the viewer five times
        summaryFuncs = {}
        for name, widget in self.summaryComboBoxes.items():
            funcName = widget.currentText()
            self.settings.setValue(f"summary/{name}", funcName)
            summaryFuncs[name] = funcName
        self.mainWindow.summary.setFunc(summaryFuncs)
        
        self.settings.endGroup()
    