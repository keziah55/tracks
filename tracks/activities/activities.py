#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Define Activities
"""

import warnings
import re
import json
from .operations import operator_dict
from .dtypes import cast_methods
    

class Relation:
    """ 
    Class to denote a relationship between two measures.
    
    For example, if m0 is distance, m1 is time and op is division, this 
    relationship gives the speed.
    
    Parameters
    ----------
    m0 : Measure
        lhs measure
    m1 : Measure
        rhs Measure
    op : Operation
        Operation relating m0 and m1
    name : str
        Name for this realtionship
    """
    
    def __init__(self, m0, m1, op, name):
        if isinstance(m0, dict):
            m0 = Measure(**m0)
        self.m0 = m0
        
        if isinstance(m1, dict):
            m1 = Measure(**m1)
        self.m1 = m1
        
        if isinstance(op, str) and op in operator_dict:
            op = operator_dict[op]
        self.op = op
        
        self.name = name
    
    def __repr__(self):
        s = f"Relation '{self.name}' = {self.m0.name} {self.op.operator} {self.m1.name}"
        return s
    
    def to_json(self):
        dct = {
            "m0":self.m0.to_json(),
            "m1":self.m1.to_json(),
            "op":self.op.__name__,
            "name":self.name,
        }
        return dct
    
class Measure:
    """ 
    Class representing a measure in an activity 
    
    Parameters
    ----------
    name : str
        Name of this measure. NB `slug` will be derived from this
    dtype : {'float', 'int', 'date', 'duration'}
        Type of data for this measure (as string)
    summary : {'sum', 'min', 'max', 'mean'}
        Function to call to summarise multiple instances of this measure
    is_metadata : bool
        True if this measure is data about the session (e.g. Date), rather than 
        measurement data (e.g. Distance). Default is False.
    sig_figs: int, optional
        Number of significant figures to use when displaying this measure
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
        is_metadata: bool = False,
        sig_figs: int = None,
        unit: str = None,
        show_unit: bool = True,
        plottable: bool = True,
        cmp_func: callable = None,
        relation: Relation = None,
    ):
        self._name = name
        self._dtype = dtype
        self._summary = summary
        self._is_metadata = is_metadata
        self._sig_figs = sig_figs
        self._show_unit = show_unit
        self._plottable = plottable
        
        if isinstance(cmp_func, str):
            if cmp_func in cast_methods:
                cmp_func = cast_methods[cmp_func]
        self._cmp_func = cmp_func
        
        if isinstance(relation, dict):
            relation = Relation(**relation)
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
        
        self._properties = ["name", "dtype", "summary", "is_metadata", "sig_figs", "unit", 
                            "show_unit", "plottable", "cmp_func", "relation"]
        
    def __getattr__(self, name):
        if name in self._properties:
            return self.__getattribute__(f"_{name}")
        
    def __repr__(self):
        s = f"Measure '{self._name}'"
        return s
    
    def to_json(self):
        cmp_func = self.cmp_func.__name__ if self.cmp_func is not None else None
        relation = self.relation.to_json() if self.relation is not None else None
        dct = {
            "name": self.name,
            "dtype": self.dtype,
            "summary": self.summary,
            "is_metadata":self.is_metadata,
            "sig_figs": self.sig_figs,
            "unit": self.unit,
            "show_unit": self.show_unit,
            "plottable": self.plottable,
            "cmp_func": cmp_func,
            "relation": relation,
        }
        return dct
    
    @property
    def slug(self):
        slug = self.name.lower()
        slug = re.sub(r"\s+", "_", slug)
        slug = re.escape(slug)
        return slug
    
    @property
    def user(self):
        return self._relation is None
    
    @property
    def full_name(self):
        name = self.name
        if self.show_unit and self.unit is not None:
            name = f"{name} ({self.unit})"
        return name
    
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
    
    @property
    def csv_file(self):
        return f"{self._name.lower()}.csv"
    
    @property
    def json_file(self):
        return f"{self._name.lower()}.json"
        
    @property
    def measures(self):
        return self._measures
    
    def add_measure(self, *args, **kwargs):
        m = Measure(*args, **kwargs)
        self._measures[m.slug] = m
        
    def get_measure(self, name):
        if (m:=self._measures.get(name, None)) is not None:
            return m
        for m in self._measures.values():
            if name in [m.name, m.full_name]:
                return m
        
    @property
    def header(self):
        header = [measure.full_name for measure in self._measures.values()]
        return header
    
    @property
    def user_input_header(self):
        header = [measure.full_name for measure in self._measures.values() if measure.relation is None]
        return header
    
    def to_json(self):
        measures = {k: m.to_json() for k, m in self._measures.items()}
        dct = {
            "name": self._name,
            "measures": measures
        }
        return dct
    
    def save(self, save_dir):
        """ Write json file to `save_dir` """
        p = save_dir.joinpath(self.json_file)
        with open(p, 'w') as fileobj:
            json.dump(self.to_json(), fileobj, indent=4)
            
    def get_relations(self):
        """ Return dict of measures in activity that are relations between others. """
        relations = {m.full_name: m.relation for m in self._measures.values() if m.relation is not None}
        return relations