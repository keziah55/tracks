#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 20:43:03 2024

@author: keziah
"""

# import polars as pl
# from tracks.activities import ActivityManager, Activity

# f = "/home/keziah/.tracks/cycling.csv"

# df = pl.read_csv(f, try_parse_dates=True)

# manager = ActivityManager()
# activity_json = manager._activities_json().get("cycling", None)
# activity = Activity(activity_json["name"])
# for measure in activity_json["measures"].values():
#     activity.add_measure(**measure)

# add new column
# i.e. Data._apply_relations
# also Data._update_relations - using an alias that's already in the df will update that column
# relations = activity.get_relations()
# relation = relations["speed"]
# m0 = df[relation.m0.slug]
# m1 = df[relation.m1.slug]
# new_col = relation.op.call(m0, m1)
# df2 = df.with_columns(new_col.alias("speed2")) # assign to new df

"""
Object providing convenient access to the contents of a DataFrame.
"""

# from qtpy.QtCore import QObject
# from qtpy.QtCore import Signal, Slot
from tracks.util import parseDate, parseDuration, hourMinSecToFloat, floatToHourMinSec
from collections import namedtuple
from datetime import date, datetime
import calendar
import numpy as np
import polars as pl
import functools


def check_empty(func):
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        if self.df.is_empty():
            return []
        else:
            return func(self, *args, **kwargs)

    return wrapped


MonthData = namedtuple("MonthData", ["month_year", "data"])


class Data:  # (QObject):
    # dataChanged = Signal(object)
    # """
    # **signal** dataChanged(object `index`)

    # Emitted when the data in the object is changed, with the pandas index
    # of the new rows.
    # """

    # newMax = Signal(str, object)
    # """
    # **signal** newMax(str `column`, object `value`)

    # Emitted when newly added data contains a new max value for a given column.
    # """

    def __init__(self, df, activity=None):
        """
        Object providing convenience functions for accessing data from a given DataFrame.
        """
        super().__init__()

        self.df = self._apply_relations(df, activity)

        self._activity = activity

    @staticmethod
    def concat(datas, activity):
        try:
            dfs = [data.df for data in datas]
        except:
            raise TypeError("All values supplied to `Data.concat` must be Data objects")
        else:
            if len(dfs) == 0:
                raise ValueError("Cannot concat empty sequence")
            tmp_df = pl.concat(dfs)
            new_data = Data(tmp_df, activity)
            return new_data

    def formatted(self, key):
        measure = self._activity[key]
        return [measure.formatted(v) for v in self.df[key]]

    def summaryString(self, key, func=sum, unit=False):
        measure = self._activity[key]
        try:
            s = measure.summarised(self[key], include_unit=unit)
        except Exception as err:
            msg = f"Could not summarise measure '{measure}'.\n"
            msg += f"Original error was: {err}"
            raise RuntimeError(msg)
        return s

    def make_summary(self) -> dict:
        summaries = {
            slug: self.summaryString(slug)
            for slug, measure in self._activity.measures.items()
            if measure.summary is not None
        }
        return summaries

    def __len__(self):
        return len(self.df)

    def __getitem__(self, key):
        if key in self.df.columns:
            # return self.df[key]
            # name = self._quickNames[key]
            return getattr(self, key)
        else:
            raise NameError(f"{key} not a valid property name.")

    def __getattr__(self, name):
        ret = self.df[name]
        # if name in ["date"]:
        #     ret = list(ret)
        # else:
        #     ret = ret.to_numpy()
        return ret

    def __repr__(self):
        return self.toString(headTail=5)

    def row(self, idx, formatted=False):
        """
        Return row `idx` as dict.

        If `formatted` is True, also format the values.
        """
        row = dict(zip(self.df.columns, self.df.row(idx)))
        # row = dict(self.df.iloc[idx])
        if formatted:
            row = {
                name: self._activity.get_measure(name).formatted(value)
                for name, value in row.items()
            }
        return row

    def toString(self, headTail=None):
        """
        Return Data object as a string.

        Parameters
        ----------
        headTail : int, optional
            If provided, abridge the object to show only the first and last
            `headTail` rows. By default, do not abridge and return the full object.
        """
        return repr(self.df)
        # keys = self.df.columns
        # joinStr = "  "
        # columns = {key: self.formatted(key) for key in keys}
        # widths = {
        #     key: max(
        #         max([len(str(item)) for item in values]), len(key)
        #     )  # +len(joinStr))
        #     for key, values in columns.items()
        # }
        # size = len(self)
        # if headTail is not None and size > 2 * headTail:
        #     indices = list(range(headTail)) + list(range(size - headTail, size))
        # else:
        #     indices = range(size)

        # s = ""
        # idxWidth = max(len(s), len(str(size)))
        # header = [f"{s:<{idxWidth}}"]
        # header += [f"{key:>{widths[key]}}" for key in columns]
        # rows = [joinStr.join(header)]

        # for n, idx in enumerate(indices):
        #     if n >= 1:
        #         if idx != indices[n - 1] + 1:
        #             rows.append("...")
        #     pdIdx = self.df.index[idx]
        #     row = [f"{pdIdx:>{idxWidth}}"]
        #     for key, lst in columns.items():
        #         value = lst[idx]
        #         width = widths[key]
        #         s = f"{value:>{width}}"
        #         row.append(s)
        #     rows.append(joinStr.join(row))

        # return "\n".join(rows)

    # @Slot(dict)
    def append(self, dct):
        """Append values in dict to DataFrame."""
        if not isinstance(dct, dict):
            msg = f"Can only append dict to Data, not {type(dct).__name__}"
            raise TypeError(msg)

        schema = self.df.columns
        for relation_name in self._activity.get_relations():
            if relation_name not in dct:
                schema.remove(relation_name)

        tmp_df = pl.DataFrame(dct, schema=schema)
        tmp_df = self._apply_relations(tmp_df, self._activity)
        self.df.extend(tmp_df)
        self.df = self.df.sort("date")
        # tmp_df = pl.concat([self.df, tmp_df])
        # tmp_df.sort("date")
        # self.df = tmp_df

        # tmp_df = pd.DataFrame.from_dict(dct)
        # tmp_df = pd.concat([self.df, tmp_df], ignore_index=True)
        # tmp_df.sort_values("date", inplace=True)
        # index = tmp_df[~tmp_df.isin(self.df)].dropna(how="all").index
        # self.df = tmp_df
        # self._update_relations(index)

        self.dataChanged.emit(index)

    def update(self, values):
        """
        Update items in the underlying DataFrame.

        `values` should be a dict; the keys should be indices and values
        should be dicts of column:value. If the value currently at the
        given column and index is different from that supplied in the
        dictionary, it will be updated.

        If changes are made, `dataChanged` is emitted.

        Example `values` structure:
            {10: {'distance':25, 'Calories':375}}
        """
        changed = []
        for index, dct in values.items():
            for col, value in dct.items():
                if self.df[index, col] != value:
                    self.df[index, col] = value
                    changed.append(index)
        if changed:
            self._update_relations(changed)
            self.dataChanged.emit(changed)

    @staticmethod
    def _apply_relations(df, activity):  # -> pd.DataFrame():
        """
        Check if relational measures in `activity` are present in `df`.

        If not, create them.
        """
        relations = activity.get_relations()
        for name, relation in relations.items():
            if name not in df.columns:
                m0 = df[relation.m0.slug]
                m1 = df[relation.m1.slug]
                # df[name] = relation.op.call(m0, m1)
                new_col = relation.op.call(m0, m1)
                df = df.with_columns(new_col.alias(name))
        return df

    def _update_relations(self, idx):
        """Recalculate relational data for all indices in iterable `idx`"""
        # recalculate relational data
        for col, relation in self._activity.get_relations().items():
            m0 = self.df[relation.m0.slug][idx]
            m1 = self.df[relation.m1.slug][idx]
            self.df[idx, col] = relation.op.call(m0, m1)

    def setDataFrame(self, df):
        """Set new DataFrame"""
        # TODO activity, _apply_relations etc?
        # called if csv changed on disk
        self.df = df
        self.dataChanged.emit(self.df.index)

    @property
    def dateTimestamps(self):
        """
        Return 'date' column, converted to array of timestamps (time since epoch).

        See also: :py:meth:`datetimes`.
        """
        return np.array([dt.timestamp() for dt in self.datetimes])

    @property
    def datetimes(self):
        """Return 'date' column, converted to list of datetime objects."""
        fmt = "%Y-%m-%d"
        # 'strptime(d.strftime(fmt), fmt)' this is ugly and is required
        # because the date column is a pandas datetime object, but it adds an
        # empty time to the date, which we need to get rid of here, before
        # calling datetime.strptime
        return [datetime.strptime(d.strftime(fmt), fmt) for d in self.df["date"]]

    def getMonth(self, month, year, return_type="DataFrame"):
        """Return DataFrame or Data of data from the given month and year."""
        # ts0 = pd.Timestamp(day=1, month=month, year=year)
        ts0 = date(year, month, 1)
        month += 1
        if month > 12:
            month %= 12
            year += 1
        # ts1 = pd.Timestamp(day=1, month=month, year=year)
        ts1 = date(year, month, 1)
        # df = self.df[(self.df["date"] >= ts0) & (self.df["date"] < ts1)]
        df = self.df.filter((pl.col("date") >= ts0) & (pl.col("date") < ts1))
        if return_type == "Data":
            df = Data(df, activity=self._activity)
        return df

    @check_empty
    def splitMonths(self, include_empty=False, return_type="DataFrame"):
        """
        Split `df` into months.

        Parameters
        -----------
        include_empty : bool
            If True and if a month has no data, a `date` and empty
            DataFrame or Data object will be included in the returned list.
            Otherwise, it  will be ignored. Default is False.
        return_type : {'DataFrame', 'Data'}
            Type of object to return with each month's data. Default is
            (polars) 'DataFrame'

        Returns
        -------
        list of (`date`, DataFrame/Data) tuples
        """
        valid_return_types = ["DataFrame", "Data"]
        if return_type not in valid_return_types:
            msg = f"Invalid return_type '{return_type}'. "
            msg += f"Valid values are {', '.join(valid_return_types)}"
            raise ValueError(msg)

        groups = data.df.group_by_dynamic("date", every="1mo")
        groups = [MonthData(month[0], group) for month, group in groups]

        if include_empty:
            # if `include_empty`, check for missing months and add empty df
            groups = self._add_empty_months(groups)

        if return_type == "Data":
            for n, (month, group) in enumerate(groups):
                df = Data(group, activity=self._activity)
                groups[n] = MonthData(month, df)

        return groups

    def _add_empty_months(self, groups):
        missing = []

        for i, (month, _) in enumerate(groups[:-1]):
            expected_next_month = month.month + 1
            expected_next_year = month.year
            if expected_next_month > 12:
                expected_next_month = 1
                expected_next_year += 1

            next_month = groups[i + 1][0]

            while (next_month.month != expected_next_month) and (
                next_month.year != expected_next_year
            ):
                month_dt = date(expected_next_year, expected_next_month, 1)
                df = pl.DataFrame(schema=self._activity.measure_slugs)
                missing.append(MonthData(month_dt, df))
                expected_next_month += 1
                if expected_next_month > 12:
                    expected_next_month = 1
                    expected_next_year += 1

        groups += missing

        return sorted(groups)

    def getMonthlyOdometer(self):
        """
        Return list of datetime objects and list of floats.

        The datetime objects are required, as they add dummy 1st of the
        month data points to reset the total to 0km.
        """
        dfs = self.splitMonths(include_empty=True)
        odo = []
        dts = []
        
        for month, df in dfs:
            col = df["distance"]
            distance = col.sum() if len(col) > 0 else 0
            dts.append(month)
            odo.append(distance)

        return dts, odo

    @check_empty
    def getPBs(self, column, pbCount):
        """
        Return indices where the value in `column` was a PB (at the time).

        Parameters
        ----------
        column : str
            Column :attr:`quickName` to look through
        pbCount : int
            Number of sessions that can be PBs simultaneously

        Returns
        -------
        idx : List[int]
            list of indices of PBs
        """
        series = self[column]
        if pbCount > len(series):
            pbCount = len(series)
        best = series[:pbCount].copy()
        idx = list(range(pbCount))  # first pbCount values will be PBs
        for n in range(pbCount, len(series)):
            if series[n] >= np.min(best):
                idx.append(n)
                # replace value in best array
                minIdx = np.argmin(best)
                best[minIdx] = series[n]
        return idx

    def combineRows(self, date):
        """Combine all rows in the dataframe with the given data."""
        idx = self.df[self.df["date"] == parseDate(date, pd_timestamp=True)].index

        # sum 'simple' data
        cols = [
            col
            for col in self.df.columns
            if self._activity.get_measure(col).relation is None
            and self._activity.get_measure(col).is_metadata is False
        ]

        for col in cols:
            series = self.df[col][idx]
            if col == "Time":
                series = [
                    hourMinSecToFloat(parseDuration(value)) for value in series
                ]  # map(hourMinSecToFloat, series)
                new_value = sum(series)
                new_value = floatToHourMinSec(new_value)
            else:
                new_value = sum(series)
            self.df.at[idx[0], col] = new_value

        i0, *idx = idx

        # recalculate relational data
        self._update_relations([i0])

        self.df.drop(idx, inplace=True)
        self.dataChanged.emit(i0)

    def removeRows(self, **kwargs):
        """
        Remove row(s) from the DataFrame by date or index.

        Pass either 'dates' or 'index' kwarg.

        Note that this assumes dates are unique in the object.
        """
        dates = kwargs.get("dates", None)
        if dates is not None:
            if isinstance(dates, str):
                dates = [dates]
            if not isinstance(dates, list):
                raise TypeError("Data.removeRows takes list of dates")

            idx = []
            for date in dates:
                idx += list(
                    self.df[self.df["date"] == parseDate(date, pd_timestamp=True)].index
                )

            self.df.drop(idx, inplace=True)
            self.dataChanged.emit(None)

        index = kwargs.get("index", None)
        if index is not None:
            self.df.drop(index, inplace=True)
            self.dataChanged.emit(None)


