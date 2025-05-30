from .. import Data
from tracks.test import make_dataframe
from tracks.test.mockparent import load_activity
import polars as pl
import numpy as np
import random
import pytest

pytest_plugin = "pytest-qt"


@pytest.fixture
def setup(activity_json_path):
    df = make_dataframe(500)
    activity = load_activity(activity_json_path)
    data = Data(df, activity=activity)
    return data, activity


def test_properties(setup):
    data, activity = setup
    assert set(data.df.columns) == set(activity.measures.keys())
    for name in data.df.columns:
        d = list(data[name])
        assert d == list(data.df[name])


def test_group_months(setup):
    data, activity = setup
    dfs = data.split_months()
    for _, df in dfs:
        if not df.is_empty():
            dates = df["date"]
            monthyear = [(date.month, date.year) for date in dates]
            assert len(set(monthyear)) == 1


def test_combine_rows(setup, qtbot):
    data, activity = setup
    df = data.df.clone()

    row = random.randrange(len(df))

    while True:
        replace = random.sample(range(len(df)), 3)
        if row not in replace:
            break

    names = df.columns

    expected = {name: df[row, name] for name in names}

    for idx in replace:
        df[idx, "date"] = expected["date"]
        df[idx, "gear"] = expected["gear"]
        expected["distance"] += df[idx, "distance"]
        expected["calories"] += df[idx, "calories"]
        expected["time"] += df[idx, "time"]
    expected["speed"] = expected["distance"] / expected["time"]
    expected["time"] = expected["time"]

    data = Data(df, activity)
    date = expected["date"].strftime("%d %b %Y")

    with qtbot.waitSignal(data.data_changed):
        data.combine_rows(date)

    tmp_df = data.df.filter(pl.col("date") == expected["date"])
    assert len(tmp_df) == 1

    for name in names:
        measure = activity[name]
        fail_msg = "\n".join(
            [
                f"failed formatting '{name}' on measure '{measure}'"
                f"Actual value={tmp_df[name]}"
                f"Expected value={expected[name]}"
            ]
        )
        assert measure.formatted(tmp_df[name][0]) == measure.formatted(expected[name]), fail_msg


def test_monthly_odometer(setup):
    _, activity = setup
    df = make_dataframe(random=False)
    data = Data(df, activity)

    dts, odo = data.get_monthly_odometer()

    df_idx = 0
    expected_dist = 0

    for i in range(len(dts)):
        dt = dts[i]
        dist = odo[i]

        if i == 0 or dt.day == 1 and dts[i - 1] != dt:
            # new month
            expected_dist = 0
        else:
            row = df[df_idx]
            assert row["date"][0] == dt
            expected_dist += row["distance"][0]
            df_idx += 1
        assert dist == expected_dist
