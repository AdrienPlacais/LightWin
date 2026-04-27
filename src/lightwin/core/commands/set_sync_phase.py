"""Define the SET_SYNC_PHASE command.

.. todo::
    Should also modify RFQ_CEL, CAVSIN, NCELLS according to doc.

"""

import logging
from collections.abc import Sequence

from lightwin.core.commands.command import Command
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.instruction import Instruction
from lightwin.tracewin_utils.line import DatLine
from lightwin.util.typing import REFERENCE_PHASES_T


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
        raise OSError(
            "Reached end of file without finding associated FIELD_MAP."
        )

    def apply(
        self, instructions: Sequence[Instruction], **kwargs: float
    ) -> list[Instruction]:
        """Set ``phi_s``, remove previous reference phase.

        When we apply this method, LightWin believes that the phase given in
        the ``DAT`` file is an absolute or relative phase. We update the
        ``reference`` of the |CS|, as well as the actual value of ``phi_ref ==
        phi_s``.

        """
        for cavity in instructions[self.influenced]:
            assert isinstance(cavity, FieldMap)
            settings = cavity.cavity_settings
            # note that, at this point, LightWin believes that the phase given
            # in the .dat is an absolute or relative phase
            settings.set_reference("phi_s", phi_ref=settings.phi_ref)
        return list(instructions)

    def to_line(
        self, *args, which_phase: REFERENCE_PHASES_T, **kwargs
    ) -> list[str]:
        """Return ``"SET_SYNC_PHASE"``.

        .. note::
            We return a commented line when ``which_phase`` is not ``"phi_s``,
            to keep output ``DAT`` as close as possible to the original one.

        .. warning::
           :meth:`.ListOfElements.store_settings_in_dat` can manually add a
           ``SET_SYNC_PHASE`` command. It happens when a ``FIELD_MAP`` has a
           reference phase different from ``"phi_s"`` but this changed during
           the simulation.

        """
        line = super().to_line(*args, **kwargs)
        if line is None:
            raise ValueError("line should not be empty")
        if which_phase == "phi_s":
            return line
        line.insert(0, ";")
        return line
