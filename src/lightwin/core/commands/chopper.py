"""Define a useless command to serve as place holder."""

import logging

from lightwin.core.commands.command import Command
from lightwin.core.instruction import Instruction
from lightwin.tracewin_utils.line import DatLine


class Chopper(Command):
    """Dummy class."""

    is_implemented = False
    n_attributes = 6

    def __init__(
        self, line: DatLine, dat_idx: int | None = None, **kwargs: str
    ) -> None:
        """Call the mother ``__init__`` method."""
        super().__init__(line, dat_idx)
        self.n_elements = int(line.splitted[1])
        self.u_v = float(line.splitted[2])
        self.d_mm = float(line.splitted[3])
        self.c_mm = float(line.splitted[4])
        self.p_axis = int(line.splitted[5])

    def set_influenced_elements(
        self, instructions: list[Instruction], **kwargs: float
    ) -> None:
        """Determine the index of the elements concerned by :func:`apply`."""
        start = self.idx["dat_idx"]
        stop = start + 1
        self.influenced = slice(start, stop)

    def apply(
        self, instructions: list[Instruction], **kwargs: float
    ) -> list[Instruction]:
        """Do nothing."""
        logging.error("Shift not implemented.")
        return instructions
