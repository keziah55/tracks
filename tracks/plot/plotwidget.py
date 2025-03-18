"""
Widget containing plot and labels.
"""

from datetime import datetime, timedelta
from pyqtgraph import (
    PlotWidget as _PlotWidget,
    PlotCurveItem,
    mkPen,
    mkBrush,
    InfiniteLine,
    setConfigOptions,
)
import time
import numpy as np
from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from customQObjects.core import Settings

from .plotlabel import PlotLabel
from .plottoolbar import PlotToolBar
from .plotstyle import PlotStyle
from .custompyqtgraph import (
    CustomPlotItem,
    CustomAxisItem,
    CustomDateAxisItem,
    CustomViewBox,
)
from tracks.util import floatToHourMinSec, date_to_timestamp


class PlotWidget(QWidget):
    """Widget to display cycling data and labels showing data at the point
    under the mouse.

    Parameters
    ----------
    data : Data
        Data object.
    style : str, optional
        Plot style to apply. Default is "dark"
    months : int, optional
        Number of months to initally zoom x-axis to.
        If `None`, show all (default behaviour)
    y_series : str
        y series to show initially. Default is "time"
    """

    current_point_changed = Signal(dict)
    """ **signal**  current_point_changed(dict `values`)

        Emitted when a point in the plot is hovered over. The dict provides
        the date, speed, distance, calories and time data for the chosen point.
    """

    point_selected = Signal(object)
    """ **signal** point_selected(datetime `currentPoint`)

        Emitted when the plot is double clicked, with the date from the
        current point.
    """

    def __init__(self, data, activity, style="dark", months=None, y_series=None):
        super().__init__()

        self._plot_state = None
        self._plot_label = None
        self.data = data
        self._activity = activity

        self._view_months = months  # number of months to show, by default

        self._plot_tool_bar = PlotToolBar()
        self._make_plot(data, activity, style=style, months=months, y_series=y_series)

        self._plot_layout = QHBoxLayout()
        self._plot_layout.addWidget(self._plot_widget)
        self._plot_layout.addWidget(self._plot_tool_bar)
        self._layout = QVBoxLayout()
        self._layout.addLayout(self._plot_layout)
        self._layout.addWidget(self._plot_label)

        self.setLayout(self._layout)

    def _make_plot(self, *args, **kwargs):
        self._plot_widget = Plot(*args, **kwargs)
        if self._plot_label is None:
            self._plot_label = PlotLabel(self._activity, self._plot_widget.style)
        else:
            self._plot_label.set_style(self._plot_widget.style)
        self._plot_label.labelClicked.connect(self._plot_widget._switch_series)
        self._plot_widget.current_point_changed.connect(self._plot_label.set_labels)
        self._plot_widget.point_selected.connect(self.point_selected)

        self._plot_tool_bar.view_all_clicked.connect(self._plot_widget.view_all)
        self._plot_tool_bar.view_range_clicked.connect(self._plot_widget.reset_month_range)
        self._plot_tool_bar.highlight_PB_clicked.connect(self._plot_widget._highlight_PBs)

    def state(self):
        state = {
            "current_series": self._plot_widget.y_series,
            "style": self._plot_widget.style.name,
            "default_months": self._view_months,
        }
        return state

    @Slot(object)
    def new_data(self, idx=None):
        self._plot_widget.update_plots()

    @Slot(object)
    def set_current_point_from_date(self, date):
        self._plot_widget.set_current_point_from_date(date)

    @Slot(object, bool)
    def set_x_axis_range(self, months, from_recent_session=True):
        self._view_months = months
        self._plot_widget.set_x_axis_range(months, from_recent_session=from_recent_session)

    @Slot(str)
    def set_style(self, style, force=False):
        if force or self._plot_widget.style.name != style:
            self._plot_state = self._plot_widget.get_state()
            self._plot_layout.removeWidget(self._plot_widget)
            self._plot_widget.deleteLater()
            self._make_plot(self.data, self._activity, style=style)
            self._plot_widget.set_state(self._plot_state)
            self._plot_layout.insertWidget(0, self._plot_widget)

    def add_custom_style(self, name, style, set_style=True):
        self._plot_widget.style.add_style(name, style)
        if set_style:
            self.set_style(name, force=True)

    def remove_custom_style(self, name):
        # TODO remove style from file
        # and update current?
        self._plot_widget.style.remove_style(name)

    def get_style(self, name):
        return self._plot_widget.style.get_style_dict(name)

    def get_style_keys(self):
        return self._plot_widget.style.keys

    def get_style_symbol_keys(self):
        return self._plot_widget.style.symbol_keys

    def get_valid_styles(self):
        return self._plot_widget.style.valid_styles

    def get_default_styles(self):
        return self._plot_widget.style.default_styles


