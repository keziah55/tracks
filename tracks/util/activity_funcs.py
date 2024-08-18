#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get functions to validate/cast Activity types.
"""

from .validate import isInt, isFloat, isDate, isDuration
from .convertfuncs import parseDuration, parseDate, hourMinSecToFloat
import numpy as np


def _mean(series):
    return series.mean()


reduce_funcs = {"sum": sum, "min": min, "max": max, "mean": _mean}

validate_funcs = {
    "date": isDate,
    "duration": isDuration,
    "float": isFloat,
    "int": isInt,
}

cast_funcs = {
    "date": parseDate,
    "duration": lambda value: hourMinSecToFloat(parseDuration(value)),
    "float": float,
    "int": int,
    "str": str,
    "hourMinSecToFloat": hourMinSecToFloat,
}


def list_reduce_funcs():
    return list(reduce_funcs.keys())


def get_reduce_func(name):
    f = reduce_funcs.get(name, None)
    if f is None:
        raise ValueError(f"Could not get reduce func for '{name}'")
    return f


def get_reduce_func_key(f):
    for key, func in reduce_funcs.items():
        if f == func:
            return key
    raise ValueError(f"Function {f} not in reduce_funcs dict")


def get_validate_func(dtype):
    f = validate_funcs.get(dtype, None)
    if f is None:
        raise ValueError(f"Could not get vaildate func for '{dtype}'")
    return f


def get_cast_func(dtype):
    f = cast_funcs.get(dtype, None)
    if f is None:
        msg = f"Could not get cast func for '{dtype}'"
        raise ValueError(msg)
    return f
