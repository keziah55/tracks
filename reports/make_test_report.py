#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to create html report from pytest results for all Qt bindings.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import re
from importlib.metadata import packages_distributions, version
import argparse
import platform
import subprocess
import numpy as np


class ReportWriter:
    """Object to summarise pytest results in an html document.

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
    """

    fmt = "%a %d %b %Y, %H:%M:%S"

    def __init__(self, results=None, out=None, ts=None):
        self.results_dir = Path(results)
        self.out = Path(out)
        self.css_file = Path(__file__).parent.joinpath("report-styles.css")
        ts = float(ts) if ts is not None else ts
        self.ts = self._get_timestamp(ts)
        self.duration = self._get_duration(ts)

        self._qt_apis = [
            re.match(r"(?P<qt>\w+)-coverage.xml", d.name) for d in self.results_dir.iterdir()
        ]
        self._qt_apis = [m.group("qt") for m in self._qt_apis if m is not None]

        self._not_passed = None
        self._missed = None

    @staticmethod
    def _pretty_qt(qt):
        qt_lookup = {
            "pyqt5": "PyQt5",
            "pyside2": "PySide2",
            "pyqt6": "PyQt6",
            "pyside6": "PySide6",
        }
        s = qt_lookup.get(qt, None)
        if s is None:
            raise KeyError(f"No pretty version of '{qt}'")
        return s

    @classmethod
    def _get_timestamp(cls, ts):
        """Return formatted timestamp string, either from current time (ms) or given time."""
        if ts is None:
            ts = datetime.now()
        else:
            ts = datetime.fromtimestamp(ts / 1e6)
        ts = ts.strftime(cls.fmt)
        return ts

    @classmethod
    def _get_duration(cls, ts):
        """Return time between now and `ts`, formatted as string of minutes and seconds."""
        if ts is None:
            return None
        td = datetime.now() - datetime.fromtimestamp(ts / 1e6)
        mins = td.seconds // 60
        secs = td.seconds % 60
        s = f"{secs}s"
        if mins > 0:
            s = f"{mins}m {s}"
        return s

    @staticmethod
    def _get_test_case_status(testcase):
        """Check if a `testcase` element has a "skipped", "failure" or "error" child."""
        statuses = ["skipped", "failure", "error"]
        for status in statuses:
            if testcase.find(status) is not None:
                return status
        return "passed"
        # if testcase.find("skipped") is not None:
        #     status = "skipped"
        # elif testcase.find("failure") is not None:
        #     status = "failed"
        # elif testcase.find("error") is not None:
        #     status = "error"
        # else:
        #     status = "passed"
        # return status

    @staticmethod
    def _get_dependency_versions():
        """Get names and version numbers of installed packages."""
        all_pkgs = [item for pkg_list in packages_distributions().values() for item in pkg_list]
        pkg_versions = {pkg: version(pkg) for pkg in all_pkgs}
        return pkg_versions

    @staticmethod
    def _escape_html(html):
        """Replace "<" or ">" in html string with "&lt;" and "&gt;" """
        html = re.sub(r"<", "&lt;", html)
        html = re.sub(r">", "&gt;", html)
        return html

    @staticmethod
    def _make_toc(lst, depth=2):
        """
        From list of html tags, put headers up to `depth` into a table of contents.

        Return a list of strings.
        """
        toc = ['<div class="sidenav">', "<ul>"]
        level = 1
        for tag in lst:
            m = re.match(r"<h(?P<n>\d+)", tag)
            if m is not None and int(m.group("n")) <= depth:
                m = re.match(r'<h(?P<n>\d+)( id="(?P<id>\S+)")?>(?P<name>.*)</h\d+>', tag)
                data = m.group("name")
                if m.group("id") is not None:
                    href = f"#{m.group('id')}"
                    data = f'<a href="{href}">{data}</a>'
                data = f"<li>{data}</li>"
                n = int(m.group("n"))
                if n > level:
                    data = f"<ul>{data}"
                    level = n
                elif n < level:
                    data = f"</ul>{data}"
                    level = n
                toc += [data]
        toc += ["</ul>", "</div>"]
        return toc

    @classmethod
    def _make_traceback_message(cls, name, lst):
        """From list of (qt_api, testcase) pairs, and child `name`, make summary html."""
        html = []
        for qt_api, testcase in lst:
            test_name = f"{testcase.attrib['classname']}.{testcase.attrib['name']}"
            element = testcase.find(name)
            message = cls._escape_html(element.attrib["message"])
            traceback = cls._escape_html(element.text)
            html += [
                f'<h3 id="{qt_api}-{test_name}">{test_name}; {qt_api}</h3>',
                "<h4>Message:</h4>",
                f"<span class=traceback>{message}</span>",
                "<h4>Traceback:</h4>",
                f"<span class=traceback>{traceback}</span>",
            ]
        return html

    @classmethod
    def _make_message(cls, name, lst):
        html = []
        for qt_api, testcase in lst:
            test_name = f"{testcase.attrib['classname']}.{testcase.attrib['name']}"
            element = testcase.find(name)
            message = cls._escape_html(element.attrib["message"])
            html += [
                f'<h3 id="{qt_api}-{test_name}">{test_name}; {qt_api}</h3>',
                "<h4>Message:</h4>",
                f"<span class=traceback>{message}</span>",
            ]
        return html

    def _get_test_suites(self):
        """Return testsuite elements for each Qt API."""
        testsuites = {}
        for api in self._qt_apis:
            file = self.results_dir.joinpath(f"{api}-results.xml")
            if file.exists():
                tree = ET.parse(file)
                testsuites[api] = tree.getroot().findall("testsuite")[0]
        return testsuites

    def _get_coverage(self):
        coverage = {}
        for api in self._qt_apis:
            file = self.results_dir.joinpath(f"{api}-coverage.xml")
            coverage[api] = {}
            if file.exists():
                tree = ET.parse(file)
                coverage[api]["summary"] = tree.getroot().attrib
                coverage[api]["packages"] = tree.getroot().findall("packages")[0]
        return coverage

    def _make_html_header(self):
        html = ["<!DOCTYPE html>", "<html>", "<head>"]
        with open(self.css_file) as fileobj:
            text = fileobj.read()
        html += ["<style>", text, "</style>", "</head>"]
        return html

    def _make_summary_info(self):
        """Make section summarising Python and system versions; timestamp and duration."""
        html = [
            '<h1 id="summary">Summary</h1>',
            f"<p>Python {platform.python_version()} on "
            f"{platform.freedesktop_os_release()['PRETTY_NAME']}, {platform.release()}</p>",
        ]

        s = f"<p>Tests started at {self.ts}"
        if self.duration is not None:
            s += f"; Duration: {self.duration}"
        html += [s, "</p>"]

        html += ['<h2 id="gitlog">Git log</h2>']
        p = subprocess.run(["git", "log", "-1"], capture_output=True)
        lines = [item for item in p.stdout.decode().split("\n") if item]
        html += [f"<p>{line}</p>" for line in lines]

        return html

    def _make_summary_table(self):
        """Make html table summarising test results and return as list of strings."""
        html = []
        html = ['<h2 id="test-results">Test results</h2>', "<table class=summaryTable>", "<tr>"]
        table_header = [
            "Qt API",
            "Tests",
            "Passed",
            "Skipped",
            "Failed",
            "Errors",
            "Time",
            "Coverage",
        ]
        html += [f"<th>{header}</th>" for header in table_header]
        for qt_api, testsuite in self.testsuites.items():
            total = int(testsuite.attrib["tests"])
            errors = int(testsuite.attrib["errors"])
            failures = int(testsuite.attrib["failures"])
            skipped = int(testsuite.attrib["skipped"])
            passed = total - errors - failures - skipped
            time = testsuite.attrib["time"]

            cov = float(self.coverage[qt_api]["summary"]["line-rate"])
            cov = f"{cov*100:0.2f}%"

            table_row = [qt_api, total, passed, skipped, failures, errors, time, cov]
            table_row = [f"<td>{item}</td>" for item in table_row]
            html += ["<tr>"] + table_row + ["</tr>"]
        html += ["</table>"]

        return html

    def _make_dependency_table(self):
        """Make html table of dependency versions and return as list of strings."""
        html = ['<h2 id="dependencies">Dependencies</h2>', "<table class=dependencyTable>"]
        deps = self._get_dependency_versions()
        for key, value in sorted(deps.items(), key=lambda item: item[0].lower()):
            html += ["<tr>", f"<td>{key}</td>", f"<td>{value}</td>", "</tr>"]
        html += ["</table>"]
        return html

    def _make_breakdown_table(self):
        """
        Make html table of test results and return as list of strings.

        Also populates `notPassed` dict.
        """
        html = ['<h1 id="breakdown">Breakdown</h1>', "<table class=breakdownTable>"]
        table_header = ["Test"] + [self._pretty_qt(qt) for qt in self._qt_apis]
        html += [f"<th>{header}</th>" for header in table_header]

        self._not_passed = {"error": [], "failed": [], "skipped": []}

        qt0, *qt_apis = self._qt_apis

        for testcase in self.testsuites[qt0].findall("testcase"):

            classname = testcase.attrib["classname"]
            name = testcase.attrib["name"]

            testcases = {qt0: testcase}

            # find this test in the other testsuite(s)
            for qt in qt_apis:
                testcases[qt] = self.testsuites[qt].findall(
                    f"*[@classname='{classname}'][@name='{name}']"
                )[0]

            # make this row of html
            html += ["<tr>", f"<td class=testName>{classname}.{name}</td>"]
            for qt, tc in testcases.items():
                status = self._get_test_case_status(tc)
                if status != "passed":
                    self._not_passed[status].append((qt, tc))
                    href = f"{qt}-{classname}.{name}"
                    td = f"<a href=#{href}>{tc.attrib['time']}s</a>"
                else:
                    td = f"{tc.attrib['time']}s"
                html += [f"<td class={status}>{td}</td>"]
            html += ["</tr>"]

        html += ["</table>"]

        return html

    def _make_not_passed_section(self):
        """
        Make sections detailing errors, failures and skipped tests.

        Return list of html strings.
        """
        if self._not_passed is None:
            msg = "'_make_breakdown_table' must be called before '_make_not_passed_section'"
            raise RuntimeError(msg)

        html = []
        for name, lst in self._not_passed.items():
            if len(lst) > 0:
                html += [f'<h1 id="{name}Tests">{name.capitalize()} ({len(lst)})</h1>']
                if name == "skipped":
                    html += self._make_message(name, lst)
                else:
                    if name == "failed":
                        name = "failure"
                    html += self._make_traceback_message(name, lst)
        return html

    def _make_warnings_section(self):
        """Read warnings summaries from test logs and return list of html strings."""
        html = []

        warnInfo = {}

        for api in self._qt_apis:
            file = self.results_dir.joinpath(f"{api}-output.log")

            files = []  # list of file lists
            msg = []  # list of strings
            prevIndent = True  # previous line started with whitespace
            inWarningsSummary = False  # current line is within warnings summary

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
                f = sorted(set(files))  # remove repeated file names and sort
                num += len(f)
                for file in f:
                    html += [f"<li>{file}</li>"]
                html += ["</ul>", f"<span class=traceback>{msg}</span>"]

            html.insert(0, f'<h1 id="warnings">Warnings ({num})</h1>')

        return html

    def _make_coverage_table(self):
        """
        Make html table of file test coverage and return as list of strings.

        Also populates `missed` dict.
        """
        html = ['<h1 id="coverage">Coverage</h1>', "<table class=breakdownTable>"]
        table_header = ["File"] + [self._pretty_qt(qt) for qt in self._qt_apis]
        html += [f"<th>{header}</th>" for header in table_header]

        self._missed = {}

        qt0, *qt_apis = self._qt_apis

        for package in self.coverage[qt0]["packages"].findall("package"):
            name = package.attrib["name"]
            for file in package.findall("classes")[0].findall(
                "class"
            ):  # only one 'classes' group per package
                fname = file.attrib["filename"]
                cov = float(file.attrib["line-rate"])
                miss = self._get_missed_lines(file)
                results = [cov]
                if cov < 1:
                    self._missed[fname] = {qt0: miss}

                # find this file in the other coverage report(s)
                for qt in qt_apis:
                    classes = (
                        self.coverage[qt]["packages"]
                        .findall(f"*[@name='{name}']")[0]
                        .findall("classes")[0]
                    )  # only one 'classes' group per package
                    file = classes.findall(f"*[@filename='{fname}']")[0]
                    cov = float(file.attrib["line-rate"])
                    miss = self._get_missed_lines(file)
                    results.append(cov)
                    if cov < 1:
                        if fname not in self._missed:
                            self._missed[fname] = {}
                        self._missed[fname][qt] = miss

                # make this row of html
                html += ["<tr>", f"<td class=fileName>{fname}</td>"]
                for cov in results:
                    td = f"{cov*100:0.0f}%"
                    background_colour = self._get_coverage_css_colour(cov)
                    style = f'style="background-color:{background_colour};"'
                    if cov < 1:
                        href = f"{qt}-missed-{fname}"
                        td = f"<a href=#{href}>{td}</a>"
                    html += [f"<td {style}> {td}</td>"]
                html += ["</tr>"]

        html += ["</table>"]

        return html

    @staticmethod
    def _get_coverage_css_colour(coverage: float):
        if coverage >= 0.9:
            return "var(--excellent)"
        elif coverage >= 0.75:
            return "var(--good)"
        elif coverage >= 0.5:
            return "var(--ok)"
        else:
            return "var(--bad)"

    def _get_missed_lines(self, classGroup):
        """Return string of missed lines in this <class>"""
        lines = classGroup.findall("lines")[0].findall("line")
        miss = [int(line.attrib["number"]) for line in lines if line.attrib["hits"] == "0"]
        if not miss:
            return ""
        miss = np.array(miss)
        consecutive = np.split(miss, np.where(np.diff(miss) != 1)[0] + 1)
        lineNums = []
        for c in consecutive:
            if len(c) > 1:
                s = f"{c[0]}-{c[-1]}"
            else:
                s = str(c[0])
            lineNums.append(s)
        return ", ".join(lineNums)

    def _make_missed_lines_table(self):
        """Make html table of missed lines and return as list of strings"""

        if self._missed is None:
            msg = "'_make_coverage_table' must be called before '_make_missed_lines_table'"
            raise RuntimeError(msg)

        html = ['<h2 id="missed">Missed lines</h2>', "<table class=breakdownTable>"]
        table_header = ["File"] + [self._pretty_qt(qt) for qt in self._qt_apis]
        html += [f"<th>{header}</th>" for header in table_header]

        for fname, dct in self._missed.items():
            html += [f'<tr id="missed-{fname}">', f"<td class=fileName>{fname}</td>"]
            for qt in self._qt_apis:
                miss = dct.get(qt, "")
                html += [f'<td id="{qt}-missed-{fname}">{miss}</td>']
            html += ["</tr>"]

        html += ["</table>"]

        return html

    def make_report(self):
        """Return string of html detailing the test results."""

        # read xml files
        self.testsuites = self._get_test_suites()
        self.coverage = self._get_coverage()

        # get html contents before writing header, so toc can be included at beginning
        main = ['<div class="main">']
        # write python and system version; get timestamp and duration
        main += self._make_summary_info()
        # summarise test results
        main += self._make_summary_table()
        # list dependencies and versions
        main += self._make_dependency_table()
        # test result breakdown
        main += self._make_breakdown_table()
        # list errors, failures and skipped tests
        main += self._make_not_passed_section()
        main += self._make_warnings_section()
        # coverage breakdown
        main += self._make_coverage_table()
        # coverage breakdown
        main += self._make_missed_lines_table()
        # end main
        main += ["</div>"]

        # make table of contents
        toc = self._make_toc(main)

        # make html header, include stylesheet inline
        header = self._make_html_header()

        # make html string
        html = header + ["<body>"] + toc + main + ["</body>", "</html>"]
        html = "\n".join(html)

        return html

    def write_report(self):
        """Get html and write to file."""
        html = self.make_report()
        with open(self.out, "w") as fileobj:
            fileobj.write(html)
        print()
        if self.duration is not None:
            print(f"Tests completed in {self.duration}")
        print(f"Test report written to {self.out.absolute()}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Write html report of pytest results.")
    parser.add_argument(
        "--results", default="./results", help='directory to read results. Default is "./results"'
    )
    parser.add_argument(
        "--out",
        default="./report.html",
        help='path to write output html to. Default is "./report.html"',
    )
    parser.add_argument(
        "--ts",
        default=None,
        help="Timestamp of test execution beginning. If not provided, uses current date and time",
    )

    args = parser.parse_args()
    writer = ReportWriter(args.results, args.out, args.ts)
    writer.write_report()
