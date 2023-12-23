"""
QTreeWidget showing data from Data.
"""

from qtpy.QtWidgets import (QTreeWidget, QTreeWidgetItem, QHeaderView, 
                             QAbstractItemView, QMessageBox, QMenu, QAction)
from qtpy.QtCore import QSize, Qt
from qtpy.QtCore import Signal, Slot
from qtpy.QtGui import QKeySequence
import calendar
from dataclasses import dataclass
from .edititemdialog import EditItemDialog
from tracks.util import(checkHourMinSecFloat, checkMonthYearFloat, isFloat, 
                        hourMinSecToFloat, monthYearToFloat)
from . import Data

class CycleTreeWidgetItem(QTreeWidgetItem):
    """ QTreeWidgetItem subclass, with __lt__ method overridden, so that 
        the QTreeWidget can sort the items, where each column may contain
        a number, month and year, or time in HH:MM.ss.
    
        This requires a `sortColumn` property to be added. This must be set
        to the desired sort column index on every instance of this object
        before calling `QTreeWidget.sortItems()`. As far as I can tell, the
        `idx` arg to `QTreeWidget.sortItems()` is ignored.
    """
    
    def __init__(self, *args, row=[], **kwargs):
        super().__init__(*args, **kwargs)
        self.sortColumn = 0
        self.setRow(row)
    
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
        
    def setRow(self, row):
        self.row = row
        for idx, text in enumerate(row):
            self.setText(idx, text)
            self.setTextAlignment(idx, Qt.AlignCenter)
            font = self.font(idx)
            font.setBold(True)
            self.setFont(idx, font)
            
    @property
    def monthYear(self):
        return self.row[0]
            
