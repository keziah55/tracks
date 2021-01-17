#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QWidget containing QLabels for each data series in the CyclePlotWidget.
"""

from PyQt5.QtWidgets import QLabel, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt

class CyclePlotLabel(QWidget):
    
    def __init__(self, style, fontSize=12):
        
        super().__init__()
        
        self.style = style
        self.fontSize = f"font-size: {fontSize}pt"
        
        self.layout = QHBoxLayout()
        
        self.data = {}
        self.data['date'] = {'string':"{}"}
        self.data['speed'] = {'string':"Avg. speed: {:.3f} km/h"}
        self.data['distance'] = {'string':"Distance: {} km"}
        self.data['calories'] = {'string':"Calories: {}"}
        self.data['time'] = {'string':"Time: {}"}
        
        for key, value in self.data.items():
            widget = QLabel()
            widget.setAlignment(Qt.AlignCenter)
            self.data[key]['widget'] = widget
            self.layout.addWidget(widget)
            
        self.setLayout(self.layout)
            
            
    def setLabels(self, dct):
        # TODO iterate through kwargs, not data
        for key, data in dct.items():
            
            text = self.data[key]['string'].format(data)
            label = self.data[key]['widget']
                
            if key in self.style.keys():
                colour = self.style[key]['colour']
                style = f"'{self.fontSize}; color: {colour}'"
            else:
                style = f"'{self.fontSize}'"
            html = f"<div style={style}>{text}</div>"
            label.setText(html)
