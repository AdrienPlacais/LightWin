"""Define methods to easily create :class:`.Command` or :class:`.Element`.

.. todo::
    Instantiate this in :class:`.BeamCalculator`. It could be initialized with
    the ``load_electromagnetic_files`` flag (False for TraceWin), the list of
    implemented elements/commands (ex Envelope3D, not everything is set).

.. todo::
    maybe ElementFactory and CommandFactory should be instantiated from this?
    Or from another class, but they do have a lot in common

"""

import logging
from abc import ABCMeta
from collections.abc import Collection, Sequence
from itertools import zip_longest
from pathlib import Path
from typing import Any

from lightwin.core.commands.factory import IMPLEMENTED_COMMANDS, CommandFactory
from lightwin.core.commands.helper import apply_commands
from lightwin.core.elements.dummy import DummyElement
from lightwin.core.elements.element import Element
from lightwin.core.elements.factory import IMPLEMENTED_ELEMENTS, ElementFactory
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.elements.helper import (
    force_a_lattice_for_every_element,
    force_a_section_for_every_element,
    give_name_to_elements,
)
from lightwin.core.em_fields.field_factory import FieldFactory
from lightwin.core.instruction import Comment, Dummy, Instruction, LineJump
from lightwin.core.list_of_elements.helper import (
    group_elements_by_section,
    group_elements_by_section_and_lattice,
)
from lightwin.tracewin_utils.line import DatLine


