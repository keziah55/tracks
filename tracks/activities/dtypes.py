#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get functions to validate/cast Activity types.
"""

from tracks.util import (hourMinSecToFloat, isDate, isFloat, isInt, isDuration, 
                         parseDate, parseDuration)

validate_methods = {
    "date": isDate,
    "duration": isDuration,
    "float": isFloat,
    "int": isInt
}

cast_methods = {
    "date": parseDate,
    "duration": parseDuration,
    "float": float,
    "int": int,
    "str": str,
    "time_to_float": hourMinSecToFloat
}

def get_validate_method(dtype):
    m = validate_methods.get(dtype, None)
    if m is None:
        raise ValueError(f"Could not get vaildate method for '{dtype}'")
    return m

def get_cast_method(dtype):
    m = cast_methods.get(dtype, None)
    if m is None:
        raise ValueError(f"Could not get cast method for '{dtype}'")
    return m