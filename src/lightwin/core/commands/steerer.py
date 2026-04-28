"""Define a useless command to serve as place holder."""

from typing import Literal, override

from lightwin.core.commands.command import Command
from lightwin.core.elements.element import Element
from lightwin.core.instruction import Instruction
from lightwin.tracewin_utils.line import DatLine

STEERER_TYPES_T = Literal["magnetic", "electric"]


class Steerer(Command):
    """Dummy class."""

    is_implemented = True
    n_attributes = range(2, 7)

    def __init__(
        self, line: DatLine, dat_idx: int | None = None, **kwargs: str
    ) -> None:
        """Call the mother ``__init__`` method."""
        super().__init__(line, dat_idx)
        splitted = line.splitted
        n_args = len(splitted)

        self.field_x = float(splitted[1])
        self.field_y = float(splitted[2])
        self.field_max = float(splitted[3]) if n_args > 3 else 0

        self.type: STEERER_TYPES_T
        self._type = int(splitted[4]) if n_args > 4 else 0
        if self._type == 0:
            self.type = "magnetic"
        elif self._type == 1:
            self.type = "electric"
        else:
            raise ValueError(
                "The 4th argument of Steerer should be 0 or 1. Got "
                f"{self._type}. Complete line is\n{line}"
            )

        self.coef_1 = (
            float(splitted[5])
            if len(splitted) > 5 and self.type == "magnetic"
            else None
        )
        self.coef_2 = (
            float(splitted[6])
            if len(splitted) > 6 and self.type == "magnetic"
            else None
        )

    def set_influenced_elements(
        self, instructions: list[Instruction], **kwargs: float
    ) -> None:
        """Determine the index of the elements concerned by :func:`apply`."""
        next_element = list(
            filter(
                lambda elt: isinstance(elt, Element),
                instructions[self.idx["dat_idx"] :],
            )
        )[0]
        start = next_element.idx["dat_idx"]
        stop = start + 1
        self.influenced = slice(start, stop)

    @classmethod
    @override
    def _args_to_line(
        cls,
        field_x: float = 0,
        field_y: float = 0,
        field_maxi: float | None = None,
        field_type: STEERER_TYPES_T | Literal[0, 1] | None = None,
        coef_1: float | None = None,
        coef_2: float | None = None,
        personalized_name: str | None = None,
    ) -> str:
        """Create the :class:`.DatLine` corresponding to ``self`` object."""
        line = f"STEERER {field_x} {field_y}"

        if field_type == "electric":
            field_type = 1
        elif field_type == "magnetic":
            field_type = 0

        if personalized_name is not None:
            line = f"{personalized_name} : {line}"

        for optional_variable in (field_maxi, field_type, coef_1, coef_2):
            if optional_variable is None:
                return line
            line += " " + str(optional_variable)

        return line
