#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Tracks.
"""
import sys
from pathlib import Path
from qtpy.QtWidgets import QApplication
from tracks.tracks import Tracks

if __name__ == '__main__':

    QApplication.setApplicationName("Tracks")
    QApplication.setOrganizationName("Tracks")
    
    app = QApplication(sys.argv)
    style_sheet = Path(__file__).parent.joinpath("tracks", "ui", "style.qss")
    if style_sheet.exists():
        with open(style_sheet) as fileobj:
            style = fileobj.read()
        app.setStyleSheet(style)
        
    # set desktop file, if it exists
    # this allows the correct icon to be shown on wayland
    p = Path.home().joinpath(".local", "share", "applications", "tracks.desktop")
    if p.exists():
        app.setDesktopFileName(str(p))
    
    window = Tracks()
    window.show()
    
    sys.exit(app.exec_())
