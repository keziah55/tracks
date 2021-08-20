from cycleTracks.data import PersonalBests
from cycleTracks.data.personalbests import NewPBDialog
from cycleTracks.util import parseDate, parseDuration
from cycleTracks.test import MockParent
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QDialog
import pytest

pytest_plugin = "pytest-qt"

# parameters for test_new_data
def getNewData(key):
    newDataParams = {'best month and best session':
                     ({'Date':[parseDate("6 May 2021", pd_timestamp=True)], 
                       'Time':[parseDuration("00:42:15")], 
                       'Distance (km)':[25.1], 'Calories':[375.4], 'Gear':[6]},
                      "<center><span>New #2 avg. speed - </span><span style='color: #f7f13b'>35.64km/h</span>!<br>and<br><span>New best month - </span><span style='color: #f7f13b'>May 2021</span>!<br><span>Congratulations!</span></center>",
                      "<b>May 2021</b>: <b>150.72</b> km, <b>04:16:35</b> hours, <b>2254.2</b> calories"),
                     'best month':
                     ({'Date':[parseDate("6 May 2021", pd_timestamp=True)], 
                       'Time':[parseDuration("00:45:15")], 
                       'Distance (km)':[25.1], 'Calories':[375.4], 'Gear':[6]},
                      "<center><span>New best month - </span><span style='color: #f7f13b'>May 2021</span>!<br><span>Congratulations!</span></center>",
                      "<b>May 2021</b>: <b>150.72</b> km, <b>04:19:35</b> hours, <b>2254.2</b> calories"
                      ),
                     'best session':
                     ({'Date':[parseDate("6 April 2021", pd_timestamp=True)], 
                       'Time':[parseDuration("00:42:15")], 
                       'Distance (km)':[25.1], 'Calories':[375.4], 'Gear':[6]},
                      "<center><span>New #2 avg. speed - </span><span style='color: #f7f13b'>35.64km/h</span>!<br><span>Congratulations!</span></center>",
                      "<b>April 2021</b>: <b>130.83</b> km, <b>03:44:48</b> hours, <b>1956.7</b> calories")}
    return newDataParams[key]
    
class TestPersonalBests:
    
    @pytest.fixture
    def setup(self, qtbot):
        # make CycleData object with known data
        dates = [f"2021-04-{i:02}" for i in range(26, 31)]
        dates += [f"2021-05-{i:02}" for i in range(1, 6)] 
        dct = {'Date':dates,
               'Time':["00:53:27", "00:43:04", "00:42:40", "00:43:09", "00:42:28",
                       "00:43:19", "00:42:21", "00:43:04", "00:42:11", "00:43:25"],
               'Distance (km)':[30.1, 25.14, 25.08, 25.41, 25.1, 25.08, 25.13, 
                                25.21, 25.08, 25.12],
               'Gear':[6]*10}
        dct['Calories'] = [d*14.956 for d in dct['Distance (km)']]
        
        self.parent = MockParent(dct=dct)
        self.pb = PersonalBests(self.parent)
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
        
    def test_new_data_different_column(self, setup, qtbot, monkeypatch):
        # test dialog message when table is sorted by Time
        new = {'Date':[parseDate("7 April 2021", pd_timestamp=True)], 
               'Time':[parseDuration("01:05:03")], 
               'Distance (km)':[25.08], 'Calories':[375.1], 'Gear':[6]}
        
        self.pb.bestSessions.horizontalHeader().sectionClicked.emit(1)
        qtbot.wait(10)
        
        # don't need dialog to pop up
        monkeypatch.setattr(NewPBDialog, "exec_", lambda *args: QDialog.Accepted)
        with qtbot.waitSignal(self.parent.data.dataChanged):
            self.parent.data.append(new)
            
        expected = "<center><span>New #1 time - </span><span style='color: #f7f13b'>01:05:03</span>!<br><span>Congratulations!</span></center>"
        assert self.pb.newPBdialog.label.text() == expected   
        
    def test_tied_data(self, setup, qtbot, monkeypatch):
        new = {'Date':[parseDate("7 May 2021", pd_timestamp=True)], 
               'Time':[parseDuration("00:42:11")], 
               'Distance (km)':[25.08], 'Calories':[375.1], 'Gear':[6]}
        
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
        
    def test_sort_column(self, setup, qtbot):
        # dict of sortable columns and list of expected dates
        columns = {'Time':['26 Apr 2021', '05 May 2021', '01 May 2021', '29 Apr 2021', '03 May 2021'], 
                   'Distance (km)':['26 Apr 2021', '29 Apr 2021', '03 May 2021', '27 Apr 2021', '02 May 2021'], 
                   'Avg. speed\n(km/h)':['04 May 2021', '02 May 2021', '30 Apr 2021', '29 Apr 2021', '28 Apr 2021'], 
                   'Calories':['26 Apr 2021', '29 Apr 2021', '03 May 2021', '27 Apr 2021', '02 May 2021']}
        
        for column, expected in columns.items():
            idx = self.pb.bestSessions.headerLabels.index(column)
            
            self.pb.bestSessions.horizontalHeader().sectionClicked.emit(idx)
            qtbot.wait(10)
            items = [self.pb.bestSessions.item(idx, 0).text() for idx in range(self.pb.bestSessions.rowCount())]
            assert items == expected
            
    def test_get_best_sessions(self, setup, qtbot):
        pb = self.pb.bestSessions._getBestSessions(n=2, key="Distance (km)", order='ascending')
        expected = [{'Date':"04 May 2021",
                     'Time':"00:42:11",
                     'Distance (km)':"25.08",
                     'Gear':"6",
                     'Calories':"375.1"},
                    {'Date':"01 May 2021",
                     'Time':"00:43:19",
                     'Distance (km)':"25.08",
                     'Gear':"6",
                     'Calories':"375.1"}]
        for n, pb_data in enumerate(pb):
            for key, value in expected[n].items():
                assert pb_data[key] == value
                
        with pytest.raises(ValueError):
            self.pb.bestSessions._getBestSessions(order='acsending')
        