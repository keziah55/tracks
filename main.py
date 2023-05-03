#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Tracks.
"""
import sys
from qtpy.QtWidgets import QApplication
from tracks.tracks import Tracks

if __name__ == '__main__':

    QApplication.setApplicationName("Tracks")
    QApplication.setOrganizationName("Tracks")
    
    app = QApplication(sys.argv)
    
    window = Tracks()
    window.show()
    
    sys.exit(app.exec_())
