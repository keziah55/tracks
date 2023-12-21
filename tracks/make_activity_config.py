#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 30 21:49:33 2023

@author: keziah
"""

import warnings
import re
import pickle
from dataclasses import dataclass
from util import hourMinSecToFloat

class Operation:
    """ Base class for binary operation """
    
    operator: str = None
    
    @staticmethod
    def call(a,b): pass

class Divide(Operation):
    """ Division operation """
    
    operator = "/"
    
    @staticmethod
    def call(a,b): return a/b
    
class Divide_time_min(Divide):
    """ Division that takes denominator as time in hours and converts to minutes before use """
    
    @staticmethod
    def call(a, b):
        b *= 60
        return a/b
    
@dataclass
class Relation:
    """ 
    Class to denote a relationship between two measures.
    
    For example, if m0 is distance, m1 is time and op is division, this 
    relationship gives the speed.
    """
    m0: object    # measure0
    m1: object    # measure1
    op: Operation # operation relating m0 and m1
    name: str     # name for this relationship
    
    def __repr__(self):
        s = f"Relation '{self.name}' = {self.m0.name} {self.op.operator} {self.m1.name}"
        return s
    
class Measure:
    """ 
    Class representing a measure in an activity 
    
    Parameters
    ----------
    name : str
        Name of this measure. NB `slug` will be derived from this
    dtype : {'float', 'int', 'date', 'time'}
        Type of data for this measure (as string)
    summary : {'sum', 'min', 'max', 'mean'}
        Function to call to summarise multiple instances of this measure
    unit : str, optional
        Unit for this measure. If None, and this measure is a relation of two
        other meaures, attempt to infer the unit from the relation.
    show_unit : bool, True
        If `unit` is not None and `show_bool`, signal that the unit should 
        appended to the name, where appropriate.
    plottable : bool, True
        True if this measure can be plotted as y series.
    cmp_func : callable, optional
        Function that should be called to process the value of this measure
        before performing comparisons. (E.g. for a Time, this should be a func
        that converts to float)
    relation : Relation, optional
        Relation instance to signal that this measure is composed of two others.
    """
    
    def __init__(self,
        name: str,
        dtype: str, 
        summary: str, 
        unit: str = None,
        show_unit: bool = True,
        plottable: bool = True,
        cmp_func: callable = None,
        relation: Relation = None,
    ):
        self._name = name
        self._dtype = dtype
        self._summary = summary
        
        self._show_unit = show_unit
        self._plottable = plottable
        self._cmp_func = cmp_func
        
        self._relation = relation
        
        if unit is None and self._relation is not None:
            units = (self._relation.m0.unit, self._relation.m1.unit)
            if any([u is None for u in units]):
                msg = f"No unit defined for either {self._relation.m0} or {self._relation.m1}"
                msg += "Cannot infer unit"
                warnings.warn(msg)
            else:
                unit = f"{units[0]}{self._relation.op.operator}{units[1]}"
        self._unit = unit
        
        self._properties = ["name", "dtype", "summary", "unit", "show_unit",
                            "plottable", "cmp_func", "relation"]
        
    def __getattr__(self, name):
        if name in self._properties:
            return self.__getattribute__(f"_{name}")
        
    def __repr__(self):
        s = f"Measure '{self._name}'"
        return s
    
    def __getstate__(self):
        return vars(self)
    
    def __setstate__(self, state):
        vars(self).update(state)
    
    @property
    def slug(self):
        slug = self.name.lower()
        slug = re.sub(r"\s+", "_", slug)
        slug = re.escape(slug)
        return slug
    
    @property
    def user(self):
        return self._relation is None
    
class Activity:
    """ 
    Class defining an activity.
    """
    def __init__(self, name):
        self._name = name
        self._measures = {}
    
    def __getattr__(self, name):
        if (m:=self._measures.get(name, None)) is not None:
            return m
        for m in self._measures.values():
            if m.name == name:
                return m
        raise AttributeError(f"'Activity' has no measure '{name}'")
        
    def __repr__(self):
        s = f"Activity '{self._name}'"
        return s
    
    def __getstate__(self):
        return vars(self)
    
    def __setstate__(self, state):
        vars(self).update(state)
        
    @property
    def measures(self):
        return list(self._measures.keys())
    
    def add_measure(self, *args, **kwargs):
        m = Measure(*args, **kwargs)
        self._measures[m.slug] = m
    
    def header(self):
        header = []
        
        for measure in self._measures.values():
            name = measure.name
            if measure.unit is not None and measure.show_unit:
                name = f"{name} ({measure.unit})"
            header.append(name)
            
        return header
    
    def save(self, p):
        with open(p, 'wb') as fileobj:
            pickle.dump(self, fileobj)
  
    
if __name__ == "__main__":
    
    from pathlib import Path
    
    p = Path.home().joinpath(".tracks")
    
    cycling = Activity("cycling")
    
    cycling.add_measure(
        name = "Date",
        dtype = "date", 
        summary = None, 
        plottable = False,
    )
        
    cycling.add_measure(
        name = "Time",
        dtype = "time", 
        summary = "sum", 
        unit = "h", 
        show_unit = False, 
        cmp_func = hourMinSecToFloat,
    )
    
    cycling.add_measure(
        name = "Distance",
        dtype = "float", 
        summary = "sum", 
        unit = "km", 
        cmp_func = float,
    )
    
    cycling.add_measure(
        name = "Calories",
        dtype = "float", 
        summary = "sum", 
        cmp_func = float,
    )
    
    cycling.add_measure(
        name = "Gear",
        dtype = "int", 
        summary = "mean", 
        plottable = False, 
        cmp_func = float,
        )
    
    cycling.add_measure(
        name = "Speed",
        dtype = "float", 
        summary = "max", 
        relation = Relation(cycling.distance, cycling.time, Divide, "Speed"), 
        cmp_func = float,
    )
         
    cycling.save(p.joinpath("cycling_activity"))  
    
    rowing = Activity("rowing")
     
    rowing.add_measure(
        name = "Date",
        dtype = "date", 
        summary = None, 
        plottable = False,
    )
        
    rowing.add_measure(
        name = "Time",
        dtype = "time", 
        summary = "sum", 
        unit = "h", 
        show_unit = False, 
        cmp_func = hourMinSecToFloat,
    )
    
    rowing.add_measure(
        name = "Distance",
        dtype = "float", 
        summary = "sum", 
        unit = "km", 
        cmp_func = float,
    )
    
    rowing.add_measure(
        name = "Calories",
        dtype = "float", 
        summary = "sum", 
        cmp_func = float,
    )
    
    rowing.add_measure(
        name = "Gear",
        dtype = "int", 
        summary = "mean", 
        plottable = False, 
        cmp_func = float,
        )
    
    rowing.add_measure(
        name = "Strokes",
        dtype = "int", 
        summary = "sum", 
        unit = "stroke",
        show_unit = False,
        cmp_func = float,
    )
    
    rowing.add_measure(
        name = "Speed",
        dtype = "float", 
        summary = "max", 
        relation = Relation(cycling.distance, cycling.time, Divide, "Speed"), 
        cmp_func = float,
    )
    
    rowing.add_measure(
        name = "Stroke rate",
        dtype = "float", 
        summary = "max", 
        unit = "stroke/min",
        relation = Relation(rowing.strokes, rowing.time, Divide_time_min, "Stroke Rate"), 
        cmp_func = float,
    )

    rowing.save(p.joinpath("rowing_activity"))  