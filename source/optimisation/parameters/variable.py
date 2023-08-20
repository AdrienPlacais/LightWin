#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 18 17:25:02 2023.

@author: placais

This module holds the class `Variable`, which stores an optimisation variable
with its name, bounds, initial value, etc.

"""
import logging
from dataclasses import dataclass

import numpy as np

from util.dicts_output import markdown


IMPLEMENTED = ('k_e', 'phi_0_abs', 'phi_0_rel', 'phi_s')


@dataclass
class Variable:
    """
    A single variable.

    It can be a cavity amplitude, absolute phase, relative phase or synchronous
    phase with an initial value and limits.

    """

    name: str
    cavity_name: str
    x_0: float
    limits: tuple

    def __post_init__(self):
        """Convert values in deg for output if it is angle."""
        if self.name not in IMPLEMENTED:
            logging.warning(f"Variable {self.name} not tested.")

        self.x_0_fmt, self.limits_fmt = self.x_0, self.limits
        if 'phi' in self.name:
            self.x_0_fmt = np.rad2deg(self.x_0)
            self.limits_fmt = np.rad2deg(self.limits)

    def __str__(self) -> str:
        """Output variable name, initial value and limits."""
        out = f"{markdown[self.name]:20} {self.cavity_name:5} "
        out += f"x_0={self.x_0_fmt:>8.3f}   "
        out += f"limits={self.limits_fmt[0]:>8.3f} {self.limits_fmt[1]:>8.3f}"
        return out