class Plot(_PlotWidget):
    """Sublcass of PyQtGraph.PlotWidget to display cycling data.

    Parameters
    ----------
    data : Data
        Data object.
    style : str
        Style name to use
    months : int, optional
        Number of months to initally zoom x-axis to.
        If `None`, show all (default behaviour)
    """

    current_point_changed = Signal(dict)
    """ **signal**  current_point_changed(dict `values`)

        Emitted when a point in the plot is hovered over. The dict provides
        the date, speed, distance, calories and time data for the chosen point.
    """

    point_selected = Signal(object)
    """ **signal** point_selected(datetime `currentPoint`)

        Emitted when the plot is double clicked, with the date from the
        current point.
    """

    def __init__(self, data, activity, style="dark", months=None, y_series=None):
        self._y_series = None
        self._plot_item = None
        self.style = PlotStyle(activity, style)
        self.set_style(style)

        self._date_axis = CustomDateAxisItem()
        self._plot_item = CustomPlotItem(
            viewBox=CustomViewBox(),
            axisItems={"bottom": self._date_axis, "left": CustomAxisItem("left")},
        )
        super().__init__(plotItem=self._plot_item)

        self._date_axis.axisDoubleClicked.connect(self.set_plot_range)

        self._highlight_point_item = None

        self.data = data

        self._activity = activity

        plottable = list(self._activity.filter_measures("plottable", lambda b: b))

        self._init_right_axis()

        # axis labels
        self._plot_item.setLabel("bottom", text="Date")

        # show grid on left and bottom axes
        self._plot_item.getAxis("left").setGrid(255)
        self._plot_item.getAxis("bottom").setGrid(255)

        # cross hairs
        self._update_time_limit = 0.05
        self._last_update_time = None
        self._v_line = InfiniteLine(angle=90, movable=False)
        self._h_line = InfiniteLine(angle=0, movable=False)
        self._plot_item.addItem(self._v_line, ignoreBounds=True)
        self._plot_item.addItem(self._h_line, ignoreBounds=True)

        self._plot_item.scene().sigMouseMoved.connect(self._mouse_moved)
        self._plot_item.scene().sigMouseClicked.connect(self._plot_clicked)

        # update second view box
        self.update_views()
        self._plot_item.vb.sigResized.connect(self.update_views)

        self._current_point = {}

        self._prev_highlight_point_colour = None

        # all points that are/were PBs can be highlighted
        self._show_pbs = False
        self._regenerate_cached_pbs = {key: False for key in plottable}
        self._hglt_pbs = {key: [] for key in plottable}

        self._view_months = None

        if y_series not in plottable:
            y_series = "time"
        self.set_y_series(y_series)
        self._plot_total_distance()

        if months is not None:
            self.set_x_axis_range(months)

    def _init_right_axis(self):
        self.vb2 = CustomViewBox()
        self._plot_item.showAxis("right")
        self._plot_item.scene().addItem(self.vb2)
        self._plot_item.getAxis("right").linkToView(self.vb2)
        self.vb2.setXLink(self._plot_item)

    @property
    def view_boxes(self):
        """Return list of all viexBoxes in the plot."""
        vbx = [self._plot_item.vb]
        if hasattr(self, "vb2"):
            vbx.append(self.vb2)
        return vbx

    @Slot()
    def update_views(self):
        ## Copied from PyQtGraph MultiplePlotAxes.py example ##
        # view has resized; update auxiliary views to match
        self.vb2.setGeometry(self._plot_item.vb.sceneBoundingRect())
        # need to re-update linked axes since this was called
        # incorrectly while views had different shapes.
        # (probably this should be handled in ViewBox.resizeEvent)
        self.vb2.linkedViewChanged(self._plot_item.vb, self.vb2.XAxis)

    def get_state(self):
        state = {}
        state["y_series"] = self.y_series
        for n, vb in enumerate(self.view_boxes):
            key = f"vb{n}State"
            state[key] = vb.getState()
        if self._current_point:
            state["currentPoint"] = self._current_point["index"]
        return state

    def set_state(self, state):
        self.y_series = state["y_series"]
        for n, vb in enumerate(self.view_boxes):
            key = f"vb{n}State"
            vb.setState(state[key])
        if len(self.view_boxes) > 1:
            self.view_boxes[1].setXLink(self._plot_item)
        if "currentPoint" in state:
            self.set_current_point(state["currentPoint"])

    def set_style(self, style):
        self.style.name = style
        dct = {
            "foreground": self.style.foreground["colour"],
            "background": self.style.background["colour"],
        }
        setConfigOptions(**dct)
        if self._plot_item is not None:
            self._plot_item.setButtonPixmaps()
        if self.y_series is not None:
            self.updatePlots()

    @Slot()
    def view_all(self):
        # enableAutoRange on both view_boxes
        for vb in self.view_boxes:
            vb.enableAutoRange()
        self._update_highlight_PBs()

    @Slot()
    def reset_month_range(self):
        if self._view_months is not None:
            self.set_x_axis_range(self._view_months)
        self._update_highlight_PBs()

    @Slot(float, float)
    def set_plot_range(self, x0, x1):
        """Set range of both view boxes to cover the points between the two
        given timestamps.
        """
        # apply to both the current scatter and background plot
        if not hasattr(self, "dataItem") or not hasattr(self, "backgroundItem"):
            return None

        if (x0, x1) == self.view_boxes[0].xRange:
            return None

        data = [
            (
                self.dataItem.scatter.data["x"],
                self.dataItem.scatter.data["y"],
                self.view_boxes[0],
            ),
            (self.backgroundItem.xData, self.backgroundItem.yData, self.view_boxes[1]),
        ]

        for xPoints, yData, viewBox in data:
            # find x-coords of points in the given month
            mask = np.isin(np.where(xPoints >= x0)[0], np.where(xPoints <= x1)[0])
            if np.any(mask):
                # select the corresponding y data
                idx = np.where(xPoints >= x0)[0][mask]
                yPoints = yData[idx]
                # get min and max
                y0 = np.min(yPoints)
                y1 = np.max(yPoints)
                # set min and max for x and y in the viewBox
                viewBox.setRange(xRange=(x0, x1), yRange=(y0, y1))
            else:
                viewBox.setRange(xRange=(x0, x1))

    @Slot(object, bool)
    def set_x_axis_range(self, months, from_recent_session=True):
        """Scale the plot to show the most recent `months` months.

        If `from_recent_session` is True (default), the month range is calculated
        relative to the most recent session in the `Data` object.
        Otherwise, it is calculated from the current date.
        These two options are equivalent if there are sessions from the current
        month in the `Data` object.
        """
        if self.data.df.is_empty():
            return
        self._view_months = months
        if from_recent_session:
            ts1 = self.data.date_timestamps[-1]
        else:
            now = datetime.now()
            ts1 = now.timestamp()
            if months is not None and now.month != self.data.datetimes[-1].month:
                months -= now.month - self.data.datetimes[-1].month
        if months is None:
            ts0 = self.data.date_timestamps[0]
        else:
            days = self._view_months * 365 / 12  # number of days to go back
            td = timedelta(days=days)
            ts0 = (datetime.fromtimestamp(ts1) - td).timestamp()
        self.set_plot_range(ts0, ts1)

    @Slot()
    def update_plots(self):
        self.plot_series(self.y_series, mode="set")
        self._plot_total_distance(mode="set")
        self.reset_month_range()
        self._regenerate_cached_pbs = {key: True for key in self._regenerate_cached_pbs}

    @property
    def y_series(self):
        return self._y_series

    @y_series.setter
    def y_series(self, key):
        self._y_series = key
        self.plot_series(self.y_series)

    def set_y_series(self, key):
        self.y_series = key

    def plot_series(self, key, mode="new"):
        """
        Plot given series on y1 axis.

        Mode must be 'new' (to add a new series) or 'set' to upadte the data in
        an existing series.
        """
        series = self.data[key]
        self._plot_item.getAxis("left").tickFormatter = floatToHourMinSec if key == "time" else None

        # make style
        styleDict = self.style[key]
        style = self._make_scatter_style(**styleDict)
        # make or update plot
        match mode:
            case "new":
                self.dataItem = self._plot_item.scatterPlot(
                    self.data.date_timestamps, series, **style
                )
                self._plot_item.vb.sigRangeChanged.connect(self._update_highlight_PBs)
            case "set":
                self.dataItem.setData(self.data.date_timestamps, series, **style)
            case _:
                msg = f"plot_series `mode` must be 'new' or 'set', not '{mode}'"
                raise ValueError(msg)
        # set axis label
        self._plot_item.setLabel(
            "left", text=self._activity[key].full_name, color=styleDict["colour"]
        )
        # retain plot range when switching series
        if self.view_boxes[0].xRange is not None:
            self.set_plot_range(*self.view_boxes[0].xRange)
        # if PBs were highlighted, highlight again
        self._update_highlight_PBs()

    def _plot_total_distance(self, mode="new"):
        """Plot monthly total distance."""
        colour = self.style["odometer"]["colour"]
        style = self._make_fill_style(colour)
        style["stepMode"] = "right"
        dts, odo = self.data.get_monthly_odometer()
        dts = [date_to_timestamp(dt) for dt in dts]
        if mode == "new":
            self.backgroundItem = PlotCurveItem(dts, odo, **style)
            self.vb2.addItem(self.backgroundItem)
        elif mode == "set":
            self.backgroundItem.setData(dts, odo, **style)
        self._plot_item.getAxis("right").setLabel("Total monthly distance", color=colour)

    @Slot(str)
    def _switch_series(self, key):
        if key in self._activity.measures and self._activity[key].plottable:
            self._plot_item.removeItem(self.dataItem)
            self.y_series = key

    @Slot(object)
    def _plot_clicked(self, event):
        """If the plot is clicked, emit `point_selected` signal with `currentPoint` datetime."""
        # get x and y bounds
        y_min = 0  # no top axis
        y_max = self._plot_item.getAxis("bottom").scenePos().y()
        # left axis position is 1,1 (don't know why), so use the bottom axis x here
        x_min = self._plot_item.getAxis("bottom").scenePos().x()
        x_max = self._plot_item.getAxis("right").scenePos().x()

        pos = event.scenePos()
        if x_min <= pos.x() <= x_max and y_min <= pos.y() <= y_max:  # event.double() and
            idx = self._current_point["index"]
            date = self.data.date[idx]
            self.point_selected.emit(date)

    def set_current_point(self, idx):
        """Set the `current_point` dict from index `idx` in the `data` DataFrame
        and emit `current_point_changed` signal.
        """
        self._current_point["index"] = int(idx)
        for name in self._activity.measures.keys():
            self._current_point[name] = self.data[idx, name]  # getattr(self.data, name)[idx]
        self.current_point_changed.emit(self._current_point)

    @Slot(object)
    def set_current_point_from_date(self, date):
        """Find point at the given date and highlight it."""
        dt = datetime(date.year, date.month, date.day)
        idx = self.data.datetimes.index(dt)
        pt = self.dataItem.scatter.points()[idx]
        self._ensure_point_visible(pt)
        # ensure visible may have resrawn, so `pt` may no longer be valid, so highlight by index
        self._highlight_point_from_index(idx)
        self.set_current_point(idx)

    def set_current_point_from_timestamp(self, ts):
        # given timestamp in seconds, find nearest date and speed
        idx = (np.abs(self.data.date_timestamps - ts)).argmin()
        self.set_current_point(idx)

    def _ensure_point_visible(self, pt):
        ts = pt.pos().x()
        x0, x1 = self.view_boxes[0].xRange
        if ts < x0:
            x0 = ts - 1e6
        elif ts > x1:
            x1 = ts + 1e6
        self.set_plot_range(x0, x1)

    def _highlight_point_from_index(self, idx):
        """Get scatter point at index `idx` and highlight it."""
        pt = self.dataItem.scatter.points()[idx]
        return self._highlight_point(pt)

    @Slot(object)
    def _highlight_point(self, point=None):
        """Change pen and brush of given point (and reset any previously
        highlighted points).
        """
        if point is None:
            if self._highlight_point_item is not None:
                point = self._highlight_point_item
            else:
                return None

        # reset previous hgltPoint pen and brush
        if self._prev_highlight_point_colour is not None:
            pen = mkPen(self._prev_highlight_point_colour)
            brush = mkBrush(self._prev_highlight_point_colour)
            try:
                self._highlight_point_item.setPen(pen)
                self._highlight_point_item.setBrush(brush)
            except:
                pass
        # store current colour of new hgltPoint
        self._prev_highlight_point_colour = point.pen().color().name()

        # set colour of new point
        colour = self.style["highlight_point"]["colour"]
        pen = mkPen(colour)
        brush = mkBrush(colour)
        self._highlight_point_item = point
        self._highlight_point_item.setPen(pen)
        self._highlight_point_item.setBrush(brush)

    @Slot(bool)
    def _highlight_PBs(self, show):
        """Highlight points that are, or were, PBs."""
        if show:
            self._show_pbs = True
            if (
                self._regenerate_cached_pbs[self.y_series]
                or len(self._hglt_pbs[self.y_series]) == 0
            ):
                self._hglt_pbs[self.y_series] = self._get_PBs()
                self._regenerate_cached_pbs[self.y_series] = False
            for idx in self._hglt_pbs[self.y_series]:
                pt = self.dataItem.scatter.points()[idx]
                colour = self.style["highlight_point"]["colour"]
                pen = mkPen(colour)
                brush = mkBrush(colour)
                pt.setPen(pen)
                pt.setBrush(brush)
        else:
            self._show_pbs = False
            for idx in self._hglt_pbs[self.y_series]:
                pt = self.dataItem.scatter.points()[idx]
                pt.resetPen()
                pt.resetBrush()

    def _update_highlight_PBs(self):
        if self._show_pbs:
            self._highlight_PBs(self._show_pbs)

    def _get_PBs(self):
        """Return array of points that represent(ed) a PB in the current series."""
        settings = Settings()
        num = settings.value("pb/numSessions", cast=int)
        return self.data.get_pbs(self.y_series, num)

    @Slot(object)
    def _mouse_moved(self, pos):
        if (
            self._last_update_time is not None
            and time.monotonic() - self._last_update_time < self._update_time_limit
        ):
            return

        self._last_update_time = time.monotonic()

        if not self.data.df.is_empty() and self._plot_item.sceneBoundingRect().contains(pos):
            mousePoint = self._plot_item.vb.mapSceneToView(pos)

            idx = int(mousePoint.x())
            if min(self.data.date_timestamps) < idx < max(self.data.date_timestamps):
                self.set_current_point_from_timestamp(idx)
                pts = self._scatter_points_at_x(mousePoint, self.dataItem.scatter)
                if len(pts) != 0:
                    # could be multiple points at same x, so get closest point to mouse by y value
                    yVals = np.array([pt.pos().y() for pt in pts])
                    idx = (np.abs(yVals - mousePoint.y())).argmin()
                    self._highlight_point(pts[idx])
            self._v_line.setPos(mousePoint.x())
            self._h_line.setPos(mousePoint.y())

    @staticmethod
    def _scatter_points_at_x(pos, scatter):
        """Return a list of points on `scatter` under the x-coordinate of the
        given position `pos`, ignoring the y-coord.
        """
        # Tried to subclass ScatterPlotItem and add this method there, but it
        # messed up the DateAxis
        x = pos.x()
        pw = scatter.pixelWidth()
        pts = []
        for s in scatter.points():
            sp = s.pos()
            ss = s.size()
            sx = sp.x()
            s2x = ss * 0.5
            if scatter.opts["pxMode"]:
                s2x *= pw
            if x > sx - s2x and x < sx + s2x:
                pts.append(s)
        return pts[::-1]

    @staticmethod
    def _make_scatter_style(colour, symbol):
        """Make style for series with no line but with symbols."""
        pen = mkPen(colour)
        brush = mkBrush(colour)
        d = {"symbol": symbol, "symbolPen": pen, "symbolBrush": brush}
        return d

    @staticmethod
    def _make_fill_style(colour):
        """Make style for PlotCurveItem with fill underneath."""
        pen = mkPen(colour)
        brush = mkBrush(colour)
        d = {"pen": pen, "brush": brush, "fillLevel": 0}
        return d