if __name__ == "__main__":

    def known_data():
        dates = [f"{i:02}-04-2021" for i in range(26, 31)]
        dates += [f"{i:02}-05-2021" for i in range(1, 6)]
        dates = [parseDate(d) for d in dates]

        times = [
            "00:53:27",
            "00:43:04",
            "00:42:40",
            "00:43:09",
            "00:42:28",
            "00:43:19",
            "00:42:21",
            "00:43:04",
            "00:42:11",
            "00:43:25",
        ]
        times = np.array([hourMinSecToFloat(t) for t in times])

        dct = {
            "date": dates,
            "time": times,
            "distance": np.array(
                [30.1, 25.14, 25.08, 25.41, 25.1, 25.08, 25.13, 25.21, 25.08, 25.12]
            ),
            "gear": [6] * 10,
        }
        dct["calories"] = dct["distance"] * 14.956
        # dct["speed"] = dct["distance"] / times
        return dct

    from pathlib import Path
    import json
    from tracks.activities import Activity

    data_path = Path.home().joinpath(".tracks")
    csv_file = data_path.joinpath("cycling_no_speed.csv")
    df = pl.read_csv(csv_file, try_parse_dates=True)

    json_path = data_path.joinpath("activities.json")
    with open(json_path, "r") as fileobj:
        all_activities = json.load(fileobj)
    activity_json = all_activities.get("cycling")
    activity = Activity(activity_json["name"])
    for measure in activity_json["measures"].values():
        activity.add_measure(**measure)

    data = Data(df, activity=activity)

    months = data.splitMonths(include_empty=True)
    # print(months)
    