#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Cycle Tracks.
"""
import sys
from PyQt5.QtWidgets import QApplication
from cycleTracks.cycletracks import CycleTracks

app = QApplication(sys.argv)
window = CycleTracks()
window.show()
sys.exit(app.exec_())
