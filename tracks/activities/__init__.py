from .activities import Activity, Relation
from .dtypes import get_cast_method, get_validate_method
from .operations import Divide, Divide_time_min
import json

def load_activity(p):
    """ Load activity from pickled file `p` """
    with open(p, "r") as fileobj:
        activity_json = json.load(fileobj)
        
    activity = Activity(activity_json['name'])
    for name, measure in activity_json['measures'].items():
        activity.add_measure(**measure)
        
    return activity

__all__ = ["Activity", "Relation", "Divide", "Divide_time_min", "load_activity",
           "get_cast_method", "get_validate_method"]