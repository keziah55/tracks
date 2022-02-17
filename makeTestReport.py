#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to create html report from pytest results for both PyQt5 and PySide2.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
import os.path
import re
import pkg_resources
import argparse

class ReportWriter:
    """ Object to summarise pytest results in an html document.
    
        Parameters
        ----------
        results : str
            Directory containing results
        out : str
            Path to write html file to
        css : str
            Location of css file
        ts : str, optional
            Timestamp of beginning of tests, as string in ISO format.
            If not supplied, current time will be used.
        qt : list, optional
            List of Qt APIs. If not provided, this defaults to ["PyQt5", "PySide2"]
    """
    
    fmt = "%d %b %Y, %H:%M:%S"
        
    def __init__(self, results=None, out=None, css=None, ts=None, qt=None):
        self.resultsDir = results
        self.out = out
        self.cssFile = css
        ts = float(ts) if ts is not None else ts
        self.ts = self._getTimestamp(ts)
        self.duration = self._getDuration(ts)
        self.qtApis = qt if qt is not None else ["PyQt5", "PySide2"]
        self.qtApisLower = [s.lower() for s in self.qtApis]
        
    @classmethod
    def _getTimestamp(cls, ts):
        """ Return formatted timestamp string, either from current time (ms) or given time. """
        if ts is None:
            ts = datetime.now()
        else:
            ts = datetime.fromtimestamp(ts/1e6)
        ts = ts.strftime(cls.fmt)
        return ts
    
    @classmethod 
    def _getDuration(cls, ts):
        if ts is None:
            return None
        td = datetime.now() - datetime.fromtimestamp(ts/1e6)
        mins = td.seconds // 60
        secs = td.seconds % 60
        s = f"{secs}s"
        if mins > 0:
            s = f"{mins}m {s}"
        return s
        
    
    @staticmethod
    def _getTestCaseStatus(testcase):
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
    
    @staticmethod
    def _getDependencyVersions():
        """ Get names and version numbers of installed packages. """
        return {p.project_name: p.version for p in pkg_resources.working_set}
    
    @staticmethod
    def _escapeHtml(html):
        """ Replace "<" or ">" in html string with "&lt;" and "&gt;" """
        html = re.sub(r"<", "&lt;", html)
        html = re.sub(r">", "&gt;", html)
        return html
        
    @staticmethod
    def _makeToc(lst, depth=2):
        """ From list of html tags, put headers up to `depth` into a table of contents.
        
            Return a list of strings.
        """
    
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
        
    @classmethod
    def _makeTracebackMessage(cls, name, lst):
        """ From list of (qtApi, testcase) pairs, and child `name`, make summary html. """
        html = []
        for qtApi, testcase in lst:
            testName = f"{testcase.attrib['classname']}.{testcase.attrib['name']}"
            element = testcase.find(name)
            message = cls._escapeHtml(element.attrib['message'])
            traceback = cls._escapeHtml(element.text)
            html += [f'<h3 id="{qtApi}-{testName}">{testName}; {qtApi}</h3>', "<h4>Message:</h4>", 
                     f"<span class=traceback>{message}</span>", 
                     "<h4>Traceback:</h4>", 
                     f"<span class=traceback>{traceback}</span>"]
        return html
    
    @classmethod 
    def _makeMessage(cls, name, lst):
        html = []
        for qtApi, testcase in lst:
            testName = f"{testcase.attrib['classname']}.{testcase.attrib['name']}"
            element = testcase.find(name)
            message = cls. _escapeHtml(element.attrib['message'])
            html += [f'<h3 id="{qtApi}-{testName}">{testName}; {qtApi}</h3>', "<h4>Message:</h4>", 
                     f"<span class=traceback>{message}</span>"]
        return html
    
    def _getTestSuites(self):
        resultsFiles = [os.path.join(self.resultsDir, f"{api}-results.xml") for api in self.qtApisLower]
        resultsFiles = [file for file in resultsFiles if os.path.exists(file)]
        trees = [ET.parse(file) for file in resultsFiles]
        roots = [tree.getroot() for tree in trees]
        testsuites = [root.findall("testsuite")[0] for root in roots]
        return testsuites
    
    def _makeHtmlHeader(self):
        html= ["<!DOCTYPE html>", "<html>", "<head>", 
               f'<link rel="stylesheet" href="{self.cssFile}">', "</head>"]
        return html
    
    def _makeSummaryTable(self):
        """ Make html table summarising test results and return as list of strings. """
        html = []
        html = ['<h2 id="test-results">Test results</h2>', "<table class=summaryTable>", "<tr>"]
        tableHeader = ["Qt API", "Tests", "Passed", "Skipped", "Failed", "Errors", "Time"]
        html += [f"<th>{header}</th>" for header in tableHeader]
        for n, testsuite in enumerate(self.testsuites):
            total = int(testsuite.attrib['tests'])
            errors = int(testsuite.attrib['errors'])
            failures = int(testsuite.attrib['failures'])
            skipped = int(testsuite.attrib['skipped'])
            passed = total - errors - failures - skipped
            time = testsuite.attrib['time']
            
            tableRow = [self.qtApis[n], total, passed, skipped, failures, errors, time]
            tableRow = [f"<td>{item}</td>" for item in tableRow]
            html += ["<tr>"] + tableRow + ["</tr>"]
        html += ["</table>"]
        return html
    
    
    def _makeDependencyTable(self):
        """ Make html table of dependency versions and return as list of strings. """
        html = ['<h2 id="dependencies">Dependencies</h2>', "<table class=dependencyTable>"]
        deps = self._getDependencyVersions()
        for key, value in sorted(deps.items(), key=lambda item: item[0].lower()):
            html += ["<tr>", f"<td>{key}</td>", f"<td>{value}</td>", "</tr>"]
        html += ["</table>"] 
        return html
    
    
    def _makeBreakdownTable(self):
        """ Make html table of test results and return as list of strings. """
        html = ['<h1 id="breakdown">Breakdown</h1>', "<table class=breakdownTable>"]
        tableHeader = ["Test"] + self.qtApis
        html += [f"<th>{header}</th>" for header in tableHeader]
        
        self.notPassed = {"error":[], "failed":[], "skipped":[]}
        
        for testcase in self.testsuites[0].findall("testcase"):
            
            classname = testcase.attrib['classname']
            name = testcase.attrib['name']
            
            # find this test in the other testsuite
            other = self.testsuites[1].findall(f"*[@classname='{classname}'][@name='{name}']")[0]
            
            status0 = self._getTestCaseStatus(testcase)
            status1 = self._getTestCaseStatus(other)
            
            data = ["", ""]
            for n, status, tc in [(0, status0, testcase), (1, status1, other)]:
                if status != "passed":
                    self.notPassed[status].append((self.qtApis[n], tc))
                    href = f"{self.qtApis[n]}-{classname}.{name}"
                    data[n] = f"<a href=#{href}>{tc.attrib['time']}s</a>"
                else:
                    data[n] = f"{tc.attrib['time']}s"
                    
            html += ["<tr>", 
                     f"<td class=testName>{classname}.{name}</td>", 
                     f"<td class={status0}>{data[0]}</td>", 
                     f"<td class={status1}>{data[1]}</td>"
                     "</tr>"]
            
        html += ["</table>"]
        
        return html
    
    def _makeNotPassedSection(self):
        """ Make sections detailing errors, failures and skipped tests. 
        
            Return list of html strings.
        """
        html = []
        for name, lst in self.notPassed.items():
            if len(lst) > 0:
                 html += [f'<h1 id="{name}Tests">{name.capitalize()} ({len(lst)})</h1>']
                 if name == "skipped":
                     html += self._makeMessage(name, lst)
                 else:
                     if name == "failed":
                         name = "failure"
                     html += self._makeTracebackMessage(name, lst)
        return html
    
    def _makeWarningsSection(self):
        # get 'warnings summary' section from logs
        summaries = []
        for api in self.qtApisLower:
            file = os.path.join(self.resultsDir, f"{api}-output.log")
            with open(file) as fileobj:
                text = fileobj.read()
            m = re.search(r"=+ warnings summary =+\n(?P<summary>.*)\n-- Docs", 
                          text, flags=re.DOTALL)
            if m is not None:
                summaries.append(m.group('summary'))
        # ideally, they're both the same, but not necessarily
        # e.g. if a test fails with one api, it might not raise the warning
        summaries = set(summaries)
        
        # make list of dictionaries, collating warnings strings with the list of files
        # for each warning summary
        warnInfo = []
        for summary in summaries:
            files = []
            msg = []
            prevIndent = True
            for line in summary.split("\n"):
                if not line:
                    continue
                if re.match(r"\s", line) is None:
                    if prevIndent:
                        files.append([])
                    files[-1].append(line)
                    prevIndent = False
                else:
                    if not prevIndent:
                        msg.append("")
                    msg[-1] += line + "\n"
                    prevIndent = True        
            warnInfo.append(dict(zip(msg, files)))
        
        # combine file lists that correspond to the same warning
        mainWarn, *otherWarn = warnInfo
        for msg, files in mainWarn.items():
            for other in otherWarn:
                if msg in other:
                    mainWarn[msg] += other[msg]
                    
        # make html list of file and warning message
        html = []
        num = 0
        for msg, files in mainWarn.items():
            html += ["<ul>"]
            f = sorted(set(files))
            num += len(f)
            for file in f:
                html += [f"<li>{file}</li>"]
            html += ["</ul>", f"<span class=traceback>{msg}</span>"]
            
        html.insert(0, f'<h1 id="warnings">Warnings ({num})</h1>')
            
        return html
            
    def makeReport(self):
        """ Return string of html detailing the test results. """
        
        self.testsuites = self._getTestSuites()
    
        # make html header and begin body
        html = self._makeHtmlHeader()
        html += ["<body>", 
                 '<h1 id="summary">Summary</h1>', 
                 f"<p>Tests started at {self.ts}"]
        if self.duration is not None:
            html += [f"; duration: {self.duration}"]
        html += ["</p>"]
        
        # summarise test results
        html += self._makeSummaryTable()
            
        # list dependencies and versions
        html += self._makeDependencyTable()
            
        # test result breakdown
        html += self._makeBreakdownTable()
        
        # list errors, failures and skipped tests
        html += self._makeNotPassedSection()
        
        html += self._makeWarningsSection()
        
        # make table of contents
        toc = self._makeToc(html)
        # insert toc at beginning of body
        idx = html.index("<body>")
        html = html[:idx+1] + toc + ['<div class="main">'] + html[idx+1:] + ["</div>", "</body>", "</html>"]
        
        html = "\n".join(html)
        
        return html
    
    def writeReport(self):
        """ Get html and write to file. """
        html = self.makeReport()
        with open(self.out, "w") as fileobj:
            fileobj.write(html)
    
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Write html report of pytest results.')
    parser.add_argument('--results', default='./results',
                        help='directory to read results. Default is "./results"')
    parser.add_argument('--out', default='./report.html',
                        help='path to write output html to. Default is "./report.html"')
    parser.add_argument('--css', default='./report-styles.css',
                        help='location of css file. Default is "./report-styles.css"')
    parser.add_argument('--ts', default=None,
                        help='Timestamp of beginning of test execution. If not provided, current date and time will be used')
    
    args = parser.parse_args()
    
    writer = ReportWriter(args.results, args.out, args.css, args.ts)
    writer.writeReport()
    