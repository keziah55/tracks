#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Operations for Relations between Measures.
"""


class Operation:
    """Base class for binary operation"""

    operator: str = None

    @staticmethod
    def call(a, b):
        pass


class Divide(Operation):
    """Division operation"""

    operator = "/"

    @staticmethod
    def call(a, b):
        return a / b


class Divide_time_min(Divide):
    """Division that takes denominator as time in hours and converts to minutes before use"""

    @staticmethod
    def call(a, b):
        c = b * 60
        return a / c


operator_dict = {
    "Divide": Divide,
    "Divide_time_min": Divide_time_min,
}
