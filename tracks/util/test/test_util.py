#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tracks.util import (
    isInt,
    isFloat,
    isDate,
    isDuration,
    checkMonthYearFloat,
    checkHourMinSecFloat,
    checkDayMonthYearFloat,
    parseDuration,
    parseDate,
    hourMinSecToFloat,
    monthYearToFloat,
    dayMonthYearToFloat,
    floatToHourMinSec,
)
import pytest
from datetime import datetime, date
import polars as pl
import numpy as np


def validDateStrings():
    today = datetime.today()
    values = [
        ("02 Mar 17", {"day": 2, "month": 3, "year": 2017}),
        ("04 April 19", {"day": 4, "month": 4, "year": 2019}),
        ("4/8/20", {"day": 4, "month": 8, "year": 2020}),
        ("14-8-2015", {"day": 14, "month": 8, "year": 2015}),
        ("", {"day": today.day, "month": today.month, "year": today.year}),
        ("3", {"day": 3, "month": today.month, "year": today.year}),
        ("5.5", {"day": 5, "month": 5, "year": today.year}),
        ("020312", {"day": 2, "month": 3, "year": 2012}),
        ("02032012", {"day": 2, "month": 3, "year": 2012}),
    ]
    return values


def invalidDateStrings():
    lst = ["31 Feb", "invalid", "March", "2020", "6/25/19", "2020/03/01"]
    return [(item, None) for item in lst]


def isDateParams():
    valid = [(tup[0], True) for tup in validDateStrings()]
    invalid = [(tup[0], False) for tup in invalidDateStrings()]
    return valid + invalid


def validDurationStrings():
    values = [
        ("5", "00:05:00"),
        ("12:30", "00:12:30"),
        ("100:11", "01:40:11"),
        ("30:55:29", "30:55:29"),
    ]
    return values


def invalidDurationStrings():
    lst = ["01:23.30", "invalid"]
    return [(item, None) for item in lst]


def isDurationParams():
    valid = [(tup[0], True) for tup in validDurationStrings()]
    invalid = [(tup[0], False) for tup in invalidDurationStrings()]
    return valid + invalid


def convertParams():
    lst = [
        (
            hourMinSecToFloat,
            checkHourMinSecFloat,
            [
                ("03:45:12", 3 + (45 / 60) + (12 / 3600)),
                ("00:00:58", 58 / 3600),
                ("10:00:00", 10),
                ("03:45:11", 3 + (45 / 60) + (11 / 3600)),
                ("03:45:13", 3 + (45 / 60) + (13 / 3600)),
                ("03:46:12", 3 + (46 / 60) + (12 / 3600)),
                ("02:45:12", 2 + (45 / 60) + (12 / 3600)),
                ("15:23", None),
                ("12", None),
            ],
            [1, 6, 3, 0, 4, 5, 2],
        ),
        (
            monthYearToFloat,
            checkMonthYearFloat,
            [
                ("Apr 2016", 2016.25),
                ("March 2016", 2016 + (2 / 12)),
                ("December 2019", 2019 + (11 / 12)),
                ("Jan 2020", 2020),
                ("15 June 2023", None),
                ("May 20", None),
                ("Blah 2021", None),
            ],
            [1, 0, 2, 3],
        ),
        (
            dayMonthYearToFloat,
            checkDayMonthYearFloat,
            [
                ("1 May 2016", 1 + (5 * 31) + (2016 * 31 * 12)),
                ("30 Apr 2016", 30 + (4 * 31) + (2016 * 31 * 12)),
                ("1 Jan 2020", 1 + 31 + (2020 * 31 * 12)),
                ("31 December 2019", 31 + (12 * 31) + (2019 * 31 * 12)),
                ("15 June", None),
                ("5 May 20", None),
                ("32 May 2020", None),
                ("10 Blah 2021", None),
            ],
            [1, 0, 3, 2],
        ),
    ]
    return lst


@pytest.mark.parametrize(
    "value,valid",
    [("3", True), ("123456", True), ("16.05", False), ("12 Jan 21", False)],
)
def test_isInt(value, valid):
    assert isInt(value) is valid


@pytest.mark.parametrize(
    "value,valid",
    [("03", True), (".123456", True), ("16.05", True), ("12 Jan 21", False)],
)
def test_isFloat(value, valid):
    assert isFloat(value) is valid


@pytest.mark.parametrize("value,valid", isDateParams())
def test_isDate(value, valid):
    assert isDate(value) is valid


@pytest.mark.parametrize("value,valid", isDurationParams())
def test_isDuration(value, valid):
    assert isDuration(value) is valid


@pytest.mark.parametrize("value,expected", validDateStrings() + invalidDateStrings())
def test_parseDate(value, expected):
    if expected is None:
        with pytest.raises(ValueError):
            parseDate(value)
    else:
        expected = date(expected["year"], expected["month"], expected["day"])
        assert parseDate(value) == expected


def test_parseDate_type_error():
    with pytest.raises(TypeError):
        parseDate(25)


def test_parseDate_value_error():
    with pytest.raises(ValueError):
        parseDate("25 Jn 2021")


@pytest.mark.parametrize("value,expected", validDurationStrings() + invalidDurationStrings())
def test_parseDuration(value, expected):
    if expected is None:
        with pytest.raises(ValueError):
            parseDuration(value)
    else:
        assert parseDuration(value) == expected


@pytest.mark.parametrize("convert_func,check_func,values,expected_idx", convertParams())
def test_convert_to_float(convert_func, check_func, values, expected_idx):
    for value, expected in values:
        valid = False if expected is None else True
        assert check_func(value) is valid

        if valid:
            if convert_func(value) % 1 == 0 and expected % 1 == 0:
                assert convert_func(value) == expected
            else:
                assert np.isclose(convert_func(value), expected)
        else:
            with pytest.raises(ValueError):
                convert_func(value)

    values = [tup[0] for tup in values if tup[1] is not None]
    expected = [values[idx] for idx in expected_idx]

    sorted_values = sorted(values, key=convert_func)
    assert sorted_values == expected


@pytest.mark.parametrize("value", [0.12, 1.23, 5.274564, 0.057])
def test_float_to_hms(value):
    s = floatToHourMinSec(value)
    value2 = hourMinSecToFloat(s)
    assert np.isclose(value, value2, atol=1 / 3600)  # tolerance within one second


@pytest.mark.parametrize(
    "value,expected",
    [
        ("1:23:45", 5025),
        ("20:05", 1205),
        ("45", None),
        ("65:12", 3912),
        ("invalid", None),
    ],
)
def test_hms_to_float_non_strict(value, expected):
    if expected is None:
        with pytest.raises(ValueError):
            hourMinSecToFloat(value, mode="sec", strict=False)
            # self.data._timeToSecs(value)
    else:
        assert hourMinSecToFloat(value, mode="sec", strict=False) == expected
