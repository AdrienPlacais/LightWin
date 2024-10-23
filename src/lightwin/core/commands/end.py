"""Define a command to indicate end of the linac."""

from lightwin.core.commands.command import Command
from lightwin.core.instruction import Instruction
from lightwin.tracewin_utils.line import DatLine


class End(Command):
    """The end of the linac."""

    is_implemented = True
    n_attributes = 0

    def __init__(
        self, line: DatLine, dat_idx: int | None = None, **kwargs: str
    ) -> None:
        """Call mother ``__init__``."""
        super().__init__(line, dat_idx)

    def set_influenced_elements(self, *args, **kwargs: float) -> None:
        """Determine the index of the element concerned by :func:`apply`."""
        start = 0
        stop = self.idx["dat_idx"] + 1
        self.influenced = slice(start, stop)

    def apply(
        self, instructions: list[Instruction], **kwargs: float
    ) -> list[Instruction]:
        """Remove everything in ``instructions`` after this object."""
        return instructions[self.influenced]
