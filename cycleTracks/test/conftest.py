from PyQt5.QtCore import QCoreApplication
import os, shutil
import pytest

@pytest.fixture
def patchSettings(monkeypatch):
    appName = "Cycle Tracks"
    orgName = "kzm"
    d = os.path.dirname(__file__)
    # if conf file exists in test dir, remove it, so we're always testing with
    # defaults, unless changed in te test
    confFile = os.path.join(d, ".config", orgName, appName+".conf")
    if os.path.exists(confFile):
        os.remove(confFile)
    monkeypatch.setenv("HOME", d)
    QCoreApplication.setApplicationName(appName)
    QCoreApplication.setOrganizationName(orgName)
    
    
@pytest.fixture
def rmSettings():
    appName = "Cycle Tracks"
    orgName = "kzm"
    d = os.path.dirname(__file__)
    # if conf file exists in test dir, remove it, so we're always testing with
    # defaults, unless changed in te test
    confFile = os.path.join(d, ".config", orgName, appName+".conf")
    if os.path.exists(confFile):
        # shutil.rmtree("/home/keziah/projects/cycleTracks/cycleTracks/test/.config") #os.path.join(d, ".config"))
        os.remove(r"/home/keziah/projects/cycleTracks/cycleTracks/test/.config/kzm/Cycle Tracks.conf")