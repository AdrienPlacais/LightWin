"""Define functions to load, modify and create ``.dat`` structure files.

.. todo::
    Insert line skip at each section change in the output.dat

"""

import logging
from collections.abc import Callable, Collection, Container, Iterable, Sequence
from pathlib import Path
from pprint import pformat
from typing import Literal

from lightwin.core.commands.command import Command
from lightwin.core.elements.element import Element
from lightwin.core.instruction import Dummy, Instruction
from lightwin.tracewin_utils.line import DatLine


def dat_filecontent_from_file(
    dat_path: Path,
    *,
    keep: Literal["none", "comments", "all"] = "none",
    filter_func: Callable[[DatLine], bool] | None = None,
    instructions_to_insert: Collection[Instruction | DatLine] = (),
) -> list[DatLine]:
    """Load the dat file and convert it into a list of lines.

    Parameters
    ----------
    dat_path : pathlib.Path
        Filepath to the ``.dat`` file, as understood by TraceWin.
    keep : Literal["none", "comments", "all"], optional
        To determine which un-necessary lines in the dat file should be kept.
        The default is `'none'`.
    filter_func : Callable
        You can provide your own filters here. Takes precedence over ``keep``.
    instructions_to_insert : Collection[Instruction | DatLine], optional
        Some elements or commands that are not present in the ``.dat`` file but
        that you want to add. The default is an empty tuple.

    Returns
    -------
    dat_filecontent : list[DatLine]
        List containing all the lines of dat_path.

    """
    with open(dat_path, "r", encoding="utf-8") as file:
        dat_filecontent = [DatLine(line, idx) for idx, line in enumerate(file)]

    dat_filecontent = _filter_lines(dat_filecontent, keep, filter_func)

    if instructions_to_insert:
        _insert_instructions(dat_filecontent, instructions_to_insert)
    return dat_filecontent


def _filter_lines(
    dat_filecontent: Sequence[DatLine],
    keep: Literal["none", "comments", "all"] = "none",
    filter_func: Callable[[DatLine], bool] | None = None,
) -> list[DatLine]:
    """Remove some :class:`.DatLine` from ``dat_filecontent``.

    Parameters
    ----------
    dat_filecontent : Sequence[DatLine]
        Content loaded from the ``.dat`` file.
    keep : Literal["none", "comments", "all"], optional
        To determine which un-necessary lines in the dat file should be kept.
        The default is `'none'`.
    filter_func : Callable[[DatLine], bool], optional
        You can provide your own filters here. Takes precedence over ``keep``.

    Returns
    -------
    list[DatLine]
        Content of the ``.dat`` file without undesirable content.

    """
    if keep == "all":
        return list(dat_filecontent)

    if filter_func is None:
        filters = {
            "none": lambda x: x.line and x.line[0] != ";",
            "comments": lambda x: x.line,
            "all": lambda _: True,
        }
        filter_func = filters[keep]

    dat_filecontent = list(filter(filter_func, dat_filecontent))

    # Update index to keep it consistent
    for i, dat_line in enumerate(dat_filecontent):
        dat_line.idx = i
    return dat_filecontent


def _insert_instructions(
    dat_filecontent: list[DatLine],
    instructions_to_insert: Collection[Instruction | DatLine] = (),
) -> None:
    """Insert the desired instructions in the ``dat_filecontent``."""
    logging.info(
        "Will insert following instructions:\n"
        f"{pformat(instructions_to_insert, width=120)}"
    )
    for i, instruction in enumerate(instructions_to_insert):
        if isinstance(instruction, DatLine):
            dat_filecontent.insert(instruction.idx + i, instruction)
            continue

        instruction.insert_dat_line(
            dat_filecontent=dat_filecontent, previously_inserted=i
        )


def dat_filecontent_from_smaller_list_of_elements(
    original_instructions: Sequence[Instruction],
    elts: Collection[Element],
) -> tuple[list[DatLine], list[Instruction]]:
    """
    Create a ``.dat`` with only elements of ``elts`` (and concerned commands).

    Properties of the FIELD_MAP, i.e. amplitude and phase, remain untouched.

    """
    indexes_to_keep = [elt.get("dat_idx", to_numpy=False) for elt in elts]
    last_index = indexes_to_keep[-1] + 1

    new_dat_filecontent: list[DatLine] = []
    new_instructions: list[Instruction] = []
    for instruction in original_instructions[:last_index]:
        if not (
            _is_needed_element(instruction, indexes_to_keep)
            or _is_useful_command(instruction, indexes_to_keep)
        ):
            continue

        new_dat_filecontent.append(instruction.line)
        new_instructions.append(instruction)

    end = original_instructions[-1]
    new_dat_filecontent.append(end.line)
    new_instructions.append(end)
    return new_dat_filecontent, new_instructions


def _is_needed_element(
    instruction: Instruction, indexes_to_keep: Container[int]
) -> bool:
    """Tell if the instruction is an element that we must keep."""
    if not isinstance(instruction, Element | Dummy):
        return False
    if instruction.idx["dat_idx"] in indexes_to_keep:
        return True
    return False


def _is_useful_command(
    instruction: Instruction, indexes_to_keep: Iterable[int]
) -> bool:
    """Tell if the current command has an influence on our elements."""
    if not isinstance(instruction, Command):
        return False
    if instruction.concerns_one_of(indexes_to_keep):
        return True
    return False


def export_dat_filecontent(
    dat_filecontent: Collection[Collection[str]] | Collection[DatLine],
    dat_path: Path,
) -> None:
    """Save the content of the updated dat to a ``.dat``.

    Parameters
    ----------
    dat_filecontent : Collection[Collection[str]]
        Content of the ``.dat``, line per line, word per word.
    dat_path : pathlib.Path
        Where to save the ``.dat``.

    """
    with open(dat_path, "w", encoding="utf-8") as file:
        for line in dat_filecontent:
            if isinstance(line, DatLine):
                file.write(line.line + "\n")
                continue
            file.write(" ".join(line) + "\n")
    logging.debug(f"New dat saved in {dat_path}.")
