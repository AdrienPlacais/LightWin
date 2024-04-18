#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Define holds function to load, modify and create .dat structure files.

.. todo::
    Insert line skip at each section change in the output.dat

Non-exhaustive list of non implemented commands:
    'SPACE_CHARGE_COMP',
    'SET_SYNC_PHASE',
    'STEERER',
    'ADJUST',
    'ADJUST_STEERER',
    'ADJUST_STEERER_BX',
    'ADJUST_STEERER_BY',
    'SET_ADV',

"""
import logging
from pathlib import Path

from core.commands.command import Command
from core.elements.element import Element
from core.instruction import Dummy, Instruction


def dat_filecontent_from_smaller_list_of_elements(
    original_instructions: list[Instruction],
    elts: list[Element],
) -> tuple[list[list[str]], list[Instruction]]:
    """
    Create a ``.dat`` with only elements of ``elts`` (and concerned commands).

    Properties of the FIELD_MAP, i.e. amplitude and phase, remain untouched, as
    it is the job of :func:`update_field_maps_in_dat`.

    """
    indexes_to_keep = [elt.get("dat_idx", to_numpy=False) for elt in elts]
    last_index = indexes_to_keep[-1] + 1

    new_dat_filecontent: list[list[str]] = []
    new_instructions: list[Instruction] = []
    for instruction in original_instructions[:last_index]:
        element_to_keep = (
            isinstance(instruction, Element | Dummy)
            and instruction.idx["dat_idx"] in indexes_to_keep
        )

        useful_command = isinstance(
            instruction, Command
        ) and instruction.concerns_one_of(indexes_to_keep)

        if not (element_to_keep or useful_command):
            continue

        new_dat_filecontent.append(instruction.line)
        new_instructions.append(instruction)

    end = original_instructions[-1]
    new_dat_filecontent.append(end.line)
    new_instructions.append(end)
    return new_dat_filecontent, new_instructions


def save_dat_filecontent_to_dat(
    dat_content: list[list[str]], dat_path: Path
) -> None:
    """Save the content of the updated dat to a `.dat`."""
    with open(dat_path, "w", encoding="utf-8") as file:
        for line in dat_content:
            file.write(" ".join(line) + "\n")
    logging.info(f"New dat saved in {dat_path}.")
