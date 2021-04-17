#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Cycle Tracks.
"""
import sys, os
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from cycleTracks.cycletracks import CycleTracks

if __name__ == '__main__':

    QApplication.setApplicationName("Cycle Tracks")
    QApplication.setOrganizationName("kzm")
    
    app = QApplication(sys.argv)
    
    # splashFile = os.path.join("images", "splash.png")
    # pixmap = QPixmap(splashFile)
    # splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
    # splash.show()
    
    app.processEvents()
       
    window = CycleTracks()
    window.show()
    # splash.finish(window)
    
    # window.raise_()
    
    sys.exit(app.exec_())
