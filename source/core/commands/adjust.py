"""Define the ADJUST command.

As for now, ADJUST commands are not used by LightWin.

Functionnality under implementation: LightWin will be able to add ADJUST and
DIAGNOSTIC commands to perform a beauty pass.

.. todo::
    How should I save the min/max variables?? For now, use None.

.. note::
    This is TraceWin's equivalent of :class:`.Variable`.

"""

from typing import override

from core.commands.command import Command
from core.elements.element import Element
from core.instruction import Instruction
from tracewin_utils.line import DatLine


class Adjust(Command):
    """A dummy command."""

    is_implemented = False
    n_attributes = range(2, 8)

    def __init__(
        self, line: DatLine, dat_idx: int | None = None, **kwargs
    ) -> None:
        """Instantiate the object."""
        super().__init__(line, dat_idx, **kwargs)
        self.number = int(line.splitted[1])
        self.vth_variable = int(line.splitted[2])
        self.n_link = int(line.splitted[3]) if len(line.splitted) > 3 else 0
        self.min = float(line.splitted[4]) if len(line.splitted) > 4 else None
        self.max = float(line.splitted[5]) if len(line.splitted) > 5 else None
        self.start_step = (
            float(line.splitted[6]) if len(line.splitted) > 6 else None
        )
        self.k_n = float(line.splitted[7]) if len(line.splitted) > 7 else None

    @override
    def _args_to_line(
        self,
        number: int,
        vth_variable: int,
        n_link: int = 0,
        mini: float | None = None,
        maxi: float | None = None,
        start_step: float | None = None,
        k_n: float | None = None,
    ) -> str:
        """Create the :class:`.DatLine` corresponding to ``self`` object."""
        line = f"ADJUST {number} {vth_variable} {n_link}"
        for optional_variable in (mini, maxi, start_step, k_n):
            if optional_variable is None:
                return line
            line += " " + str(optional_variable)
        return line

    def set_influenced_elements(
        self, instructions: list[Instruction], **kwargs: float
    ) -> None:
        """Apply command to first :class:`.Element` that is found."""
        start = self.idx["dat_idx"] + 1
        indexes_between_this_cmd_and_element = (
            self._indexes_between_this_command_and(
                instructions[start:], Element
            )
        )
        self.influenced = indexes_between_this_cmd_and_element.stop
        return

    def apply(self, *args, **kwargs) -> list[Instruction]:
        """Do not apply anything."""
        raise NotImplementedError
