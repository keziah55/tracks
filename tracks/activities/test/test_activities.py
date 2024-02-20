from .. import Activity, Relation, Divide, Divide_time_min
import tempfile
from pathlib import Path
import shutil
from datetime import datetime
import json
import pytest

def get_format_test_params():
    params = [
        ("date", datetime(2024, 2, 20, 0, 0, 0), "20 Feb 2024"),
        ("time", 0.5, "00:30:00"),
        ("distance", 12.1, "12.10"),
        ("speed", 25.4567891, "25.46"),
        ("calories", 500.27, "500.3"),
        ("steps", 7050, "7050"),
        ("step_rate", 10.23456, "10.235"),
        ]
    return params

def get_op_test_params():
    params = [
        (Divide, 15, 5, 3.0),
        (Divide_time_min, 15, 5, 0.05)
    ]
    return params

class TestActivities:
    
    @classmethod
    def setup_class(cls):
        cls.tmp_dir = Path(tempfile.mkdtemp(prefix="tracks-", suffix="-activities"))
        
    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.tmp_dir)
    
    @pytest.fixture
    def demo_activity(self):
        p = self.tmp_dir.joinpath("activities.json")
        with open(p) as fileobj:
            activities = json.load(fileobj)
            
        key = "running"
        running = activities[key]
        
        activity = Activity(key)
        for measure_name, measure in running['measures'].items():
            if measure_name == "step_rate":
                with pytest.warns(UserWarning):
                    activity.add_measure(**measure)
            else:
                activity.add_measure(**measure)
        return activity
    
    def test_create_activity(self):
        
        activity = Activity("running")
        
        activity.add_measure(
            name = "Date",
            dtype = "date", 
            summary = None, 
            is_metadata=True,
            plottable = False,
        )
            
        activity.add_measure(
            name = "Time",
            dtype = "duration", 
            summary = "sum", 
            unit = "h", 
            show_unit = False, 
            cmp_func = "hourMinSecToFloat",
        )
        
        activity.add_measure(
            name = "Distance",
            dtype = "float", 
            summary = "sum", 
            sig_figs = 2,
            unit = "km", 
            cmp_func = float,
        )
        
        activity.add_measure(
            name = "Speed",
            dtype = "float", 
            summary = "max", 
            sig_figs = 2,
            relation = Relation(activity.distance, activity.time, Divide, "Speed"), 
            cmp_func = float,
        )
        
        activity.add_measure(
            name = "Calories",
            dtype = "float", 
            summary = "sum", 
            sig_figs = 1,
            cmp_func = float,
        )
        
        activity.add_measure(
            name = "Steps",
            dtype = "int", 
            summary = "mean", 
            cmp_func = float,
            show_unit = False,
        )
    
        with pytest.warns(UserWarning):
            activity.add_measure(
                name = "Step rate",
                dtype = "float",
                summary = "max",
                sig_figs = 3,
                relation = Relation(activity.steps, activity.time, Divide_time_min, "Step rate"),
                cmp_func = float,
            )
        
        activity.save(self.tmp_dir)
        p = self.tmp_dir.joinpath("activities.json")
        assert p.exists()
        
        new_activity = Activity("boxing")
        new_activity.add_measure(
            name = "Date",
            dtype = "date", 
            summary = None, 
            is_metadata=True,
            plottable = False,
        )
            
        new_activity.add_measure(
            name = "Time",
            dtype = "duration", 
            summary = "sum", 
            unit = "h", 
            show_unit = False, 
            cmp_func = "hourMinSecToFloat",
        )
        new_activity.save(self.tmp_dir)
        
    def test_load_activity(self):
        p = self.tmp_dir.joinpath("activities.json")
        with open(p) as fileobj:
            activities = json.load(fileobj)
            
        keys = ["running", "boxing"]
        assert set(keys) == set(activities.keys())
        
        key = keys[0]
        running = activities[key]
        
        activity = Activity(key)
        for measure_name, measure in running['measures'].items():
            if measure_name == "step_rate":
                with pytest.warns(UserWarning):
                    activity.add_measure(**measure)
            else:
                activity.add_measure(**measure)
            
    def test_relations(self, demo_activity):
        relations = demo_activity.get_relations()
        expected_relations = ["speed", "step_rate"]
        assert set(expected_relations) == set(relations.keys())
        assert demo_activity.speed.unit == "km/h"
        assert demo_activity.step_rate.unit is None
        
        for measure_name, measure in demo_activity.measures.items():
            if measure_name in expected_relations:
                assert measure.user is False
            else:
                assert measure.user is True
                
        expected_header = ["Date", "Time", "Distance (km)", "Calories", "Steps"]
        assert set(expected_header) == set(demo_activity.user_input_header)
    
    @pytest.mark.parametrize(["measure", "value", "expected"], get_format_test_params())
    def test_measure_formatted(self, demo_activity, measure, value, expected):
        m = demo_activity[measure]
        assert m.formatted(value) == expected
        
    def test_unknown_measure(self, demo_activity):
        measure = "invalid"
        
        with pytest.raises(AttributeError):
            demo_activity.invalid
        
        with pytest.raises(AttributeError):
            demo_activity[measure]
            
        with pytest.raises(ValueError):
            demo_activity.get_measure(measure)
            
        with pytest.raises(ValueError):
            demo_activity.get_measure_from_full_name(measure)
        
    def test_filter_measures(self, demo_activity):
        filtered = demo_activity.filter_measures("show_unit", lambda value: value is False)
        expected = ["time", "steps"]
        assert set(expected) == set(filtered.keys())

@pytest.mark.parametrize(["op", "a", "b", "expected"], get_op_test_params())
def test_operations(op, a, b, expected):
    assert op.call(a,b) == expected
