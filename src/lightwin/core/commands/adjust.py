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

from lightwin.core.commands.command import Command
from lightwin.core.commands.steerer import Steerer
from lightwin.core.elements.element import Element
from lightwin.core.instruction import Instruction
from lightwin.tracewin_utils.line import DatLine


class Adjust(Command):
    """A dummy command."""

    is_implemented = False
    n_attributes = range(2, 8)

    def __init__(
        self, line: DatLine, dat_idx: int | None = None, **kwargs
    ) -> None:
        """Instantiate the object."""
        super().__init__(line, dat_idx, **kwargs)
        splitted = line.splitted
        n_args = len(splitted)
        self.number = int(splitted[1])
        self.vth_variable = int(splitted[2])
        self.n_link = int(splitted[3]) if n_args > 3 else 0
        self.min = float(splitted[4]) if n_args > 4 else None
        self.max = float(splitted[5]) if n_args > 5 else None
        self.start_step = float(splitted[6]) if n_args > 6 else None
        self.k_n = float(splitted[7]) if n_args > 7 else None

    @classmethod
    @override
    def _args_to_line(
        cls,
        number: int,
        vth_variable: int,
        n_link: int = 0,
        mini: float | None = None,
        maxi: float | None = None,
        start_step: float | None = None,
        k_n: float | None = None,
    ) -> str:
        """Create the :class:`.DatLine` corresponding to ``self`` object.

        Parameters
        ----------
        number :
            Number of the diagnostics this command should be associated to.
        vth_variable :
            Position of the variable to adjust.
        n_link :
            Link this command with other ``ADJUST`` with the same ``n_link``,
            if different from 0.
        mini :
            Minimum variable value.
        maxi :
            Maximum variable value.
        start_step :
            Step size of the first iteration.
        k_n :
            Corrective coefficient when two variables are linked.

        """
        line = f"ADJUST {number} {vth_variable} {n_link}"
        for optional_variable in (mini, maxi, start_step, k_n):
            if optional_variable is None:
                return line
            line += " " + str(optional_variable)
        return line

    def set_influenced_elements(
        self, instructions: list[Instruction], **kwargs: float
    ) -> None:
        r"""Apply command to the first |E| that is found.

        Potential :class:`.Command`\s between current object and the influenced
        |E| are discarded.

        """
        start = self.idx["dat_idx"] + 1
        indexes_between_this_cmd_and_element = (
            self._indexes_between_this_command_and(
                instructions[start:], Element
            )
        )
        idx_element = indexes_between_this_cmd_and_element.stop
        self.influenced = slice(idx_element, idx_element + 1)
        return

    def apply(self, *args, **kwargs) -> list[Instruction]:
        """Do not apply anything."""
        raise NotImplementedError


class AdjustSteerer(Command):
    """Command to adjust steerers."""

    is_implemented = True
    n_attributes = range(1, 5)
    _command_in_tw = "ADJUST_STEERER"

    def __init__(
        self, line: DatLine, dat_idx: int | None = None, **kwargs
    ) -> None:
        super().__init__(line, dat_idx, **kwargs)
        self.number = int(line.splitted[1])
        self.min = float(line.splitted[2]) if len(line.splitted) > 5 else None
        self.max = float(line.splitted[3]) if len(line.splitted) > 5 else None
        self.first_step = (
            float(line.splitted[4]) if len(line.splitted) > 6 else None
        )

    @classmethod
    @override
    def _args_to_line(
        cls,
        number: int,
        mini: float = 0,
        maxi: float = 0,
        first_step: float = 0,
        personalized_name: str | None = None,
    ) -> str:
        """Create the :class:`.DatLine` corresponding to ``self`` object.

        Parameters
        ----------
        number :
            Number of the diagnostics this command should be associated to.
        mini :
            Minimum variable value.
        maxi :
            Maximum variable value.
        start_step :
        personalized_name :
            Name.

        """
        line = f"{cls._command_in_tw} {number} {mini} {maxi} {first_step}"
        if personalized_name is not None:
            line = f"{personalized_name} : {line}"
        return line

    def set_influenced_elements(
        self, instructions: list[Instruction], **kwargs: float
    ) -> None:
        r"""Apply command to the first :class:`.Steerer` that is found.

        Potential :class:`.Command`\s between current object and the influenced
        :class:`.Steerer` are discarded.

        """
        start = self.idx["dat_idx"] + 1
        indexes_between_this_cmd_and_element = (
            self._indexes_between_this_command_and(
                instructions[start:], Steerer
            )
        )
        idx_element = indexes_between_this_cmd_and_element.stop
        self.influenced = slice(idx_element, idx_element + 1)
        return


class AdjustSteererBx(AdjustSteerer):
    _command_in_tw = "ADJUST_STEERER_BX"


class AdjustSteererBy(AdjustSteerer):
    _command_in_tw = "ADJUST_STEERER_BY"
