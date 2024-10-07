"""
QTreeWidget showing data from Data.
"""

from qtpy.QtWidgets import (
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
    QMenu,
    QAction,
)
from qtpy.QtCore import QSize, Qt
from qtpy.QtCore import Signal, Slot
from qtpy.QtGui import QKeySequence, QFont
import calendar
from dataclasses import dataclass
from .edititemdialog import EditItemDialog
from tracks.util import (
    checkHourMinSecFloat,
    checkMonthYearFloat,
    isFloat,
    hourMinSecToFloat,
    monthYearToFloat,
)
from . import Data


class CycleTreeWidgetItem(QTreeWidgetItem):
    """QTreeWidgetItem subclass, with __lt__ method overridden, so that
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

        cast = self._get_item_cast(item0, item1)
        if cast is not None:
            return cast(item0) < cast(item1)
        else:
            return item0 < item1

    @staticmethod
    def _get_item_cast(item0, item1):
        if isFloat(item0) and isFloat(item1):
            return float
        elif checkMonthYearFloat(item0) and checkMonthYearFloat(item1):
            return monthYearToFloat
        elif checkHourMinSecFloat(item0) and checkHourMinSecFloat(item1):
            return hourMinSecToFloat
        else:
            return None

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
    def month_year(self):
        return self.row[0]


class IndexTreeWidgetItem(QTreeWidgetItem):
    """QTreeWidgetItem that stores the index of the DataFrame row it represents."""

    def __init__(self, *args, activity=None, index=None, headerLabels=[], row={}, **kwargs):
        super().__init__(*args, **kwargs)
        self._activity = activity
        self.index = index
        self.headerLabels = headerLabels
        self.setRow(row)

    def setRow(self, row):
        self.row = row
        for idx, col in enumerate(self._activity.measures):
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
    data : Data
        :class:`Data` object
    activity : Activity
        Activity to view
    widthSpace : int
        Spacing to add to width in `sizeHint`. Default is 5.
    """

    item_selected = Signal(object)
    """ **signal** item_selected(CycleTreeWidgetItem `item`)

        Emitted when an item in the tree is selected, either by clicking
        on it or by navigating with the up or down keys.
    """

    viewer_sorted = Signal()
    """ **signal** viewer_sorted()

        Emitted after the DataViewer items have been sorted.
    """

    selected_summary = Signal(str)
    """ **signal** selected_summary(str `summaryString`)

        Emitted with a string summarising selected items.
    """

    viewer_updated = Signal()
    """ **signal** viewer_updated()

        Emitted when `new_data` has finished.
    """

    def __init__(self, data, activity, widthSpace=10):
        super().__init__()

        self.data = data
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

        self.make_tree()

        self.sortColumn = None
        self.sortDescending = [True for _ in range(len(self._activity.header))]
        self.header().setSectionsClickable(True)
        self.header().sectionClicked.connect(self.sort_tree)

        self.currentItemChanged.connect(self._item_changed)

        self.itemSelectionChanged.connect(self._summarise_selected)

        self.sort_tree(0)

        msg = "Browse all sessions, grouped by month. Click on the headers \n"
        msg += "to sort by that metric in ascending or descending order.\n"
        msg += "Click on a session to highlight it in the plot."
        self.setToolTip(msg)

        self.editAction = QAction("Edit")
        self.editAction.setShortcut(QKeySequence("Ctrl+E"))
        self.editAction.triggered.connect(self._edit_items)
        self.addAction(self.editAction)

        self.mergeAction = QAction("Merge")
        self.mergeAction.setShortcut(QKeySequence("Ctrl+M"))
        self.mergeAction.triggered.connect(self.combine_rows)
        self.addAction(self.mergeAction)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        menu = QMenu()
        menu.addAction(self.editAction)
        menu.addAction(self.mergeAction)
        menu.exec_(self.mapToGlobal(pos))

    def _edit_items(self):
        items = [item for item in self.selectedItems() if item not in self.top_level_items]
        if items:
            self.dialog = EditItemDialog(self._activity, items, self._activity.header)
            result = self.dialog.exec_()
            if result == EditItemDialog.Accepted:
                values, remove = self.dialog.get_values()
                self.data.update(values)
                if remove:
                    self.data.remove_rows(index=remove)

    def sizeHint(self):
        width = self.header().length() + self.widthSpace
        height = super().sizeHint().height()
        return QSize(width, height)

    @property
    def top_level_items(self):
        """List of top level QTreeWidgetItems."""
        items = [self.topLevelItem(i) for i in range(self.topLevelItemCount())]
        return items

    @property
    def top_level_itemsDict(self):
        return {item.month_year: item for item in self.top_level_items}

    @Slot(object)
    def new_data(self, indices=None):
        """
        Add or update items.

        If `indices` is None, the whole tree will be cleared and remade.
        If a list or Pandas Index is passed, the corresponding items will be
        changed and top level items updated as necessary.
        """
        if indices is None:
            # clear and remake tree
            self._make_tree()
            return

        indices = list(indices)  # cast to list so updated items can be removed

        # update changed items
        changed = []
        for item in self.items:
            if (idx := item.treeWidgetItem.index) in indices:
                # if index is already in tree, update that row and remove from indices list
                item.treeWidgetItem.setRow(self.data.row(idx, formatted=True))
                indices.remove(idx)
                # store month and year of changed items, so top level items can be
                # updated where necessary
                date = self.data[idx, "date"]
                if (month_year := (date.month, date.year)) not in changed:
                    changed.append(month_year)

        # update top level items of changed months
        for month, year in changed:
            data = self.data.get_month(month, year, return_type="Data")
            summaries = list(data.make_summary().values())
            month_year = f"{calendar.month_name[date.month]} {date.year}"
            rootText = [month_year] + summaries
            rootItem = self.top_level_itemsDict[month_year]
            rootItem.setRow(rootText)

        # for remaining indices add new rows to tree
        for idx in indices:
            date = self.data[idx, "date"]
            month_year = f"{calendar.month_name[date.month]} {date.year}"
            data = self.data.get_month(date.month, date.year, return_type="Data")
            summaries = list(data.make_summary().values())
            rootText = [month_year] + summaries
            if month_year not in self.top_level_itemsDict:
                rootItem = CycleTreeWidgetItem(self, row=rootText)
            else:
                rootItem = self.top_level_itemsDict[month_year]
                rootItem.setRow(rootText)

            item = IndexTreeWidgetItem(
                rootItem,
                activity=self._activity,
                index=idx,
                headerLabels=self._activity.header,
                row=self.data.row(idx, formatted=True),
            )
            itemData = TreeItem(self.data["date"][idx], rootItem, item)
            self.items.append(itemData)

        self.sort_tree(self.sortColumn, switchOrder=False)

        self.viewer_updated.emit()

    def _make_tree(self):
        """Clear and remake tree, preserving which items are expanded."""
        expanded = []
        for item in self.top_level_items:
            if item.isExpanded():
                expanded.append(item.text(0))

        self.clear()
        self.make_tree()
        for item in self.top_level_items:
            if item.text(0) in expanded:
                self.expandItem(item)

        self.viewer_updated.emit()

    def update_top_level_items(self):
        dfs = self.data.split_months(return_type="Data")
        for month_year, data in reversed(dfs):
            # root item of tree: summary of month, with total time, distance
            # and calories (in bold)
            month_year = month_year.strftime("%B %Y")
            summaries = list(data.make_summary().values())
            rootText = [month_year] + summaries
            rootItem = self.top_level_itemsDict[month_year]
            rootItem.setRow(rootText)
        self.viewer_updated.emit()

    @Slot(int)
    def sort_tree(self, idx, switchOrder=True):
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
        for rootItem in self.top_level_items:
            rootItem.sortColumn = idx
        self.sortColumn = idx

        # make header label for sort column italic
        for i in range(self.header().count()):
            font = self.headerItem().font(i)
            if i == idx:
                font.setWeight(QFont.ExtraBold)
            else:
                font.setWeight(QFont.Normal)
            self.headerItem().setFont(i, font)

        self.sortItems(idx, order)
        self.viewer_sorted.emit()

    def make_tree(self):
        """Populate tree with data from Data object."""

        self.items = []
        dfs = self.data.split_months(return_type="Data")
        # pandas df had persistent index, polars doesn't
        # calculate equivalent index here
        # starting from len(data), because we go through the months backwards
        idx = len(self.data) - 1

        for month_year, data in reversed(dfs):
            # root item of tree: summary of month, with total time, distance
            # and calories (in bold)
            summaries = list(data.make_summary().values())
            rootText = [month_year.strftime("%B %Y")] + summaries
            rootItem = CycleTreeWidgetItem(self, row=rootText)

            # make rows of data for tree
            for rowIdx in reversed(range(len(data))):
                item = IndexTreeWidgetItem(
                    rootItem,
                    activity=self._activity,
                    index=idx,
                    headerLabels=self._activity.header,
                    row=data.row(rowIdx, formatted=True),
                )
                itemData = TreeItem(data["date"][rowIdx], rootItem, item)
                self.items.append(itemData)
                idx -= 1

        self.header().resizeSections(QHeaderView.ResizeToContents)

    @Slot()
    def combine_rows(self):
        """Combine selected rows, if the date and gear values are the same."""
        selected = self.selectedItems()
        if len(selected) <= 1:
            return None

        # TODO gear hardcoded here
        idx = self._activity.measure_slugs.index("date")
        dates = [item.text(idx) for item in selected]
        idx = self._activity.measure_slugs.index("gear")
        gears = [item.text(idx) for item in selected]

        if len(set(dates)) > 1:
            QMessageBox.warning(
                self,
                "Cannot combine selected data",
                "Cannot combine selected data - dates do not match.",
            )
        elif len(set(gears)) > 1:
            QMessageBox.warning(
                self,
                "Cannot combine selected data",
                "Cannot combine selected data - gears do not match.",
            )
        else:
            self.data.combine_rows(dates[0])

    @Slot(object)
    def highlight_item(self, date):
        for item in self.items:
            if item.dateTime == date:
                self.setCurrentItem(item.treeWidgetItem)

    @Slot(QTreeWidgetItem, QTreeWidgetItem)
    def _item_changed(self, currentItem, previousItem):
        for item in self.items:
            if item.treeWidgetItem == currentItem:
                self.item_selected.emit(item.dateTime)
                break

    @Slot()
    def _summarise_selected(self):
        """
        Emit :attr:`selected_summary` with string for status bar.

        If a top level item is selected, summarise it. Otherwise, summarise
        multiple selected items.
        """
        if len(self.selectedItems()) == 0:
            return
        s = ""
        if (
            len(self.selectedItems()) == 1
            and (item := self.selectedItems()[0]) in self.top_level_items
        ):
            s = self._summarise_month(item)
        elif all([item in self.top_level_items for item in self.selectedItems()]):
            s = self._summarise_months(self.selectedItems())
        elif (
            len(
                (
                    idx := [
                        item.index
                        for item in self.selectedItems()
                        if item not in self.top_level_items
                    ]
                )
            )
            > 1
        ):
            df = self.data.df[idx]
            data = Data(df, activity=self._activity)
            s = self._summarise_data(data)
        if s:
            self.selected_summary.emit(s)

    def _summarise_month(self, item):
        """Summarise month given by `item`"""
        if item not in self.top_level_items:
            raise ValueError("_summarise_month can only summarise top-level tree items")
        months = self.data.split_months(return_type="Data")
        month, *_ = [
            data for month_year, data in months if month_year.strftime("%B %Y") == item.text(0)
        ]
        return self._summarise_data(month)

    def _summarise_data(self, data):
        """Return string of summarised `data`, where `data` is a :class:`Data` object"""
        summary = [f"{value}" for key, value in data.make_summary(unit=True).items()]
        s = f"{len(data)} sessions; "
        s += "; ".join(summary)
        return s

    def _summarise_months(self, items):
        """Return summary string from list of top-level items"""
        if any([item not in self.top_level_items for item in items]):
            raise ValueError("_summarise_months can only summarise top-level tree items")
        selected_months = [item.text(0) for item in items]

        months = self.data.split_months(return_type="Data")

        months = map(
            lambda tup: tup.data,
            filter(lambda tup: tup.month_year in selected_months, months),
        )

        if months := list(months):

            concat_data = Data.concat(months, self._activity)

            s = f"{len(selected_months)} months; "
            s += self._summarise_data(concat_data)
            return s
        else:
            return ""
