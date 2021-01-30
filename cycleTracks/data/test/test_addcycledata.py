from cycleTracks.data import AddCycleData
import pytest

pytest_plugin = "pytest-qt"

class TestAddCycleData:
    
    @pytest.fixture
    def setup(self, qtbot):
        
        self.widget = AddCycleData()
        qtbot.addWidget(self.widget)
        self.widget.show()
        
        
    def test_add_data(self, setup, qtbot):
        pass