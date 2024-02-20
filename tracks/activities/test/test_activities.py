from .. import Activity, Relation, ActivityManager, Divide, Divide_time_min
import tempfile
from pathlib import Path
import shutil
import json
import pytest

class TestActivities:
    
    @pytest.fixture
    def setup(self):
        pass
    
    @classmethod
    def setup_class(cls):
        cls.tmp_dir = Path(tempfile.mkdtemp(prefix="tracks-", suffix="-activities"))
        
    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.tmp_dir)
    
    def test_create_activity(self, setup):
        
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
            unit = "steps"
        )
    
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
        
        
    def test_load_activity(self, setup):
        p = self.tmp_dir.joinpath("activities.json")
        with open(p) as fileobj:
            activities = json.load(fileobj)
            
        keys = ["running", "boxing"]
        assert set(keys) == set(activities.keys())
        
        key = keys[0]
        running = activities[key]
        
        activity = Activity(key)
        for measure in running['measures'].values():
            activity.add_measure(**measure)
            
        relations = activity.get_relations()
        assert {"speed", "step_rate"} == set(relations.keys())
    