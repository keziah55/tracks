#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 16 19:21:18 2022

@author: keziah
"""

import xml.etree.ElementTree as ET
import os.path
from datetime import datetime

def getTestcaseStatus(testcase):
    if testcase.find("skipped") is not None:
        status = "skipped"
    elif testcase.find("failure") is not None:
        status = "failed"
    elif testcase.find("error") is not None:
        status = "failed"
    else:
        status = "passed"
    return status

ts = None
isoFmt = "%Y-%m-%dT%H:%M:%S.%f"
fmt = "%d %b %Y, %H:%M:%S.%f"

html = ["<html>", "<body>"]
html += ["<style>", 
         ".failed { background-color:#c92626; }", 
         ".error { background-color:#c92626; }", 
         ".skipped { background-color:#c97a26; }", 
         ".passed { background-color:#26c954; }", 
         "</style>"]

resultsDir = "results"
qtApis = ["PyQt5", "PySide2"]
qtApisLower = [s.lower() for s in qtApis]

resultsFiles = [os.path.join(resultsDir, f"{api}-results.xml") for api in qtApisLower]
resultsFiles = [file for file in resultsFiles if os.path.exists(file)]
trees = [ET.parse(file) for file in resultsFiles]
roots = [tree.getroot() for tree in trees]
testsuites = [root.findall("testsuite")[0] for root in roots]

## summary
if ts is None:
    ts = datetime.now()
else:
    ts = datetime.strptime(ts, isoFmt)
ts = ts.strftime(fmt)

html += ["<h1>Summary</h1>", f"<p>{ts}</p>"]

html += ["<table>", "<tr>"]
tableHeader = ["Qt API", "Tests", "Passed", "Skipped", "Failed", "Errors", "Time"]
html += [f"<th>{header}</th>" for header in tableHeader]
for n, testsuite in enumerate(testsuites):
    total = int(testsuite.attrib['tests'])
    errors = int(testsuite.attrib['errors'])
    failures = int(testsuite.attrib['failures'])
    skipped = int(testsuite.attrib['skipped'])
    passed = total - errors - failures - skipped
    time = testsuite.attrib['time']
    
    tableRow = [qtApis[n], total, passed, skipped, failures, errors, time]
    tableRow = [f"<td>{item}</td>" for item in tableRow]
    html += ["<tr>"] + tableRow + ["</tr>"]
html += ["</table>"]    
    
    
## test result breakdown
html += ["<h1>Breakdown</h1>", "<table class=breakdown>"]
tableHeader = ["Test"] + qtApis
html += [f"<th>{header}</th>" for header in tableHeader]

for testcase in testsuites[0].findall("testcase"):
    
    classname = testcase.attrib['classname']
    name = testcase.attrib['name']
    time = testcase.attrib['time']
    
    other = testsuites[1].findall(f"*[@classname='{classname}'][@name='{name}']")[0]
    
    status0 = getTestcaseStatus(testcase)
    status1 = getTestcaseStatus(other)
    
    html += ["<tr>", 
             f"<td>{classname}.{name}</td>", 
             f"<td class={status0}> {time}</td>", 
             f"<td class={status1}> {other.attrib['time']}</td>"
             "</tr>"]
    
html += ["</table>"]

    
html += ["<body>", "<html>"]
html = "\n".join(html)
with open("summary.html", "w") as fileobj:
    fileobj.write(html)
    