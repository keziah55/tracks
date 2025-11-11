#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Objects to manage creating/editing activities.
"""

import json
from typing import NamedTuple
from .activities import Activity, Measure
from qtpy.QtCore import QObject, Signal, Slot
from qtpy.QtWidgets import (
    QDialog,
    QWidget,
    QFormLayout,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QSpinBox,
)
from customQObjects.widgets import ComboBox


class BoolField(NamedTuple):
    name: str
    value: bool


class BoolComboBox(ComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args, values=[BoolField("True", True), BoolField("False", False)], **kwargs
        )


class MeasureEditor(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.layout = QFormLayout(parent=self)
        self.setLayout(self.layout)

        self._name_edit = QLineEdit()
        self._name_edit.setToolTip("Name of this measure")

        self._dtype_choices = ComboBox()
        self._dtype_choices.addItems(["date", "duration", "float", "int"])
        self._dtype_choices.setToolTip("Type of data for this measure")

        self._summary_func_choices = ComboBox()
        self._summary_func_choices.addItems(["sum", "min", "max", "mean"])
        self._summary_func_choices.setToolTip("Function to use when summarising this data")

        self._is_metadata_choices = BoolComboBox()
        self._is_metadata_choices.setToolTip(
            "True if this measure is data about the session (e.g. Date), "
            "rather than measurement data (e.g. Distance)."
        )

        self._sig_figs_choices = QSpinBox()
        self._sig_figs_choices.setMinimum(1)
        self._sig_figs_choices.setToolTip(
            "Number of significant figures to use when displaying this measure"
        )

        self._unit_edit = QLineEdit()
        self._unit_edit.setToolTip("Unit for this measure (optional)")

        self._show_unit_choices = BoolComboBox()
        self._show_unit_choices.setToolTip(
            "True if the unit should be appended to the name, where appropriate"
        )

        self._plottable_choices = BoolComboBox()
        self._plottable_choices.setToolTip("True if this measure can be plotted as y series")

        self._cmp_func_choices = ComboBox()
        self._cmp_func_choices.setToolTip("Function to use when comparing values of this measure")

        self._is_relation = BoolComboBox()
        self._is_relation.setToolTip("True if this measure is derived from others")

        self._widgets = {
            "name": self._name_edit,
            "dtype": self._dtype_choices,
            "summary": self._summary_func_choices,
            "is_metadata": self._is_metadata_choices,
            "sig_figs": self._sig_figs_choices,
            "unit": self._unit_edit,
            "show_unit": self._show_unit_choices,
            "plottable": self._plottable_choices,
            "cmp_func": self._cmp_func_choices,
            "relation": self._is_relation,
        }

        for key, widget in self._widgets.items():
            name = self._measure_property_to_widget_name(key)
            self.layout.addRow(name, widget)

    def _measure_property_to_widget_name(self, prop: str) -> str:
        dct = {
            "name": "Name",
            "dtype": "Data type",
            "summary": "Summary function",
            "is_metadata": "Is metadata",
            "sig_figs": "Significant figures",
            "unit": "Unit",
            "show_unit": "Show unit",
            "plottable": "Is plottable",
            "cmp_func": "Comparison function",
            "relation": "Is relation",
        }

        if (name := dct.get(prop, None)) is not None:
            return name
        else:
            raise ValueError(f"Unknown Measure property '{prop}'")

    def set_values_from_measure(self, measure: Measure):

        self._name_edit.setText(measure.name)

        self._dtype_choices.setCurrentText(measure.dtype)

        if measure.summary_func_name is not None:
            self._summary_func_choices.setCurrentText(measure.summary_func_name)

        self._is_metadata_choices.setCurrentText(str(measure.is_metadata))

        if measure.sig_figs is not None:
            self._sig_figs_choices.setValue(measure.sig_figs)

        if measure.unit is not None:
            self._summary_func_choices.setText(measure.unit)
            self._show_unit_choices.setCurrentText(str(measure.show_unit))
        else:
            self._show_unit_choices.setEnabled(False)

        self._plottable_choices.setCurrentText(str(measure._show_unit_choices))

        if measure.cmp_func_name is not None:
            self._summary_func_choices.setCurrentText(measure.cmp_func_name)

        if measure.relation is not None:
            self._is_relation.setCurrentIndex("True")
        else:
            self._is_relation.setCurrentIndex("False")


class ActivityEditor(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QVBoxLayout()
        # layout.addWidget(scrollArea)
        # layout.addWidget(self.buttonBox)
        self.setLayout(layout)

        self.setWindowTitle("Create or edit activities")
