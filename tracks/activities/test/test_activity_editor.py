from .. import ActivityEditor
from qtpy.QtWidgets import QApplication
import sys


def test_editor(qtbot, activity_json_path):
    widget = ActivityEditor()
    qtbot.addWidget(widget)

    widget.show()

    qtbot.wait(3000)
