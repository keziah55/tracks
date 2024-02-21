from qtpy.QtCore import QCoreApplication
from customQObjects.core import Settings
from dataclasses import dataclass
from pathlib import Path
import pytest
import shutil


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
    target_json_dir = patch_dir.joinpath(".tracks")
    if not target_json_dir.exists():
        target_json_dir.mkdir()
    target_json_path = target_json_dir.joinpath("activities.json")
    # if not target_json_path.exists():
    source_json_path = Path(__file__).parent.joinpath("test", "data", "activities.json")
    shutil.copy2(source_json_path, target_json_path)
    return target_json_path


@pytest.fixture(autouse=True)
def patch_settings(monkeypatch, patch_dir, activity_json_path):
    app_name = "Tracks"
    org_name = "Tracks"

    # if conf file exists in test dir, remove it, so we're always testing with
    # defaults, unless changed in the test
    conf_file = patch_dir.joinpath(".config", org_name, app_name + ".conf")
    if conf_file.exists():
        conf_file.unlink()
    monkeypatch.setenv("HOME", str(patch_dir))
    QCoreApplication.setApplicationName(app_name)
    QCoreApplication.setOrganizationName(org_name)

    plot_style_file = patch_dir.joinpath(".tracks", "plot_styles.json")
    plot_style_file.unlink(missing_ok=True)
    monkeypatch.setattr(Settings, "fileName", lambda *args, **kwargs: conf_file)


@pytest.fixture()
def variables():
    v = Variables()
    return v
