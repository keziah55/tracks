#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get functions to validate/cast Activity types.
"""

from typing import Callable
import polars as pl
from .validate import isInt, isFloat, isDate, isDuration
from .convertfuncs import parseDuration, parseDate, hourMinSecToFloat


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

pl_type_map = {"date": pl.Date, "duration": pl.Float64, "float": pl.Float64, "int": pl.Int64}


def list_reduce_funcs() -> list[str]:
    return list(reduce_funcs.keys())


def get_reduce_func(name: str) -> Callable:

    if (f := reduce_funcs.get(name, None)) is None:
        raise ValueError(f"Could not get reduce func for '{name}'")
    else:
        return f


def get_reduce_func_key(f: Callable) -> str:
    for key, func in reduce_funcs.items():
        if f == func:
            return key
    raise ValueError(f"Function {f} not in reduce_funcs dict")


def get_validate_func(dtype: str) -> Callable:

    if (f := validate_funcs.get(dtype, None)) is None:
        raise ValueError(f"Could not get vaildate func for '{dtype}'")
    else:
        return f


def get_cast_func(dtype: str) -> Callable:

    if (f := cast_funcs.get(dtype, None)) is None:
        raise ValueError(f"Could not get cast func for '{dtype}'")
    else:
        return f


def get_pl_type(dtype: str) -> type:

    if (t := pl_type_map.get(dtype, None)) is None:
        raise ValueError(f"Could not get polars type for '{dtype}'")
    else:
        return t
