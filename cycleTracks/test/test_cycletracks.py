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
    
    @pytest.mark.skip("test not yet written")
    def test_add_data(self, setup, qtbot, teardown):
        pass
    
    @pytest.mark.skip("test not yet written")
    def test_plot_clicked(self, setup, qtbot, teardown):
        # test that clicking on the plot highlights the nearest plot in the viewer
        pass

    @pytest.mark.skip("test not yet written")
    def test_viewer_clicked(self, setup, qtbot, teardown):
        # test that clicking on an item in the viewer highlights the corresponding point in the plot
        pass