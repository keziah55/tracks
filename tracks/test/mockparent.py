from tracks.activities import Activity
from tracks.data import Data
from . import make_dataframe
import json
from pathlib import Path
import polars as pl


def load_activity(json_path, activity_name="cycling"):
    with open(json_path, "r") as fileobj:
        all_activity_json = json.load(fileobj)

    activity_json = all_activity_json[activity_name]

    activity = Activity(activity_json["name"])
    for measure in activity_json["measures"].values():
        activity.add_measure(**measure)

    return activity


# TODO move to conftest.py?
class MockParent:
    """Mock Tracks object.

    Data can be passed in with `dct` or a pre-determined data set can be
    used by passing `known=True`. If neither `dct` nor `known` are passed,
    random data will be generated.

    Parameters
    ----------
    dct : dict, optional
        If provided, make DataFrame from this dict. Default is None, generate
        random data. See also `fixed`.
    random : bool, optional
        If True (and `dct` not supplied) generate random data. Otherwise,
        use pre-set data. Default is True.
    size : int, optional
        If generating random data, make DataFrame of this length. Default is 500.
    """

    def __init__(self, **kwargs):
        dct = kwargs.get("dct", None)
        random = kwargs.get("random", True)
        if dct is None:
            size = kwargs.get("size", 500)
            self.df = make_dataframe(random=random, size=size)
        else:
            self.df = pl.from_dict(dct)

        json_path = Path(__file__).parent.parent.joinpath(
            ".mock_test_dir", ".tracks", "activities.json"
        )
        self.activity = load_activity(json_path, "cycling")

        self.data = Data(self.df, activity=self.activity)
        self.dataAnalysis = None
