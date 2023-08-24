#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 22 10:26:19 2021.

@author: placais

This module holds all the commands.

"""


class Lattice:
    """Used to get the number of elements per lattice."""

    def __init__(self, elem: list[str]) -> None:
        self.n_lattice = int(elem[1])


class Freq:
    """Used to get the frequency of every Section."""

    def __init__(self, elem: list[str]) -> None:
        self.f_rf_mhz = float(elem[1])


class FieldMapPath:
    """Used to get the base path of field maps."""

    def __init__(self, elem: list[str]) -> None:
        self.path = elem[1]


class End:
    """The end of the linac."""

    def __init__(self, elem: list[str]) -> None:
        pass
