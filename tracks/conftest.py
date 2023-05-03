from qtpy.QtCore import QCoreApplication
from dataclasses import dataclass
import os
import pytest

@dataclass
class Variables:
    wait: int = 100
    shortWait: int = 10
    longWait: int = 30000
    mouseDelay: int = 50

@pytest.fixture(autouse=True)
def patchSettings(monkeypatch):
    appName = "Cycle Tracks"
    orgName = "Tracks"
    d = os.path.dirname(__file__)
    # if conf file exists in test dir, remove it, so we're always testing with
    # defaults, unless changed in the test
    confFile = os.path.join(d, ".config", orgName, appName+".conf")
    if os.path.exists(confFile):
        os.remove(confFile)
    monkeypatch.setenv("HOME", d)
    QCoreApplication.setApplicationName(appName)
    QCoreApplication.setOrganizationName(orgName)

@pytest.fixture()
def variables():
    v = Variables()
    return v