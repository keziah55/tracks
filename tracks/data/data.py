#!/usr/bin/env python3
"""
Object providing convenient access to the contents of a DataFrame.
"""

from qtpy.QtCore import QObject
from qtpy.QtCore import Signal, Slot
from tracks.util import parseDate, parseDuration, hourMinSecToFloat, floatToHourMinSec
from collections import namedtuple
from datetime import date, datetime
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


class Data(QObject):
    data_changed = Signal(object)
    """
    **signal** data_changed(object `index`)

    Emitted when the data in the object is changed, with the pandas index
    of the new rows.
    """

    new_max = Signal(str, object)
    """
    **signal** new_max(str `column`, object `value`)

    Emitted when newly added data contains a new max value for a given column.
    """

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
        except AttributeError:
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

    def summary_string(self, key, func=sum, unit=False):
        measure = self._activity[key]
        s = measure.summarised(self[key], include_unit=unit)
        return s

    def make_summary(self, unit=False) -> dict:
        summaries = {
            slug: self.summary_string(slug, unit=unit)
            for slug, measure in self._activity.measures.items()
            if measure.summary is not None
        }
        return summaries

    def __len__(self):
        return len(self.df)

    def __getitem__(self, key):
        """
        If given column name, return that column.

        If given index and column name, return item at that position.
        """
        if isinstance(key, tuple):
            idx, key = key
            return self.df[int(idx), key]

        elif isinstance(key, str):
            if key in self.df.columns:
                # return self.df[key]
                # name = self._quickNames[key]
                return getattr(self, key)
            else:
                raise NameError(f"{key} not a valid property name.")

        else:
            raise KeyError(f"Cannot access item with key {key}")

    def __getattr__(self, name):
        ret = self.df[name]
        return ret

    def __repr__(self):
        return self.to_string(headTail=5)

    def row(self, idx, formatted=False):
        """
        Return row `idx` as dict.

        If `formatted` is True, also format the values.
        """
        row = dict(zip(self.df.columns, self.df.row(idx)))
        if formatted:
            row = {
                name: self._activity.get_measure(name).formatted(value)
                for name, value in row.items()
            }
        return row

    def to_string(self, headTail=None):
        """
        Return Data object as a string.

        Parameters
        ----------
        headTail : int, optional
            If provided, abridge the object to show only the first and last
            `headTail` rows. By default, do not abridge and return the full object.
        """
        return repr(self.df)

    @Slot(dict)
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

        num_new = len(tmp_df)
        size = len(self.df)
        index = list(range(size - num_new, size))

        self.data_changed.emit(index)

    def update(self, values):
        """
        Update items in the underlying DataFrame.

        `values` should be a dict; the keys should be indices and values
        should be dicts of column:value. If the value currently at the
        given column and index is different from that supplied in the
        dictionary, it will be updated.

        If changes are made, `data_changed` is emitted.

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
            self.data_changed.emit(changed)

    @staticmethod
    def _apply_relations(df, activity) -> pl.DataFrame():
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

    def set_data_frame(self, df):
        """Set new DataFrame"""
        # TODO activity, _apply_relations etc?
        # called if csv changed on disk
        self.df = df
        self.data_changed.emit(self.df.index)

    @property
    def date_timestamps(self):
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

    def get_month(self, month, year, return_type="DataFrame"):
        """Return DataFrame or Data of data from the given month and year."""
        ts0 = date(year, month, 1)
        month += 1
        if month > 12:
            month %= 12
            year += 1
        ts1 = date(year, month, 1)
        df = self.df.filter((pl.col("date") >= ts0) & (pl.col("date") < ts1))
        if return_type == "Data":
            df = Data(df, activity=self._activity)
        return df

    @check_empty
    def split_months(self, include_empty=False, return_type="DataFrame"):
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

        groups = self.df.group_by_dynamic("date", every="1mo")
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

    def get_monthly_odometer(self):
        """
        Return list of datetime objects and list of floats.

        The datetime objects are required, as they add dummy 1st of the
        month data points to reset the total to 0km.
        """
        dfs = self.split_months(include_empty=True)
        odo = []
        dts = []

        for i, (month_year, df) in enumerate(dfs):
            # at the start of every month, insert 0km entry
            if df.is_empty():
                # if there's no data in the df, make new dt
                month = month_year.month
                year = month_year.year
            else:
                month = df["date"][0].month
                year = df["date"][0].year
            tmp = date(year, month, 1)
            dts.append(tmp)
            odo.append(0)

            for row in df.rows(named=True):
                dt = row["date"]
                dist = odo[-1] + row["distance"]
                dts.append(dt)
                odo.append(dist)

        return dts, odo

    @check_empty
    def get_pbs(self, column, pbCount):
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
        best = list(series[:pbCount])
        idx = list(range(pbCount))  # first pbCount values will be PBs
        for n in range(pbCount, len(series)):
            if series[n] >= np.min(best):
                idx.append(n)
                # replace value in best array
                minIdx = np.argmin(best)
                best[minIdx] = series[n]
        return idx

    def combine_rows(self, date):
        """Combine all rows in the dataframe with the given data."""
        d = parseDate(date)
        idx = self.df.with_row_index().filter(pl.col("date") == d)["index"]

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
                series = [hourMinSecToFloat(parseDuration(value)) for value in series]
                new_value = sum(series)
                new_value = floatToHourMinSec(new_value)
            else:
                new_value = sum(series)
            self.df[idx[0], col] = new_value

        i0, *idx = idx

        # recalculate relational data
        self._update_relations([i0])

        self._drop_by_index(idx)
        self.data_changed.emit(i0)

    def remove_rows(self, **kwargs):
        """
        Remove row(s) from the DataFrame by date or index.

        Pass either 'dates' or 'index' kwarg.
        """
        idx = kwargs.get("index", [])

        dates = kwargs.get("dates", None)
        if dates is not None:
            if isinstance(dates, str):
                dates = [dates]
            if not isinstance(dates, list):
                raise TypeError("Data.removeRows takes list of dates")

            dates = [parseDate(date) for date in dates]
            idx += self.df.with_row_index().filter(pl.col("date").is_in(dates))["index"]

        if idx:
            self._drop_by_index(idx)
            self.data_changed.emit(None)

    def _drop_by_index(self, idx):
        """
        Drop rows from the Data object, by index.

        Parameters
        ----------
        idx : list[int]
            List of indices
        """
        self.df = self.df.with_row_index().filter(~pl.col("index").is_in(idx)).drop("index")

    def sort(self, *args, return_type="Data", with_index=False, index_name="index", **kwargs):
        """
        Return new Data object (or polars DataFrame) with sorted data.

        See
        [Dataframe.sort](https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.sort.html)
        for args.

        Parameters
        ----------
        args
            [Dataframe.sort](https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.sort.html)
            args
        return_type : {"Data", "DataFrame"}
            Whether to return as `Data` object or polars `DataFrame`
        with_index : bool
            If True, add index column before sorting.
        index_name : str, optional
            If `with_index`, optionally set the name of the index column. Default is "index".
        kwargs
            [Dataframe.sort](https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.sort.html)
            kwargs
        """
        df = self.df.with_row_index(name=index_name) if with_index else self.df
        df = df.sort(*args, **kwargs)
        if return_type == "Data":
            df = Data(df, activity=self._activity)
        return df
