from cycleTracks.cycletracks import CycleTracks
from . import makeDataFrame
import tempfile
import pytest

pytest_plugin = "pytest-qt"
pytestmark = pytest.mark.filterwarnings("error")

class TestTracks:
    
    @pytest.fixture
    def setup(self, qtbot, monkeypatch):
        
        self.tmpfile = tempfile.NamedTemporaryFile()
        makeDataFrame(1000, path=self.tmpfile.name)
        
        def mockGetFile(*args, **kwargs):
            return self.tmpfile.name
        monkeypatch.setattr(CycleTracks, "getFile", mockGetFile)
        self.app = CycleTracks()
        
    @pytest.fixture
    def teardown(self):
        yield
        self.app.close()
        
    def test_app(self, setup, qtbot, teardown):
        # qtbot.wait(10000)
        pass