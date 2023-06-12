#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to create html report from pytest results for both PyQt5 and PySide2.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import re
import pkg_resources
import argparse
import platform
import subprocess
import numpy as np

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
            List of Qt APIs. If not provided, this defaults to ["PyQt5", "PySide2", "PyQt6", "PySide6"]
    """
    
    fmt = "%a %d %b %Y, %H:%M:%S"
        
    def __init__(self, results=None, out=None, ts=None, qt=None):
        self.resultsDir = Path(results)
        self.out = Path(out)
        self.cssFile = Path(__file__).parent.joinpath("report-styles.css")
        ts = float(ts) if ts is not None else ts
        self.ts = self._getTimestamp(ts)
        self.duration = self._getDuration(ts)
        
        qtLookup = {"pyqt5":"PyQt5", "pyside2":"PySide2", "pyqt6":"PyQt6", "pyside6":"PySide6"}
        self.qtApis = [qtLookup.get(q, q) for q in qt] if qt is not None else ["PyQt5", "PySide2", "PyQt6", "PySide6"]
        self.qtApisLower = [s.lower() for s in self.qtApis]
        
    @staticmethod
    def _getOSrelease():
        """ Return contents of /etc/os-release as dict. 
        
            This method can be removed once we're using python 3.10, as
            platform.freedesktop_os_release() will do this.
        """
        dct = {}
        with open("/etc/os-release") as fileobj:
            while True:
                line = fileobj.readline()
                if not line:
                    break
                else:
                    m = re.match(r'(?P<key>\w+)=(?P<value>.+)', line)
                    dct[m.group('key')] =  m.group('value').strip('"')
        return dct
        
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
        """ Return time between now and `ts`, formatted as string of minutes and seconds. """
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
        """ Return testsuite elements for each Qt API. """
        testsuites = {}
        for api in self.qtApisLower:
            file = self.resultsDir.joinpath(f"{api}-results.xml")
            if file.exists():
                tree = ET.parse(file)
                testsuites[api] = tree.getroot().findall("testsuite")[0]
        return testsuites
    
    def _getCoverage(self):
        coverage = {}
        for api in self.qtApisLower:
            file = self.resultsDir.joinpath(f"{api}-coverage.xml")
            coverage[api] = {}
            if file.exists():
                tree = ET.parse(file)
                coverage[api]['summary'] = tree.getroot().attrib
                coverage[api]['packages'] = tree.getroot().findall("packages")[0]
        return coverage
    
    def _makeHtmlHeader(self):
        html = ["<!DOCTYPE html>", "<html>", "<head>"]
        with open(self.cssFile) as fileobj:
            text = fileobj.read()
        html += ["<style>", text, "</style>", "</head>"]
        return html
    
    def _makeSummaryInfo(self):
        """ Make section summarising Python and system versions; timestamp and duration. """
        try:
            # from python 3.10
            osInfo = platform.freedesktop_os_release()
        except AttributeError:
            osInfo = self._getOSrelease()
        html = ['<h1 id="summary">Summary</h1>', 
                f"<p>Python {platform.python_version()} on {osInfo['PRETTY_NAME']}, {platform.release()}</p>"]
        
        s = f"<p>Tests started at {self.ts}"
        if self.duration is not None:
            s += f"; Duration: {self.duration}"
        html += [ s, "</p>"]
        
        html += ['<h2 id="gitlog">Git log</h2>']
        p = subprocess.run(["git", "log", "-1"], capture_output=True)
        lines = [item for item in p.stdout.decode().split("\n") if item]
        html += [f"<p>{line}</p>" for line in lines]
        
        return html
    
    def _makeSummaryTable(self):
        """ Make html table summarising test results and return as list of strings. """
        html = []
        html = ['<h2 id="test-results">Test results</h2>', "<table class=summaryTable>", "<tr>"]
        tableHeader = ["Qt API", "Tests", "Passed", "Skipped", "Failed", "Errors", "Time", "Coverage"]
        html += [f"<th>{header}</th>" for header in tableHeader]
        for qtApi, testsuite in self.testsuites.items():
            total = int(testsuite.attrib['tests'])
            errors = int(testsuite.attrib['errors'])
            failures = int(testsuite.attrib['failures'])
            skipped = int(testsuite.attrib['skipped'])
            passed = total - errors - failures - skipped
            time = testsuite.attrib['time']
            
            cov = float(self.coverage[qtApi]['summary']['line-rate'])
            cov = f"{cov*100:0.2f}%"
            
            tableRow = [qtApi, total, passed, skipped, failures, errors, time, cov]
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
        """ Make html table of test results and return as list of strings. 
        
            Also populates `notPassed` dict.
        """
        html = ['<h1 id="breakdown">Breakdown</h1>', "<table class=breakdownTable>"]
        tableHeader = ["Test"] + self.qtApis
        html += [f"<th>{header}</th>" for header in tableHeader]
        
        self.notPassed = {"error":[], "failed":[], "skipped":[]}
        
        qt0, *qtApis = self.qtApis
        
        for testcase in self.testsuites[qt0.lower()].findall("testcase"):
            
            classname = testcase.attrib['classname']
            name = testcase.attrib['name']
            
            testcases = {qt0:testcase}
            
            # find this test in the other testsuite(s)
            for qt in qtApis:
                testcases[qt] = self.testsuites[qt.lower()].findall(f"*[@classname='{classname}'][@name='{name}']")[0]
            
            # make this row of html
            html += ["<tr>", f"<td class=testName>{classname}.{name}</td>"]
            for qt, tc in testcases.items():
                status = self._getTestCaseStatus(tc)
                if status != "passed":
                    self.notPassed[status].append((qt, tc))
                    href = f"{qt}-{classname}.{name}"
                    td = f"<a href=#{href}>{tc.attrib['time']}s</a>"
                else:
                    td = f"{tc.attrib['time']}s"
                html += [f"<td class={status}>{td}</td>"]
            html += ["</tr>"]
            
        html += ["</table>"]
        
        return html
    
    def _makeNotPassedSection(self):
        """ Make sections detailing errors, failures and skipped tests. 
        
            Return list of html strings.
        """
        if not hasattr(self, "notPassed"):
            msg = "'_makeBreakdownTable' must be called before '_makeNotPassedSection'"
            raise RuntimeError(msg)
            
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
        """ Read warnings summaries from test logs and return list of html strings. """
        html = []
                
        warnInfo = {}

        for api in self.qtApisLower:
            file = self.resultsDir.joinpath(f"{api}-output.log")
            
            files = [] # list of file lists
            msg = [] # list of strings
            prevIndent = True # previous line started with whitespace
            inWarningsSummary = False # current line is within warnings summary
            
            with open(file) as fileobj:
                while True:
                    line = fileobj.readline()
                    if not line:
                        # end of file
                        break
                    if re.match(r"=+ warnings summary", line):
                        # entering warnings summary
                        inWarningsSummary = True
                        continue
                    elif re.match(r"-- Docs", line):
                        # end of warnings summary
                        break
                    
                    if inWarningsSummary:
                        # get files and warning messages
                        line = line.strip("\n")
                        if not line:
                            continue
                        
                        if re.match(r"\s", line) is None:
                            # line doesn't start with whitespace, so is a file name
                            if prevIndent:
                                # if previous line was a warning message, not a file name
                                files.append([])
                            # append to last file list
                            files[-1].append(line)
                            prevIndent = False
                        else:
                            if not prevIndent:
                                # if previous line was a file name, not part of a message
                                msg.append("")
                            # append to last message
                            msg[-1] += line + "\n"
                            prevIndent = True   
            if not warnInfo:
                # if this is the first file (with warnings), make dict of message:file list pairs
                warnInfo = dict(zip(msg, files))
            else:
                # if dict already exists
                for n, msgStr in enumerate(msg):
                    if msgStr in warnInfo:
                        # if message alerady in dict append to its file list
                        warnInfo[msgStr] += files[n]
                    else:
                        # otherwise add new entry
                        warnInfo[msgStr] = files[n]
        if warnInfo:
            # make html list of file and warning message
            num = 0
            for msg, files in warnInfo.items():
                html += ["<ul>"]
                f = sorted(set(files)) # remove repeated file names and sort
                num += len(f)
                for file in f:
                    html += [f"<li>{file}</li>"]
                html += ["</ul>", f"<span class=traceback>{msg}</span>"]
                
            html.insert(0, f'<h1 id="warnings">Warnings ({num})</h1>')
            
        return html
    
    def _makeCoverageTable(self):
        """ Make html table of file test coverage and return as list of strings. 
        
            Also populates `missed` dict.
        """
        html = ['<h1 id="coverage">Coverage</h1>', "<table class=breakdownTable>"]
        tableHeader = ["File"] + self.qtApis
        html += [f"<th>{header}</th>" for header in tableHeader]

        self.missed = {}
        
        qt0, *qtApis = self.qtApisLower
        
        for package in self.coverage[qt0]['packages'].findall("package"):
            name = package.attrib['name']
            for file in package.findall('classes')[0].findall('class'): # only one 'classes' group per package
                fname = file.attrib['filename']
                cov = float(file.attrib['line-rate'])
                miss = self._getMissedLines(file) 
                results = [cov]
                if cov < 1:
                    self.missed[fname] = {qt0:miss}
                
                # find this file in the other coverage report(s)
                for qt in qtApis:
                    classes = self.coverage[qt]['packages'].findall(f"*[@name='{name}']")[0].findall('classes')[0] # only one 'classes' group per package
                    file = classes.findall(f"*[@filename='{fname}']")[0]
                    cov = float(file.attrib['line-rate'])
                    miss = self._getMissedLines(file)
                    results.append(cov)
                    if cov < 1:
                        if fname not in self.missed:
                            self.missed[fname] = {}
                        self.missed[fname][qt] = miss
                
                # make this row of html
                html += ["<tr>", f"<td class=fileName>{fname}</td>"]
                for cov in results:
                    td = f"{cov*100:0.0f}%"
                    if cov < 1:
                        href = f"{qt}-missed-{fname}"
                        td = f"<a href=#{href}>{td}</a>"
                    html += [f"<td>{td}</td>"]
                html += ["</tr>"]
                
        html += ["</table>"]
        
        return html
    
    
    def _getMissedLines(self, classGroup):
        """ Return string of missed lines in this <class> """
        lines = classGroup.findall('lines')[0].findall('line')
        miss = [int(line.attrib['number']) for line in lines if line.attrib['hits']=='0']
        if not miss:
            return ""
        miss = np.array(miss)
        consecutive = np.split(miss, np.where(np.diff(miss) != 1)[0]+1)
        lineNums = []
        for c in consecutive:
            if len(c) > 1:
                s = f"{c[0]}-{c[-1]}"
            else:
                s = str(c[0])
            lineNums.append(s)
        return ", ".join(lineNums)
            
    
    def _makeMissedLinesTable(self):
        """ Make html table of missed lines and return as list of strings """
        
        if not hasattr(self, "missed"):
            msg = "'_makeCoverageTable' must be called before '_makeMissedLinesTable'"
            raise RuntimeError(msg)
        
        html = ['<h2 id="missed">Missed lines</h2>', "<table class=breakdownTable>"]
        tableHeader = ["File"] + self.qtApis
        html += [f"<th>{header}</th>" for header in tableHeader]
        
        for fname, dct in self.missed.items():
            html += [f'<tr id="missed-{fname}">', f"<td class=fileName>{fname}</td>"]
            for qt in self.qtApisLower:
                miss = dct.get(qt, "")
                html += [f'<td id="{qt}-missed-{fname}">{miss}</td>']
            html += ["</tr>"]
            
        html += ["</table>"]
        
        return html
                
    
    def makeReport(self):
        """ Return string of html detailing the test results. """
        
        # read xml files
        self.testsuites = self._getTestSuites()
        self.coverage = self._getCoverage()
        
        ## get html contents before writing header, so toc can be included at beginning
        main = ['<div class="main">']
        # write python and system version; get timestamp and duration
        main += self._makeSummaryInfo()
        # summarise test results
        main += self._makeSummaryTable()
        # list dependencies and versions
        main += self._makeDependencyTable()
        # test result breakdown
        main += self._makeBreakdownTable()
        # list errors, failures and skipped tests
        main += self._makeNotPassedSection()
        main += self._makeWarningsSection()
        # coverage breakdown
        main += self._makeCoverageTable()
        # coverage breakdown
        main += self._makeMissedLinesTable()
        # end main
        main += ["</div>"]
        
        # make table of contents
        toc = self._makeToc(main)
        
        # make html header, include stylesheet inline
        header = self._makeHtmlHeader()
        
        # make html string
        html = header + ["<body>"] + toc + main + ["</body>", "</html>"]
        html = "\n".join(html)
        
        return html
    
    def writeReport(self):
        """ Get html and write to file. """
        html = self.makeReport()
        with open(self.out, "w") as fileobj:
            fileobj.write(html)
        print()
        if self.duration is not None:
            print(f"Tests completed in {self.duration}")
        print(f"Test report written to {self.out.absolute()}")
    
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Write html report of pytest results.')
    parser.add_argument('--results', default='./results',
                        help='directory to read results. Default is "./results"')
    parser.add_argument('--out', default='./report.html',
                        help='path to write output html to. Default is "./report.html"')
    parser.add_argument('--ts', default=None,
                        help='Timestamp of beginning of test execution. If not provided, current date and time will be used')
    parser.add_argument('--qt', default=None,
                        help='Qt bindings used in tests')
    
    args = parser.parse_args()
    qt = args.qt.split(',') if args.qt is not None else None
    writer = ReportWriter(args.results, args.out, args.ts, qt)
    writer.writeReport()