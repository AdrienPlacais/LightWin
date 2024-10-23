"""Define a master class for :class:`.Element` and :class:`.Command`.

.. todo::
    The ``line`` is edited to remove personalized name, weight and always have
    the same arguments at the same position. But after I shall re-add them with
    reinsert_optional_commands_in_line. This is very patchy and un-Pythonic.

"""

import logging
from abc import ABC
from collections.abc import Collection, MutableSequence
from typing import Self

from lightwin.tracewin_utils.line import DatLine


class Instruction(ABC):
    """An object corresponding to a line in a ``.dat`` file."""

    line: DatLine
    idx: dict[str, int]
    n_attributes: int | range | Collection
    is_implemented: bool

    def __init__(
        self,
        line: DatLine,
        dat_idx: int | None = None,
        **kwargs,
    ) -> None:
        """Instantiate corresponding line and line number in ``.dat`` file.

        Parameters
        ----------
        line : list[str]
            Line containing the instructions.
        dat_idx : int
            Position in the ``.dat``. Note that this index will vary if some
            instructions (empty lines, comments in particular) are removed from
            the dat content.

        """
        self.line = line
        if dat_idx is None:
            dat_idx = line.idx
        self._assert_correct_number_of_args(dat_idx)
        self.idx = {"dat_idx": dat_idx}

        self._personalized_name = line.personalized_name
        self._default_name: str

    def _assert_correct_number_of_args(self, idx: int) -> None:
        """Check if given number of arguments is ok."""
        if not self.is_implemented:
            return
        n_args = self.line.n_args
        if isinstance(self.n_attributes, int):
            assert n_args == self.n_attributes, (
                f"At line #{idx}, the number of arguments is {n_args} "
                f"instead of {self.n_attributes}. Full instruction:\n"
                f"{self.line}"
            )
        if isinstance(self.n_attributes, range | Collection):
            assert n_args in self.n_attributes, (
                f"At line #{idx}, the number of arguments is {n_args} "
                f"but should be in {self.n_attributes}. Full instruction:\n"
                f"{self.line}"
            )

    def __str__(self) -> str:
        """Give name of current command. Used by LW to identify elements."""
        return self.name

    def __repr__(self) -> str:
        """Give more information than __str__. Used for display only."""
        if self.name:
            f"{self.__class__.__name__:15s} {self.name}"
        return f"{self.__class__.__name__:15s} {self.line}"

    @property
    def name(self) -> str:
        """Give personal. name of instruction if exists, default otherwise."""
        if self._personalized_name:
            return self._personalized_name
        if hasattr(self, "_default_name"):
            return self._default_name
        return str(self.line)

    def to_line(self, *args, **kwargs) -> list[str]:
        """Convert the object back into a ``.dat`` line."""
        return self.line.splitted_full

    def increment_dat_position(self, increment: int = 1) -> None:
        """Increment dat index for when another instruction is inserted."""
        self.idx["dat_idx"] += increment
        self.line.idx += 1

    def insert_dat_line(
        self,
        *args,
        dat_filecontent: list[DatLine],
        previously_inserted: int = 0,
        **kwargs,
    ) -> None:
        """Insert the current object in the ``dat_filecontent`` object.

        Parameters
        ----------
        dat_filecontent : list[Collection[str]]
            The list of instructions, in the form of a list of lines.
        previously_inserted : int, optional
            Number of :class:`.Instruction` that were already inserted in the
            given ``dat_filecontent``.

        """
        index = self.line.idx + previously_inserted
        dat_filecontent.insert(index, self.line)

    def insert_line(
        self,
        *args,
        dat_filecontent: list[Collection[str]],
        previously_inserted: int = 0,
        **kwargs,
    ) -> None:
        """Insert the current object in the ``dat_filecontent`` object.

        Parameters
        ----------
        dat_filecontent : list[Collection[str]]
            The list of instructions, in the form of a list of lines.
        previously_inserted : int, optional
            Number of :class:`.Instruction` that were already inserted in the
            given ``dat_filecontent``.

        """
        index = self.idx["dat_idx"] + previously_inserted
        dat_filecontent.insert(index, self.to_line(*args, **kwargs))

    def insert_object(self, instructions: MutableSequence[Self]) -> None:
        """Insert current instruction in a list full of other instructions."""
        instructions.insert(self.idx["dat_idx"], self)
        for instruction in instructions[self.idx["dat_idx"] + 1 :]:
            instruction.increment_dat_position()

    @classmethod
    def from_args(cls, dat_idx: int, *args, **kwargs) -> Self:
        """Instantiate instruction from its arguments directly."""
        line = cls._args_to_line(*args, **kwargs)
        dat_line = DatLine(line, dat_idx)
        return cls(dat_line)

    @classmethod
    def _args_to_line(cls, *args, **kwargs) -> str:
        """Create the line of the dat file from arguments of the command."""
        raise NotImplementedError(
            "Must be overriden for specific instruction."
        )


class Dummy(Instruction):
    """An object corresponding to a non-implemented element or command."""

    is_implemented = False

    def __init__(
        self,
        line: DatLine,
        warning: bool = False,
        **kwargs,
    ) -> None:
        """Create the dummy object, raise a warning if necessary.

        Parameters
        ----------
        line : DatLine
            Arguments of the line in the ``.dat`` file.
        dat_idx : int
            Line number in the ``.dat`` file.
        warning : bool, optional
            To raise a warning when the element is not implemented. The default
            is False.

        """
        super().__init__(line, **kwargs)
        if warning:
            logging.warning(
                "A dummy element was added as the corresponding element or "
                "command is not implemented. If the BeamCalculator is not "
                "TraceWin, this may be a problem. In particular if the missing"
                " element has a length that is non-zero. You can disable this "
                "warning in tracewin_utils.dat_files._create"
                f"_element_n_command_objects. Line with a problem:\n"
                f"{self.line}"
            )


class Comment(Dummy):
    """An object corresponding to a comment."""

    def __init__(
        self, line: DatLine, dat_idx: int | None = None, **kwargs
    ) -> None:
        """Create the object, but never raise a warning.

        Parameters
        ----------
        line : list[str]
            Arguments of the line in the ``.dat`` file.
        dat_idx : int
            Line number in the ``.dat`` file.

        """
        super().__init__(line, warning=False, **kwargs)


class LineJump(Comment):
    """An object corresponding to an empty line. Basically a comment."""
