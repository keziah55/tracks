#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from cycleTracks.util import (isInt, isFloat, isDate, isDuration, checkMonthYearFloat, 
                              checkHourMinSecFloat, parseDuration, parseDate, 
                              hourMinSecToFloat, monthYearToFloat, dateMonthYearToFloat)
import pytest
from datetime import datetime

def validDateStrings():
    today = datetime.today()
    values = {'02 Mar 17':{'date':2, 'month':3, 'year':2017}, 
              '04 April 19':{'date':4, 'month':4, 'year':2019}, 
              '4/8/20':{'date':4, 'month':8, 'year':2020}, 
              '14-8-2015':{'date':14, 'month':8, 'year':2015}, 
              '':{'date':today.day, 'month':today.month, 'year':today.year},
              '3':{'date':2, 'month':today.month, 'year':today.year}, 
              '5.5':{'date':5, 'month':5, 'year':today.year},
              '020312':{'date':2, 'month':3, 'year':2012}, 
              '02032012':{'date':2, 'month':3, 'year':2012}}
    return values

def invalidDateStrings():
    return ["31 Feb", "invalid", "March", "2020", "6/25/19", "2020/03/01"]

def isDateParams():
    valid = [(s, True) for s in validDateStrings().keys()]
    invalid = [(s, False) for s in invalidDateStrings()]
    return valid + invalid


def validDurationStrings():
    values = {"5":"00:05:00", "12:30":"00:12:30", "100:11":"01:40:01", 
              "30:55:29":"30:55:29"}
    return values

def invalidDurationStrings():
    return ["01:23.30", "invalid"]

def isDurationParams():
    valid = [(s, True) for s in validDurationStrings().keys()]
    invalid = [(s, False) for s in invalidDurationStrings()]
    return valid + invalid
    
@pytest.mark.parametrize("value,valid", [("3", True), ("123456", True), ("16.05", False), ("12 Jan 21", False)])
def test_isInt(value, valid):
    assert isInt(value) is valid
    
@pytest.mark.parametrize("value,valid", [("03", True), (".123456", True), ("16.05", True), ("12 Jan 21", False)])
def test_isFloat(value, valid):
    assert isFloat(value) is valid
    
@pytest.mark.parametrize("value,valid", isDateParams())
def test_isDate(value, valid):
    assert isDate(value) is valid
    
@pytest.mark.parametrize("value,valid", isDurationParams())
def test_isDuration(value, valid):
    assert isDuration(value) is valid