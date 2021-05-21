from .test_cycletracks import TracksSetupTeardown
import pytest

pytest_plugin = "pytest-qt"

class TestPreferences(TracksSetupTeardown):
    
    @pytest.mark.skip("test not yet written")
    def test_plot_range(self, setup, qtbot):
        pass