"""
QTreeWidget showing data from CycleData.
"""

from PyQt5.QtWidgets import (QTreeWidget, QTreeWidgetItem, QHeaderView, 
                             QAbstractItemView, QMessageBox, QMenu, QAction)
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot
from PyQt5.QtGui import QFontMetrics, QKeySequence
import re
import numpy as np
from .edititemdialog import EditItemDialog
from cycleTracks.util import(checkHourMinSecFloat, checkMonthYearFloat, isFloat, 
                             hourMinSecToFloat, monthYearToFloat)

class CycleTreeWidgetItem(QTreeWidgetItem):
    """ QTreeWidgetItem subclass, with __lt__ method overridden, so that 
        the QTreeWidget can sort the items, where each column may contain
        a number, month and year, or time in HH:MM.ss.
    
        This requires a `sortColumn` property to be added. This must be set
        to the desired sort column index on every instance of this object
        before calling `QTreeWidget.sortItems()`. As far as I can tell, the
        `idx` arg to `QTreeWidget.sortItems()` is ignored.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sortColumn = 0
    
    def __lt__(self, other):
        item0 = self.text(self.sortColumn)
        item1 = other.text(self.sortColumn)
        if isFloat(item0) and isFloat(item1):
            return float(item0) < float(item1)
        elif checkMonthYearFloat(item0) and checkMonthYearFloat(item1):
            value0 = monthYearToFloat(item0)
            value1 = monthYearToFloat(item1)
            return value0 < value1
        elif checkHourMinSecFloat(item0) and checkHourMinSecFloat(item1):
            value0 = hourMinSecToFloat(item0)
            value1 = hourMinSecToFloat(item1)
            return value0 < value1
        else:
            return item0 < item1
        
    @property 
    def sortColumn(self):
        return self._sortColumn
    
    @sortColumn.setter 
    def sortColumn(self, value):
        self._sortColumn = value
        

class CycleDataViewer(QTreeWidget):
    """ QTreeWidget showing cycling data, split by month.
    
        Each item in the tree shows a summary: month, total time, total distance,
        max. avg. speed and total calories.
        
        The tree can be sorted by double clicking on the header.
    
        Parameters
        ----------
        parent : QWidget
            Main window/widget with :class:`CycleData` object
        widthSpace : int
            Spacing to add to width in `sizeHint`. Default is 5.
    """
    
    itemSelected = Signal(object)
    """ itemSelected(CycleTreeWidgetItem `item`)
    
        Emitted when an item in the tree is selected, either by clicking
        on it or by navigating with the up or down keys.
    """
    
    viewerSorted = Signal()
    """ viewerSorted()
    
        Emitted after the CycleDataViewer items have been sorted.
    """
    
    requestRemoveData = Signal(list)
    """ requestRemoveData(list `items`)
    
        When data are removed/edited, request that these items are removed from 
        the CycleData object. `items` is a list of dates to be removed.
    """
    
    requestAddData = Signal(dict)
    """ requestAddData(dict `values`)
    
        When data are removed/edited, request that these new values are added  
        to the CycleData object.
    """
    
    def __init__(self, parent, widthSpace=10):
        super().__init__()
        
        self.parent = parent
        
        self.widthSpace = widthSpace
        self.dateFmt = "%d %b %Y"
        
        self.headerLabels = ['Date', 'Time', 'Distance (km)', 'Avg. speed\n(km/h)', 
                             'Calories', 'Gear']
        self.setHeaderLabels(self.headerLabels)
        self.header().setStretchLastSection(False)
        # make header tall enough for two rows of text (avg speed has line break)
        font = self.header().font()
        metrics = QFontMetrics(font)
        height = metrics.height()
        self.header().setMinimumHeight(height*2)
        # align header text centrally
        for idx in range(len(self.headerLabels)):
            self.headerItem().setTextAlignment(idx, Qt.AlignCenter)
            
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        self.makeTree()
        
        self.sortColumn = None
        self.sortDescending = [True for _ in range(len(self.headerLabels))]
        self.header().setSectionsClickable(True)
        self.header().sectionClicked.connect(self.sortTree)
        
        self.currentItemChanged.connect(self._itemChanged)
        
        self.sortTree(0)
        
        msg = "Browse all sessions, grouped by month. Click on the headers \n"
        msg += "to sort by that metric in ascending or descending order.\n"
        msg += "Click on a session to highlight it in the plot."
        self.setToolTip(msg)
        
        self.editAction = QAction("Edit")
        self.editAction.setShortcut(QKeySequence("Ctrl+E"))
        self.editAction.triggered.connect(self._editItem)
        self.addAction(self.editAction)
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._showContextMenu)
        
    def _showContextMenu(self, pos):
        menu = QMenu()
        menu.addAction(self.editAction)
        menu.exec_(self.mapToGlobal(pos))
        
    def _editItem(self):
        items = [item for item in self.selectedItems() if item not in self.topLevelItems]
        if items:
            dialog = EditItemDialog(items, self.headerLabels)
            result = dialog.exec_()
            if result == EditItemDialog.Accepted:
                idx = self.headerLabels.index('Date')
                # TODO make QTreeWidgetItem subclass that stores the pandas index
                # (does the pandas index change if rows are dropped/merged?)
                # Add CycleData method to update rows
                # Change CycleData.removeRows to take indices (and combineRows)
                # Add combine rows to context menu
                selectedIdx = [self.items[item]['index'] for item in items]
                selectedDates = [item.text(idx) for item in items]
                # TODO edit data directly instead of removing and adding
                self.requestRemoveData.emit(selectedDates)
                values = dialog.getValues()
                self.requestAddData.emit(values)
    
    def sizeHint(self):
        width = self.header().length() + self.widthSpace
        height = super().sizeHint().height()
        return QSize(width, height)
    
    @property
    def data(self):
        return self.parent.data
    
    @property 
    def topLevelItems(self):
        """ List of top level QTreeWidgetItems. """
        items = [self.topLevelItem(i) for i in range(self.topLevelItemCount())]
        return items
    
    @Slot()
    def newData(self):
        expanded = []
        for item in self.topLevelItems:
            if item.isExpanded():
                expanded.append(item.text(0))
        self.clear()
        self.makeTree()
        for item in self.topLevelItems:
            if item.text(0) in expanded:
                self.expandItem(item)
                
    @Slot(int)
    def sortTree(self, idx):
        """ Sort the tree based on column `idx`. """
        
        # switch sort order if clicked column is already selected
        if idx == self.sortColumn:
            self.sortDescending[idx] = not self.sortDescending[idx]
            
        order = Qt.DescendingOrder if self.sortDescending[idx] else Qt.AscendingOrder
        
        # set sort column index
        for rootItem in self.topLevelItems:
            rootItem.sortColumn = idx
        self.sortColumn = idx
            
        # make header label for sort column italic
        for i in range(self.header().count()):
            font = self.headerItem().font(i)
            if i == idx:
                font.setItalic(True)
            else:
                font.setItalic(False)
            self.headerItem().setFont(i, font)
                
        self.sortItems(idx, order)
        self.viewerSorted.emit()
        
    def makeTree(self):
        """ Populate tree with data from CycleData object. """
        
        self.items = {}
        dfs = self.data.splitMonths(returnType="CycleData")
        
        for monthYear, data in reversed(dfs):
            # root item of tree: summary of month, with total time, distance
            # and calories (in bold)
            rootText = [monthYear, 
                        data.summaryString('Time (hours)'), 
                        data.summaryString('Distance (km)'),
                        data.summaryString('Avg. speed (km/h)', func=max),
                        data.summaryString('Calories'),
                        data.summaryString('Gear', func=lambda v: np.around(np.mean(v)))]
            
            rootItem = CycleTreeWidgetItem(self)
            for idx, text in enumerate(rootText):
                rootItem.setText(idx, text)
                rootItem.setTextAlignment(idx, Qt.AlignCenter)
                font = rootItem.font(idx)
                font.setBold(True)
                rootItem.setFont(idx, font)
                
            # make rows of data for tree
            for rowIdx in reversed(range(len(data))):
                item = QTreeWidgetItem(rootItem)
                for idx, col in enumerate(self.headerLabels):
                    col = re.sub(r"\s", " ", col) # remove \n from avg speed
                    value = data[col][rowIdx]
                    value = self.data.fmtFuncs[col](value)
                    item.setText(idx, value)
                    item.setTextAlignment(idx, Qt.AlignCenter)
                dct = {'datetime':data['Date'][rowIdx], 'topLevelItem':rootItem,#'item':item, 
                       'index':data.df.index[rowIdx]}
                self.items[item] = dct
                    
        self.header().resizeSections(QHeaderView.ResizeToContents)
        
    
    @Slot()
    def combineRows(self):
        """ Combine selected rows, if the date and gear values are the same. """
        selected = self.selectedItems()
        if len(selected) <= 1:
            return None
        
        idx = self.headerLabels.index('Date')
        dates = [item.text(idx) for item in selected]
        idx = self.headerLabels.index('Gear')
        gears = [item.text(idx) for item in selected]
        
        if len(set(dates)) > 1:
            QMessageBox.warning(self, "Cannot combine selected data",
                                "Cannot combine selected data - dates do not match.")
        elif len(set(gears)) > 1:
            QMessageBox.warning(self, "Cannot combine selected data",
                                "Cannot combine selected data - gears do not match.")
        else:
            self.data.combineRows(dates[0])
            
            
    @Slot(object)
    def highlightItem(self,  date):
        for item in self.items:
            if item['datetime'] == date:
                self.setCurrentItem(item['item'])
                
    @Slot(QTreeWidgetItem, QTreeWidgetItem)
    def _itemChanged(self, currentItem, previousItem):
        for item in self.items:
            if item['item'] == currentItem:
                self.itemSelected.emit(item['datetime'])
