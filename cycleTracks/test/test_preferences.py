from .test_cycletracks import TracksSetupTeardown

pytest_plugin = "pytest-qt"

class TestPreferences(TracksSetupTeardown):
    
    def test_plot_range(self, setup, qtbot):
        pass