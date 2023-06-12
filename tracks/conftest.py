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

@pytest.fixture(autouse=True)
def patchSettings(monkeypatch):
    appName = "Tracks"
    orgName = "Tracks"
    # if conf file exists in test dir, remove it, so we're always testing with
    # defaults, unless changed in the test
    confFile = Path(__file__).parent.joinpath(".config", orgName, appName+".conf")
    if confFile.exists():
        confFile.unlink()
    monkeypatch.setenv("HOME", str(Path(__file__).parent))
    QCoreApplication.setApplicationName(appName)
    QCoreApplication.setOrganizationName(orgName)
    
    plotStyleFile = confFile.parent.joinpath('plotStyles.ini')
    if plotStyleFile.exists():
        plotStyleFile.unlink()
    monkeypatch.setattr(Settings, "fileName", lambda *args, **kwargs: confFile)

@pytest.fixture()
def variables():
    v = Variables()
    return v