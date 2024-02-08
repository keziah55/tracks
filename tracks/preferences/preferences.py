"""
Preferences dialog
"""
from qtpy.QtWidgets import (QAbstractScrollArea, QDialog, QDialogButtonBox, 
                            QListWidget, QVBoxLayout, QHBoxLayout)
from customQObjects.widgets import StackedWidget
# from .plotpref import PlotPreferences
# from .datapref import DataPreferences

class PreferencesDialog(QDialog):
    
    # pages = [PlotPreferences, DataPreferences]
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self._main_window = parent

        self.contentsWidget = QListWidget()
        self.pagesWidget = StackedWidget()
        
        # pages = sorted(self.pages, key=lambda widget: widget.name)
        
        # for page in pages:
        #     widget = page(self._main_window)
        #     self.pagesWidget.addWidget(widget)
        #     self.contentsWidget.addItem(widget.name)

        self.contentsWidget.currentItemChanged.connect(self.changePage)
        # self.contentsWidget.setCurrentRow(0)
        
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Apply|QDialogButtonBox.Close)
        
        okButton =  self.buttonBox.button(QDialogButtonBox.Ok)
        okButton.clicked.connect(self.ok)
        applyButton =  self.buttonBox.button(QDialogButtonBox.Apply)
        applyButton.clicked.connect(self.apply)
        closeButton = self.buttonBox.button(QDialogButtonBox.Close)
        closeButton.clicked.connect(self.close)

        horizontalLayout = QHBoxLayout()
        horizontalLayout.addWidget(self.contentsWidget)
        horizontalLayout.addWidget(self.pagesWidget)
        
        self.contentsWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(horizontalLayout)
        mainLayout.addWidget(self.buttonBox)

        self.setLayout(mainLayout)

        self.setWindowTitle("Preferences")

    def add_page(self, activity_name, page):
        contents_items = [self.contentsWidget.item(n).text() for n in range(self.contentsWidget.count())]
        if page.name not in contents_items:
            self.contentsWidget.addItem(page.name)
        if len(contents_items) == 0:
            self.contentsWidget.setCurrentRow(0)
        
        key = f"{activity_name}-{page.name.lower()}"
        self.pagesWidget.addWidget(page, key)

    def changePage(self, current, previous):
        if not current:
            current = previous
        
        pref_name = current.text().lower()
        self.show_page(pref_name)
            
        # self.pagesWidget.setCurrentIndex(self.contentsWidget.row(current))
        
    def show_page(self, pref_name):
        activity_name = self._main_window.current_activity.name
        key = f"{activity_name}-{pref_name}"
        
        try:
            self.pagesWidget.setCurrentKey(key)
        except KeyError:
            pass
        else:
            self.pagesWidget.currentWidget().setCurrentValues()
        
    def show(self):
        # for n in range(self.pagesWidget.count()):
        #     self.pagesWidget.widget(n).setCurrentValues()
        self.setWindowTitle(f"Preferences - {self._main_window.current_activity.name}")
        self.show_page(self.contentsWidget.currentItem().text().lower())
        
        super().show()
        
    def apply(self):
        self.pagesWidget.currentWidget().apply()
        
    def ok(self):
        # for idx in range(self.pagesWidget.count()):
            # self.pagesWidget.widget(idx).apply()
        for key, widget in self.pagesWidget.widgetDict.items():
            if key.startswith(self._main_window.current_activity.name):
                widget.apply()
        self.accept()