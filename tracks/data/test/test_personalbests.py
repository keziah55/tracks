from .. import PersonalBests
from ..personalbests import NewPBDialog
from tracks.util import parseDate, parseDuration, hourMinSecToFloat
from tracks.test import MockParent
from qtpy.QtWidgets import QWidget, QVBoxLayout, QDialog
import pytest

pytest_plugin = "pytest-qt"

# parameters for test_new_data
def getNewData(key):
    newDataParams = {
        'best month and best session': (
            {
                'date':[parseDate("6 May 2021", pd_timestamp=True)], 
                'time':[hourMinSecToFloat(parseDuration("00:42:15"))], 
                'distance':[25.1], 
                'calories':[375.4], 
                'gear':[6]
            },
            "<center><span>New #2 speed - </span><span style='color: #f7f13b'>35.64 km/h</span>!<br>and<br><span>New best month - </span><span style='color: #f7f13b'>May 2021</span>!<br><span>Congratulations!</span></center>",
            "<b>May 2021</b>: <b>150.72</b> km, <b>04:16:35</b> hours, <b>2254.2</b> calories"
        ),
        'best month':(
            {
                'date':[parseDate("6 May 2021", pd_timestamp=True)], 
                'time':[hourMinSecToFloat(parseDuration("00:45:15"))], 
                'distance':[25.1], 
                'calories':[375.4], 
                'gear':[6]
            },
            "<center><span>New best month - </span><span style='color: #f7f13b'>May 2021</span>!<br><span>Congratulations!</span></center>",
            "<b>May 2021</b>: <b>150.72</b> km, <b>04:19:35</b> hours, <b>2254.2</b> calories"
        ),
        'best session': (
            {
                'date':[parseDate("6 April 2021", pd_timestamp=True)], 
                 'time':[hourMinSecToFloat(parseDuration("00:42:15"))], 
                 'distance':[25.1], 
                 'calories':[375.4], 
                 'gear':[6]
            },
            "<center><span>New #2 speed - </span><span style='color: #f7f13b'>35.64 km/h</span>!<br><span>Congratulations!</span></center>",
            "<b>April 2021</b>: <b>155.93</b> km, <b>04:27:03</b> hours, <b>2332.1</b> calories"
        )
    }
    return newDataParams[key]
    
class TestPersonalBests:
    
    @pytest.fixture
    def setup(self, qtbot):
        # make Data object with known data
        self.parent = MockParent(random=False)
        self.pb = PersonalBests(self.parent.data, self.parent.activity)
        self.pb.newPBdialog.timer.setInterval(100) # don't need 3 seconds for tests
        self.widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.pb.bestMonth)
        layout.addWidget(self.pb.bestSessions)
        self.widget.setLayout(layout)
        
        qtbot.addWidget(self.widget)
        self.widget.setGeometry(100, 100, 500, 600)
        
        self.parent.data.dataChanged.connect(self.pb.newData)
        self.widget.show()
        
    @pytest.mark.parametrize("key", ['best month and best session', 'best month', 'best session'])
    def test_new_data(self, setup, qtbot, key):
        
        new, expected_dialog, expected_label = getNewData(key)
        
        signals = [(self.parent.data.dataChanged, 'data.dataChanged'),
                   (self.pb.newPBdialog.accepted, 'dialog.accepted')]
        with qtbot.waitSignals(signals):
            self.parent.data.append(new)
            
        assert self.pb.newPBdialog.label.text() == expected_dialog
        
        assert self.pb.bestMonth.text() == expected_label
        
    def test_new_data_different_column(self, setup, qtbot, monkeypatch, variables):
        # test dialog message when table is sorted by Time
        new = {'date':[parseDate("7 April 2021", pd_timestamp=True)], 
               'time':[hourMinSecToFloat(parseDuration("01:05:03"))], 
               'distance':[25.08], 'calories':[375.1], 'gear':[6]}
        
        self.pb.bestSessions.horizontalHeader().sectionClicked.emit(1)
        qtbot.wait(variables.shortWait)
        
        # don't need dialog to pop up
        monkeypatch.setattr(NewPBDialog, "exec_", lambda *args: QDialog.Accepted)
        with qtbot.waitSignal(self.parent.data.dataChanged):
            self.parent.data.append(new)
            
        expected = "<center><span>New #1 time - </span><span style='color: #f7f13b'>01:05:03</span>!<br><span>Congratulations!</span></center>"
        assert self.pb.newPBdialog.label.text() == expected   
        
    def test_tied_data(self, setup, qtbot, monkeypatch):
        new = {'date':[parseDate("7 May 2021", pd_timestamp=True)], 
               'time':[hourMinSecToFloat(parseDuration("00:42:11"))], 
               'distance':[25.08], 'calories':[375.1], 'gear':[6]}
        
        # don't need dialog to pop up
        monkeypatch.setattr(NewPBDialog, "exec_", lambda *args: QDialog.Accepted)
        with qtbot.waitSignal(self.parent.data.dataChanged):
            self.parent.data.append(new)
            
        rowNums = [self.pb.bestSessions.verticalHeaderItem(i).text() 
                   for i in range(self.pb.bestSessions.rowCount())]
        assert rowNums == ["1=", "1=", "3", "4", "5"]
        
        date0 = self.pb.bestSessions.item(0, 0).text()
        assert date0 == "07 May 2021"
        
        date1 = self.pb.bestSessions.item(1, 0).text()
        assert date1 == "04 May 2021"
        
    def test_sort_column(self, setup, qtbot, variables):
        # dict of sortable columns and list of expected dates
        columns = {'time':['26 Apr 2021', '05 May 2021', '01 May 2021', '29 Apr 2021', '03 May 2021'], 
                   'distance':['26 Apr 2021', '29 Apr 2021', '03 May 2021', '27 Apr 2021', '02 May 2021'], 
                   'speed':['04 May 2021', '02 May 2021', '30 Apr 2021', '29 Apr 2021', '28 Apr 2021'], 
                   'calories':['26 Apr 2021', '29 Apr 2021', '03 May 2021', '27 Apr 2021', '02 May 2021']}
        
        for column, expected in columns.items():
            idx = self.pb.bestSessions._activity.measure_slugs.index(column)
            
            self.pb.bestSessions.horizontalHeader().sectionClicked.emit(idx)
            qtbot.wait(variables.shortWait)
            items = [self.pb.bestSessions.item(idx, 0).text() for idx in range(self.pb.bestSessions.rowCount())]
            assert items == expected
            
    def test_get_best_sessions(self, setup, qtbot):
        pb = self.pb.bestSessions._getBestSessions(num=2, key="distance", order='ascending')
        expected = [{'date':"04 May 2021",
                     'time':"00:42:11",
                     'distance':"25.08",
                     'gear':"6",
                     'calories':"375.1"},
                    {'date':"01 May 2021",
                     'time':"00:43:19",
                     'distance':"25.08",
                     'gear':"6",
                     'calories':"375.1"}]
        for n, pb_data in enumerate(pb):
            for key, value in expected[n].items():
                assert pb_data[key] == value
                
        with pytest.raises(ValueError):
            self.pb.bestSessions._getBestSessions(order='acsending')
        