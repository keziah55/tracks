from qtpy.QtCore import QCoreApplication
from customQObjects.core import Settings
from dataclasses import dataclass
from pathlib import Path
import pytest

@dataclass
class Variables:
    wait: int = 100
    shortWait: int = 10
    longWait: int = 30000
    mouseDelay: int = 50
    
@pytest.fixture()
def patch_dir():
    patch_dir = Path(__file__).parent.joinpath(".mock_test_dir")
    if not patch_dir.exists():
        patch_dir.mkdir(parents=True)
    return patch_dir
    
@pytest.fixture()
def activity_json_path(patch_dir):
    json_path = patch_dir.joinpath(".tracks", "cycling.json")
    if not json_path.exists():
        json_path.symlink_to(Path(__file__).parent.joinpath("test", "test_data", "cycling.json"))
    return json_path

@pytest.fixture(autouse=True)
def patchSettings(monkeypatch, patch_dir, activity_json_path):
    app_name = "Tracks"
    org_name = "Tracks"
    
    # patch_dir = Path(__file__).parent.joinpath(".mock_test_dir")
    # if not patch_dir.exists():
    #     patch_dir.mkdir(parents=True)
        
    # json_path = patch_dir.joinpath(".tracks", "cycling.json")
    # if not json_path.exists():
    #     json_path.symlink_to(Path(__file__).parent.joinpath("test", "test_data", "cycling.json"))
        
    # if conf file exists in test dir, remove it, so we're always testing with
    # defaults, unless changed in the test
    conf_file = patch_dir.joinpath(".config", org_name, app_name+".conf")
    if conf_file.exists():
        conf_file.unlink()
    monkeypatch.setenv("HOME", str(patch_dir))
    QCoreApplication.setApplicationName(app_name)
    QCoreApplication.setOrganizationName(org_name)
    
    plot_style_file = conf_file.parent.joinpath('plotStyles.ini')
    if plot_style_file.exists():
        plot_style_file.unlink()
    monkeypatch.setattr(Settings, "fileName", lambda *args, **kwargs: conf_file)

@pytest.fixture()
def variables():
    v = Variables()
    return v