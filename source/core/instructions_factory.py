#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Define methods to easily create :class:`.Command` or :class:`.Element`.

.. todo::
    Instantiate this in :class:`.BeamCalculator`. It could be initialized with
    the ``load_electromagnetic_files`` flag (False for TraceWin), the list of
    implemented elements/commands (ex Envelope3D, not everything is set).

.. todo::
    to fix!!! does not recognize lower case commands such as ``end``

.. todo::
    maybe ElementFactory and CommandFactory should be instantiated from this?
    Or from another class, but they do have a lot in common

"""
import os.path
from typing import Any
import logging

import config_manager as con

from core.instruction import Instruction, Dummy

from core.elements.element import Element
from core.elements.dummy import DummyElement
from core.elements.field_maps.field_map import FieldMap
from core.elements.factory import ElementFactory, IMPLEMENTED_ELEMENTS
from core.elements.helper import (give_name_to_elements,
                                  force_a_lattice_for_every_element,
                                  force_a_section_for_every_element,
                                  )

from core.commands.factory import CommandFactory, IMPLEMENTED_COMMANDS
from core.commands.helper import apply_commands

from tracewin_utils.electromagnetic_fields import load_electromagnetic_fields


class InstructionsFactory:
    """Define a factory class to easily create commands and elements."""

    def __init__(self,
                 freq_bunch: float,
                 default_field_map_folder: str,
                 load_field_maps: bool,
                 field_maps_in_3d: bool,
                 load_cython_field_maps: bool,
                 **factory_kw: Any) -> None:
        """Instantiate the command and element factories.

        Parameters
        ----------
        freq_bunch : float
            Beam bunch frequency in MHz.
        default_field_map_folder : str
            Where to look for field maps when no ``FIELD_MAP_PATH`` is
            precised.
        load_field_maps : bool
            To load or not the field maps (useless to do it with
            :class:`.TraceWin`).
        field_maps_in_3d : bool
            To load or not the field maps in 3D (useful only with
            :class:`.Envelope3D`... Except that this is not supported yet, so
            it is never useful.
        load_cython_field_maps : bool
            To load or not the field maps for Cython (useful only with
            :class:`.Envelope1D` and :class:`.Envelope3D` used with Cython).
        factory_kw : Any
            Other parameters passed to the :class:`.CommandFactory` and
            :class:`.ElementFactory`.

        """
        # arguments for commands
        self._freq_bunch = freq_bunch

        if load_field_maps:
            assert os.path.isdir(default_field_map_folder)

        # factories
        self._command_factory = CommandFactory(**factory_kw)
        self._element_factory = ElementFactory(
            default_field_map_folder=default_field_map_folder,
            **factory_kw)

        self._load_field_maps = load_field_maps
        if field_maps_in_3d:
            raise NotImplementedError("No solver can handle 3D field maps yet."
                                      " Except TraceWin, but you do not need "
                                      "to load the field maps with this solver"
                                      ", it does it itself.")
        self._field_maps_in_3d = field_maps_in_3d
        self._load_cython_field_maps = load_cython_field_maps

        self._cython: bool = con.FLAG_CYTHON
        # would be better without config dependency

    def run(self,
            dat_content: list[list[str]],
            ) -> list[Instruction]:
        """
        Create all the elements and commands.

        .. todo::
            Check if the return value from ``apply_commands`` is necessary.

        .. todo::
            remove ``cython`` from here.

        Parameters
        ----------
        dat_content : list[list[str]]
            List containing all the lines of ``dat_filepath``.
        cython : bool
            If the field maps should be loaded for Cython.

        """
        instructions = [self._call_proper_factory(line, dat_idx)
                        for dat_idx, line in enumerate(dat_content)]

        new = apply_commands(instructions, self._freq_bunch)
        assert new == instructions

        elts = [elt for elt in instructions if isinstance(elt, Element)]
        give_name_to_elements(elts)
        self._handle_lattice_and_section(elts)
        self._check_every_elt_has_lattice_and_section(elts)

        if self._load_field_maps:
            field_maps = [elt for elt in elts if isinstance(elt, FieldMap)]
            load_electromagnetic_fields(field_maps,
                                        self._load_cython_field_maps)

        return instructions

    def _call_proper_factory(self,
                             line: list[str],
                             dat_idx: int,
                             **instruction_kw: str) -> Instruction:
        """Create proper :class:`.Instruction`, or :class:`.Dummy`.

        We go across every word of ``line``, and create the first instruction
        that we find. If we do not recognize it, we return a dummy instruction
        instead.

        Parameters
        ----------
        line : list[str]
            A single line of the ``.dat`` file.
        dat_idx : int
            Line number of the line (starts at 0).
        command_fac : CommandFactory
            A factory to create :class:`.Command`.
        element_fac : ElementFactory
            A factory to create :class:`.Element`.
        instruction_kw : dict
            Keywords given to the ``run`` method of the proper factory.

        Returns
        -------
        Instruction
            Proper :class:`.Command` or :class:`.Element`, or :class:`.Dummy`.

        """
        for word in line:
            word = word.upper()
            if word in IMPLEMENTED_COMMANDS:
                return self._command_factory.run(line,
                                                 dat_idx,
                                                 **instruction_kw)
            if word in IMPLEMENTED_ELEMENTS:
                return self._element_factory.run(line,
                                                 dat_idx,
                                                 **instruction_kw)
        return Dummy(line, dat_idx, warning=True)

    def _handle_lattice_and_section(self, elts: list[Element]) -> None:
        """Ensure that every element has proper lattice, section indexes."""
        elts_without_dummies = [elt for elt in elts
                                if not isinstance(elt, DummyElement)]
        force_a_section_for_every_element(elts_without_dummies)
        force_a_lattice_for_every_element(elts_without_dummies)

    def _check_every_elt_has_lattice_and_section(self, elts: list[Element]
                                                 ) -> None:
        """Check that every element has a lattice and section index."""
        for elt in elts:
            if elt.get('lattice', to_numpy=False) is None:
                logging.error("At least one Element is outside of any lattice."
                              " This may cause problems...")
                break

        for elt in elts:
            if elt.get('section', to_numpy=False) is None:
                logging.error("At least one Element is outside of any section."
                              " This may cause problems...")
                break