class IndexTreeWidgetItem(QTreeWidgetItem):
    """ QTreeWidgetItem that stores the index of the DataFrame row it represents. """
    
    def __init__(self, *args, index=None, headerLabels=[], row={}, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = index
        self.headerLabels = headerLabels
        self.setRow(row)
        
    def setRow(self, row):
        self.row = row
        for idx, col in enumerate(self.headerLabels):
            value = self.row[col]
            self.setText(idx, value)
            self.setTextAlignment(idx, Qt.AlignCenter)
        
@dataclass
class TreeItem:
    dateTime: object = None
    topLevelItem: CycleTreeWidgetItem = None
    treeWidgetItem: IndexTreeWidgetItem = None

class DataViewer(QTreeWidget):
    """ 
    QTreeWidget showing cycling data, split by month.
    
    Each item in the tree shows a summary: month, total time, total distance,
    max. speed and total calories.
    
    The tree can be sorted by double clicking on the header.

    Parameters
    ----------
    parent : QWidget
        Main window/widget with :class:`Data` object
    activity : Activity
        Activity to view
    widthSpace : int
        Spacing to add to width in `sizeHint`. Default is 5.
    """
    
    itemSelected = Signal(object)
    """ **signal** itemSelected(CycleTreeWidgetItem `item`)
    
        Emitted when an item in the tree is selected, either by clicking
        on it or by navigating with the up or down keys.
    """
    
    viewerSorted = Signal()
    """ **signal** viewerSorted()
    
        Emitted after the DataViewer items have been sorted.
    """
    
    selectedSummary = Signal(str)
    """ **signal** selectedSummary(str `summaryString`)
    
        Emitted with a string summarising selected items.
    """
    
    viewerUpdated = Signal()
    """ **signal** viewerUpdated() 
    
        Emitted when `newData` has finished.
    """
    
    def __init__(self, parent, activity, widthSpace=10):
        super().__init__()
        
        self.parent = parent
        self._activity = activity
        
        self.widthSpace = widthSpace
        self.dateFmt = "%d %b %Y"
        
        self.setHeaderLabels(self._activity.header)
        self.header().setStretchLastSection(False)
        # # make header tall enough for two rows of text (avg speed has line break)
        # font = self.header().font()
        # metrics = QFontMetrics(font)
        # height = metrics.height()
        # self.header().setMinimumHeight(height*2)
        # align header text centrally
        for idx in range(len(self._activity.header)):
            self.headerItem().setTextAlignment(idx, Qt.AlignCenter)
            
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        self.makeTree()
        
        self.sortColumn = None
        self.sortDescending = [True for _ in range(len(self._activity.header))]
        self.header().setSectionsClickable(True)
        self.header().sectionClicked.connect(self.sortTree)
        
        self.currentItemChanged.connect(self._itemChanged)
        
        self.itemSelectionChanged.connect(self._summariseSelected)
        
        self.sortTree(0)
        
        msg = "Browse all sessions, grouped by month. Click on the headers \n"
        msg += "to sort by that metric in ascending or descending order.\n"
        msg += "Click on a session to highlight it in the plot."
        self.setToolTip(msg)
        
        self.editAction = QAction("Edit")
        self.editAction.setShortcut(QKeySequence("Ctrl+E"))
        self.editAction.triggered.connect(self._editItems)
        self.addAction(self.editAction)
        
        self.mergeAction = QAction("Merge")
        self.mergeAction.setShortcut(QKeySequence("Ctrl+M"))
        self.mergeAction.triggered.connect(self.combineRows)
        self.addAction(self.mergeAction)
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._showContextMenu)
        
    def _showContextMenu(self, pos):
        menu = QMenu()
        menu.addAction(self.editAction)
        menu.addAction(self.mergeAction)
        menu.exec_(self.mapToGlobal(pos))
        
    def _editItems(self):
        items = [item for item in self.selectedItems() if item not in self.topLevelItems]
        if items:
            self.dialog = EditItemDialog(self._activity, items, self._activity.header)
            result = self.dialog.exec_()
            if result == EditItemDialog.Accepted:
                values, remove = self.dialog.getValues()
                self.data.update(values)
                if remove:
                    self.data.removeRows(index=remove)
                
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
    
    @property 
    def topLevelItemsDict(self):
        return {item.monthYear: item for item in self.topLevelItems}
    
    @Slot(object)
    def newData(self, indices=None):
        """ 
        Add or update items. 
        
        If `indices` is None, the whole tree will be cleared and remade.
        If a list or Pandas Index is passed, the corresponding items will be
        changed and top level items updated as necessary.
        """
        if indices is None:
            # clear and remake tree
            self._makeTree()
            return 
        
        indices = list(indices) # cast to list so updated items can be removed

        # update changed items
        changed = []
        for item in self.items:
            if (idx := item.treeWidgetItem.index) in indices:
                # if index is already in tree, update that row and remove from indices list
                item.treeWidgetItem.setRow(self.data.row(idx, formatted=True))
                indices.remove(idx)
                # store month and year of changed items, so top level items can be 
                # updated where necessary
                date = self.data.df.iloc[idx]['Date']
                if (monthYear := (date.month, date.year)) not in changed:
                    changed.append(monthYear)
                    
        # update top level items of changed months
        for month, year in changed:
            data = self.data.getMonth(month, year, returnType="Data")
            summaries = data.make_summary()
            monthYear = f"{calendar.month_name[date.month]} {date.year}"
            rootText = [monthYear] + summaries
            rootItem = self.topLevelItemsDict[monthYear]
            rootItem.setRow(rootText)
        
        # for remaining indices add new rows to tree
        for idx in indices:
            date = self.data.df.iloc[idx]['Date']
            monthYear = f"{calendar.month_name[date.month]} {date.year}"
            data = self.data.getMonth(date.month, date.year, returnType="Data")
            summaries = data.make_summary()
            rootText = [monthYear] + summaries
            if monthYear not in self.topLevelItemsDict:
                rootItem = CycleTreeWidgetItem(self, row=rootText)
            else:
                rootItem = self.topLevelItemsDict[monthYear]
                rootItem.setRow(rootText)
                
            item = IndexTreeWidgetItem(rootItem, index=idx, 
                                       headerLabels=self._activity.header,
                                       row=self.data.row(idx, formatted=True))
            itemData = TreeItem(self.data['Date'][idx], rootItem, item)
            self.items.append(itemData)
            
        self.sortTree(self.sortColumn, switchOrder=False)
            
        self.viewerUpdated.emit()
        
    def _makeTree(self):
        """ Clear and remake tree, preserving which items are expanded. """
        expanded = []
        for item in self.topLevelItems:
            if item.isExpanded():
                expanded.append(item.text(0))
                
        self.clear()
        self.makeTree()
        for item in self.topLevelItems:
            if item.text(0) in expanded:
                self.expandItem(item)
                
        self.viewerUpdated.emit()
                
    def updateTopLevelItems(self):
        dfs = self.data.splitMonths(returnType="Data")
        for monthYear, data in reversed(dfs):
            # root item of tree: summary of month, with total time, distance
            # and calories (in bold)
            summaries = data.make_summary()
            rootText = [monthYear] + summaries
            rootItem = self.topLevelItemsDict[monthYear]
            rootItem.setRow(rootText)
        self.viewerUpdated.emit()
        
    @Slot(int)
    def sortTree(self, idx, switchOrder=True):
        """ 
        Sort the tree based on column `idx`. 
        
        If `idx` is the current `sortColumn` and `switchOrder` is True, the sort 
        order will be reversed. To re-apply the current sort, pass switchOrder=False.
        """
        
        # switch sort order if clicked column is already selected
        if idx == self.sortColumn and switchOrder:
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
        """ Populate tree with data from Data object. """
        
        self.items = []
        dfs = self.data.splitMonths(returnType="Data")
        
        for monthYear, data in reversed(dfs):
            # root item of tree: summary of month, with total time, distance
            # and calories (in bold)
            summaries = data.make_summary()
            rootText = [monthYear] + summaries
            rootItem = CycleTreeWidgetItem(self, row=rootText)
                
            # make rows of data for tree
            for rowIdx in reversed(range(len(data))):
                item = IndexTreeWidgetItem(rootItem, index=data.df.index[rowIdx], 
                                           headerLabels=self._activity.header,
                                           row=data.row(rowIdx, formatted=True))
                itemData = TreeItem(data['Date'][rowIdx], rootItem, item)
                self.items.append(itemData)
                    
        self.header().resizeSections(QHeaderView.ResizeToContents)
    
    @Slot()
    def combineRows(self):
        """ Combine selected rows, if the date and gear values are the same. """
        selected = self.selectedItems()
        if len(selected) <= 1:
            return None
        
        idx = self._activity.header.index('Date')
        dates = [item.text(idx) for item in selected]
        idx = self._activity.header.index('Gear')
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
            if item.dateTime == date:
                self.setCurrentItem(item.treeWidgetItem)
                
    @Slot(QTreeWidgetItem, QTreeWidgetItem)
    def _itemChanged(self, currentItem, previousItem):
        for item in self.items:
            if item.treeWidgetItem == currentItem:
                self.itemSelected.emit(item.dateTime)
                break
            
    @Slot()
    def _summariseSelected(self):
        """ 
        Emit :attr:`selectedSummary` with string for status bar. 
        
        If a top level item is selected, summarise it. Otherwise, summarise
        multiple selected items.
        """
        s = ""
        if len(self.selectedItems()) == 1 and (item:=self.selectedItems()[0]) in self.topLevelItems:
            s = self._summariseMonth(item)
        elif len((idx:=[item.index for item in self.selectedItems() if item not in self.topLevelItems])) > 1:
            df = self.data.df.loc[idx]
            data = Data(df, activity=self._activity)
            s = self._summariseData(data)
        self.selectedSummary.emit(s)
        
    def _summariseMonth(self, item):
        """ Summarise month given by `item` """
        if item not in self.topLevelItems:
            return
        months = self.data.splitMonths(returnType='Data')
        month, *_ = [data for monthyear, data in months if monthyear==item.text(0)]
        return self._summariseData(month)
            
    def _summariseData(self, data):
        """ Return string of summarised `data`, where `data` is a :class:`Data` object """
        summary = data.make_summary()
        s = f"{len(data)} sessions: "
        s += "; ".join(summary)
        return s
