"""Define the SET_SYNC_PHASE command.

.. todo::
    Should also modify RFQ_CEL, CAVSIN, NCELLS according to doc.

"""

import logging
from collections.abc import Sequence
from typing import Literal

from lightwin.core.commands.command import Command
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.instruction import Instruction
from lightwin.tracewin_utils.line import DatLine


class SetSyncPhase(Command):
    """A class that modifies reference phase of next cavity."""

    is_implemented = True
    n_attributes = 0

    def __init__(
        self, line: DatLine, dat_idx: int | None = None, **kwargs: str
    ) -> None:
        """Instantiate command."""
        return super().__init__(line, dat_idx)

    def set_influenced_elements(
        self, instructions: Sequence[Instruction], **kwargs: float
    ) -> None:
        """Capture first cavity after this command."""
        for instruction in instructions[self.idx["dat_idx"] + 1 :]:
            if isinstance(instruction, SetSyncPhase):
                logging.error("Two consecutive SET_SYNC_PHASE.")
            if isinstance(instruction, FieldMap):
                start = instruction.idx["dat_idx"]
                stop = start + 1
                self.influenced = slice(start, stop)
                return
        raise IOError(
            "Reached end of file without finding associated FIELD_MAP."
        )

    def apply(
        self, instructions: list[Instruction], **kwargs: float
    ) -> list[Instruction]:
        """Modify reference of cavity."""
        for cavity in instructions[self.influenced]:
            assert isinstance(cavity, FieldMap)
            settings = cavity.cavity_settings
            # note that, at this point, LightWin believes that the phase given
            # in the .dat is an absolute or relative phase
            phi_s = settings.phi_ref
            assert phi_s is not None
            settings.reference = "phi_s"
            settings.phi_ref = phi_s
        return instructions

    def to_line(
        self,
        *args,
        which_phase: Literal["phi_0_abs", "phi_0_rel", "phi_s"],
        **kwargs,
    ) -> list[str]:
        """Return the command, commented if output phase should not be phi_s.

        .. note::
            We keep old implementation for now. But this method returns nothing
            because the ``to_line`` method of :class:`.FieldMap` already
            handles adding a ``SET_SYNC_PHASE`` when necessary.

        """
        return []
        line = super().to_line(*args, **kwargs)
        if which_phase == "phi_s":
            return line
        line.insert(0, ";")
        return line