class InstructionsFactory:
    """Define a factory class to easily create commands and elements."""

    def __init__(
        self,
        freq_bunch_mhz: float,
        default_field_map_folder: Path,
        load_field: bool,
        field_maps_in_3d: bool,
        load_cython_field_maps: bool,
        elements_to_dump: ABCMeta | tuple[ABCMeta, ...] = (),
        **factory_kw: Any,
    ) -> None:
        """Instantiate the command and element factories.

        Parameters
        ----------
        freq_bunch_mhz :
            Beam bunch frequency in :unit:`MHz`.
        default_field_map_folder :
            Where to look for field maps when no ``FIELD_MAP_PATH`` is
            precised. This is also the folder where the ``DAT`` is.
        load_field :
            Whether :class:`.Field` should be created. This is not supported
            yet for :class:`.CyEnvelope1D` and :class:`.Envelope3D`, but it is
            mandatory for :class:`.Envelope1D`.
        field_maps_in_3d :
            Whether 3D field maps should be loaded. This is useful only with
            :class:`.Envelope3D`... Except that this is not supported yet, so
            it is never useful.
        load_cython_field_maps :
            To load or not the field maps for Cython (useful only with
            :class:`.Envelope1D` and :class:`.Envelope3D` used with Cython).
        elements_to_dump :
            Class of Elements that you want to remove. If you want to skip an
            Element because it is not implemented, prefer assigning it to a
            :class:`.DummyElement`.
        factory_kw :
            Other parameters passed to the :class:`.CommandFactory` and
            :class:`.ElementFactory`.

        """
        # arguments for commands
        self._freq_bunch_mhz = freq_bunch_mhz

        if load_field:
            assert default_field_map_folder.is_dir()

        # factories
        self._command_factory = CommandFactory(
            default_field_map_folder=default_field_map_folder, **factory_kw
        )
        self.element_factory = ElementFactory(
            default_field_map_folder=default_field_map_folder,
            freq_bunch_mhz=freq_bunch_mhz,
            **factory_kw,
        )
        self._elements_to_dump = elements_to_dump

        self._load_field = load_field
        if field_maps_in_3d:
            raise NotImplementedError(
                "No solver can handle 3D field maps yet. Except TraceWin, but "
                "you do not need to load the field maps with this solver, it "
                "does it itself."
            )
        self._field_maps_in_3d = field_maps_in_3d
        self._load_cython_field_maps = load_cython_field_maps
        self._field_factory = FieldFactory(
            default_field_map_folder,
            load_cython_field_maps=load_cython_field_maps,
        )

    def run(self, dat_filecontent: Collection[DatLine]) -> list[Instruction]:
        """Create all the elements and commands.

        .. todo::
            Check if the return value from ``apply_commands`` is necessary.

        Parameters
        ----------
        dat_filecontent :
            List containing all the lines of ``dat_filepath``.

        """
        instructions = [
            self._call_proper_factory(line, dat_idx)
            for dat_idx, line in enumerate(dat_filecontent)
        ]
        instructions = apply_commands(instructions, self._freq_bunch_mhz)

        elts = [elt for elt in instructions if isinstance(elt, Element)]
        give_name_to_elements(elts)
        self._handle_lattice_and_section(elts)
        self._check_every_elt_has_lattice_and_section(elts)
        self._check_last_lattice_of_every_lattice_is_complete(elts)
        self._filter_out_elements_to_dump(elts)

        if self._load_field:
            field_maps = [elt for elt in elts if isinstance(elt, FieldMap)]
            self._field_factory.run_all(field_maps)

        return instructions

    def _call_proper_factory(
        self,
        dat_line: DatLine,
        dat_idx: int | None = None,
        **instruction_kw: str,
    ) -> Instruction:
        """Create proper :class:`.Instruction`, or :class:`.Dummy`.

        We go across every word of ``line``, and create the first instruction
        that we find. If we do not recognize it, we return a dummy instruction
        instead.

        Parameters
        ----------
        line :
            A single line of the ``DAT`` file.
        dat_idx :
            Line number of the line (starts at 0). If not provided, taken from
            ``line``.
        command_fac :
            A factory to create :class:`.Command`.
        element_fac :
            A factory to create :class:`.Element`.
        instruction_kw :
            Keywords given to the ``run`` method of the proper factory.

        Returns
        -------
            Proper :class:`.Command` or :class:`.Element`, or :class:`.Dummy`,
            or :class:`.Comment`.

        """
        if not dat_line.instruction:
            return LineJump(dat_line, dat_idx)
        if dat_line.instruction == ";":
            return Comment(dat_line, dat_idx)
        if dat_line.instruction in IMPLEMENTED_COMMANDS:
            return self._command_factory.run(
                dat_line, dat_idx, **instruction_kw
            )
        if dat_line.instruction in IMPLEMENTED_ELEMENTS:
            return self.element_factory.run(
                dat_line, dat_idx, **instruction_kw
            )

        return Dummy(dat_line, warning=True)

    def _handle_lattice_and_section(self, elts: list[Element]) -> None:
        """Ensure that every element has proper lattice, section indexes."""
        elts_without_dummies = [
            elt for elt in elts if not isinstance(elt, DummyElement)
        ]
        force_a_section_for_every_element(elts_without_dummies)
        force_a_lattice_for_every_element(elts_without_dummies)

    def _check_every_elt_has_lattice_and_section(
        self, elts: list[Element]
    ) -> None:
        """Check that every element has a lattice and section index."""
        for elt in elts:
            if elt.idx["lattice"] == -1:
                logging.error(
                    "At least one Element is outside of any lattice. This may "
                    "cause problems..."
                )
                break

        for elt in elts:
            if elt.idx["section"] == -1:
                logging.error(
                    "At least one Element is outside of any section. This may "
                    "cause problems..."
                )
                break

    def _check_last_lattice_of_every_lattice_is_complete(
        self, elts: Sequence[Element]
    ) -> None:
        """Check that last lattice of every section is complete."""
        by_section_and_lattice = group_elements_by_section_and_lattice(
            group_elements_by_section(elts)
        )
        for sec, lattices in enumerate(by_section_and_lattice):
            if len(lattices) <= 1:
                continue
            if (ultim := len(lattices[-1])) == (penult := len(lattices[-2])):
                continue
            joined = "\n".join(
                (
                    f"{str(x):>20}\t{str(y):<20}"
                    for x, y in zip_longest(
                        lattices[-2], lattices[-1], fillvalue="-"
                    )
                )
            )
            joined = f"{'Penultimate:':>20}\t{'Ultimate:':<20}\n" + joined
            logging.warning(
                f"Lattice length mismatch in the {sec}th section. The last "
                f"lattice of this section has {ultim} elements, while "
                f"penultimate has {penult} elements. This may create problems "
                "if you rely on lattices identification to compensate faults. "
            )
            logging.debug(f"{joined}")

    def _filter_out_elements_to_dump(self, elts: list[Element]) -> None:
        """Remove the desired elements."""
        removed_elts = [
            elts.pop(i)
            for i, elt in enumerate(elts)
            if isinstance(elt, self._elements_to_dump)
        ]
        n_removed = len(removed_elts)
        if n_removed > 0:
            types = {elt.__class__.__name__ for elt in removed_elts}
            logging.warning(
                f"Removed {n_removed} elements, according to the "
                "InstructionsFactory._elements_to_dump key. The removed "
                f"elements have types: {types}.\nNote that with TraceWin, "
                "every Command and Element is kept.\nNote that this will "
                "likely lead to problems when visualising structure -- prefer "
                "setting a Dummy element to ignore non-implemented elements."
            )
