#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 16 19:21:18 2022

@author: keziah
"""

import xml.etree.ElementTree as ET
import os.path
from datetime import datetime
import re
import pkg_resources

def getTestCaseStatus(testcase):
    """ Check if a `testcase` element has a "skipped", "failure" or "error" child. """
    if testcase.find("skipped") is not None:
        status = "skipped"
    elif testcase.find("failure") is not None:
        status = "failed"
    elif testcase.find("error") is not None:
        status = "error"
    else:
        status = "passed"
    return status

def getDependencyVersions():
    """ Get names and version numbers of installed packages. """
    return {p.project_name: p.version for p in pkg_resources.working_set}

def escapeHtml(html):
    """ Replace "<" or ">" in html string with "&lt;" and "&gt;" """
    html = re.sub(r"<", "&lt;", html)
    html = re.sub(r">", "&gt;", html)
    return html
    
def makeToc(lst, depth=2):
    """ From list of html tags, find headers up to `depth`. """

    toc = ['<div class="sidenav">', '<ul>']
    level = 1
    for tag in lst:
        m = re.match(r"<h(?P<n>\d+)", tag)
        if m is not None and int(m.group('n')) <= depth:
            m = re.match(r'<h(?P<n>\d+)( id="(?P<id>\S+)")?>(?P<name>.*)</h\d+>', tag)
            data = m.group('name')
            if m.group('id') is not None:
                href = f"#{m.group('id')}"
                data = f'<a href="{href}">{data}</a>'
            data = f"<li>{data}</li>"
            n = int(m.group('n'))
            if n > level:
                data = f'<ul>{data}'
                level = n
            elif n < level:
                data = f"</ul>{data}"
                level = n
            toc += [data]
    toc += ['</ul>', "</div>"]
    return  toc
    

ts = None
isoFmt = "%Y-%m-%dT%H:%M:%S.%f"
fmt = "%d %b %Y, %H:%M:%S.%f"

html = ["<!DOCTYPE html>", "<html>", "<head>", '<link rel="stylesheet" href="report-styles.css">' "</head>", "<body>"]

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

html += ['<h1 id="summary">Summary</h1>', f"<p>{ts}</p>"]

## summarise test results
html += ['<h2 id="test-results">Test results</h2>', "<table class=summaryTable>", "<tr>"]
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
    
## list dependencies and versions
html += ['<h2 id="dependencies">Dependencies</h2>', "<table class=dependencyTable>"]
deps = getDependencyVersions()
for key, value in sorted(deps.items(), key=lambda item: item[0].lower()):
    html += ["<tr>", f"<td>{key}</td>", f"<td>{value}</td>", "</tr>"]
html += ["</table>"]  
    
## test result breakdown
html += ['<h1 id="breakdown">Breakdown</h1>', "<table class=breakdownTable>"]
tableHeader = ["Test"] + qtApis
html += [f"<th>{header}</th>" for header in tableHeader]

notPassed = {"error":[], "failed":[], "skipped":[]}

for testcase in testsuites[0].findall("testcase"):
    
    classname = testcase.attrib['classname']
    name = testcase.attrib['name']
    time = testcase.attrib['time']
    
    # find this test in the other testsuite
    other = testsuites[1].findall(f"*[@classname='{classname}'][@name='{name}']")[0]
    
    status0 = getTestCaseStatus(testcase)
    status1 = getTestCaseStatus(other)
    
    data = ["", ""]
    for n, status, tc in [(0, status0, testcase), (1, status1, other)]:
        if status != "passed":
            notPassed[status].append((qtApis[n], tc))
            href = f"{qtApis[n]}-{classname}.{name}"
            data[n] = f"<a href=#{href}>{tc.attrib['time']}s</a>"
        else:
            data[n] = f"{tc.attrib['time']}s"
            
    html += ["<tr>", 
             f"<td class=testName>{classname}.{name}</td>", 
             f"<td class={status0}>{data[0]}</td>", 
             f"<td class={status1}>{data[1]}</td>"
             "</tr>"]
    
html += ["</table>"]

if len(notPassed["error"]) > 0:
    html += [f'<h1 id="errorTests">Errors ({len(notPassed["error"])})</h1>']
    # TODO

if len(notPassed["failed"]) > 0:
    html += [f'<h1 id="failedTests">Failed ({len(notPassed["failed"])})</h1>']
    for qtApi, testcase in notPassed["failed"]:
        testName = f"{testcase.attrib['classname']}.{testcase.attrib['name']}"
        element = testcase.find("failure")
        message = escapeHtml(element.attrib['message'])
        traceback = escapeHtml(element.text)
        html += [f'<h3 id="{qtApi}-{testName}">{testName}; {qtApi}</h3>', "<h4>Message:</h4>", 
                 f"<span class=traceback>{message}</span>", 
                 "<h4>Traceback:</h4>", 
                 f"<span class=traceback>{traceback}</span>"]

if len(notPassed["skipped"]) > 0:
    html += [f'<h1 id="skippedTests">Skipped ({len(notPassed["skipped"])})</h1>']
    for qtApi, testcase in notPassed["skipped"]:
        testName = f"{testcase.attrib['classname']}.{testcase.attrib['name']}"
        element = testcase.find("skipped")
        message = escapeHtml(element.attrib['message'])
        html += [f'<h3 id="{qtApi}-{testName}">{testName}; {qtApi}</h3>', "<h4>Message:</h4>", 
                 f"<span class=traceback>{message}</span>"]

    
toc = makeToc(html)

idx = html.index("<body>")
html = html[:idx+1] + toc + ['<div class="main">'] + html[idx+1:] + ["</div>", "</body>", "</html>"]

# html += ["</body>", "</html>"]

html = "\n".join(html)
with open("report.html", "w") as fileobj:
    fileobj.write(html)
    