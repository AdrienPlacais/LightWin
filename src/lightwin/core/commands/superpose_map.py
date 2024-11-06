"""Define a command to superpose longitudinal field maps.

.. note::
    As for now, the transverse motion in field maps is not implemented, even
    with :class:`.Envelope3D`.

"""

import logging
from collections.abc import Collection, Sequence

from lightwin.core.commands.command import Command
from lightwin.core.elements.element import Element
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.elements.field_maps.superposed_field_map import (
    SuperposedFieldMap,
    SuperposedPlaceHolderCmd,
    SuperposedPlaceHolderElt,
)
from lightwin.core.instruction import Comment, Instruction
from lightwin.tracewin_utils.line import DatLine


class SuperposeMap(Command):
    """Command to merge several field maps.

    Parameters
    ----------
    z_0 : float
        Position at which the next field map should be inserted.

    """

    is_implemented = True
    n_attributes = (1, 6)

    def __init__(
        self, line: DatLine, dat_idx: int | None = None, **kwargs: str
    ) -> None:
        """Save position as attribute."""
        super().__init__(line, dat_idx)
        self.z_0 = float(line.splitted[1]) * 1e-3

    def set_influenced_elements(
        self, instructions: list[Instruction], **kwargs: float
    ) -> None:
        """Determine the index of the elements concerned by :func:`apply`.

        It spans from the current ``SUPERPOSE_MAP`` command, up to the next
        element that is not a field map. It allows to consider situations where
        we field_map is not directly after the ``SUPERPOSE_MAP`` command.

        Example
        -------
        ```
        SUPERPOSE_MAP
        STEERER
        FIELD_MAP
        ```

        .. warning::
            Only the first of the ``SUPERPOSE_MAP`` command will have the
            entire valid range of elements.

        """
        start = self.idx["dat_idx"]
        next_element_but_not_field_map = list(
            filter(
                lambda elt: (
                    isinstance(elt, Element) and not isinstance(elt, FieldMap)
                ),
                instructions[self.idx["dat_idx"] :],
            )
        )[0]
        stop = next_element_but_not_field_map.idx["dat_idx"]
        self.influenced = slice(start, stop)

    def apply(
        self, instructions: list[Instruction], **kwargs: float
    ) -> list[Instruction]:
        """Apply the command.

        Only the first :class:`SuperposeMap` of a bunch of field maps should be
        applied. In order to avoid messing with indexes in the ``.dat`` file,
        all Commands are replaced by dummy commands. All field maps are
        replaced by dummy elements of length 0, except the first field_map that
        is replaced by a SuperposedFieldMap.

        """
        instructions_to_merge = instructions[self.influenced]
        total_length = self._total_length_m(instructions_to_merge)

        new_instructions = self._generate_new_instructions(
            total_length, instructions_to_merge
        )

        instructions[self.influenced] = new_instructions
        number_of_superposed = int(len(new_instructions) / 2)

        elts_after_self = list(
            filter(
                lambda elt: isinstance(elt, Element),
                # instructions[self.idx["dat_idx"] + 1 :],
                instructions[new_instructions[-1].idx["dat_idx"] + 1 :],
            )
        )
        self._re_set_indexes(elts_after_self, number_of_superposed)

        # instructions[self.influenced] = instructions_to_merge
        return instructions

    def _total_length_m(
        self, instructions_to_merge: list[Instruction]
    ) -> float:
        """Compute length of the superposed field maps."""
        z_max = 0.0
        z_0 = None
        for instruction in instructions_to_merge:
            if isinstance(instruction, SuperposeMap):
                z_0 = instruction.z_0
                continue

            if isinstance(field_map := instruction, FieldMap):
                if z_0 is None:
                    logging.error(
                        "There is no SUPERPOSE_MAP for current FIELD_MAP.\n"
                        f"{instruction.line}"
                    )
                    z_0 = 0.0
                field_map.z_0 = z_0

                z_1 = z_0 + field_map.length_m
                if z_1 > z_max:
                    z_max = z_1
                z_0 = None
        return z_max

    def _generate_new_instructions(
        self, total_length_m: float, instructions_to_merge: list[Instruction]
    ) -> list[Instruction]:
        """Create the instructions replacing superpose and field maps."""
        indexes = [x.idx["dat_idx"] for x in instructions_to_merge]

        superposed = SuperposedFieldMap.from_field_maps(
            instructions_to_merge,
            dat_idx=indexes.pop(0),
            total_length_m=total_length_m,
            starting_positions=_starting_positions(instructions_to_merge),
        )
        idx_in_lattice = superposed.idx["idx_in_lattice"]
        lattice = superposed.idx["lattice"]
        section = superposed.idx["section"]

        new_instructions: list[Instruction] = [superposed]
        for instruction, dat_idx in zip(instructions_to_merge[1:], indexes):
            if isinstance(instruction, Comment):
                new_instructions.append(instruction)
                continue

            dat_line = DatLine(
                "SUPERPOSED_MAP_PLACE_HOLDER 0",
                dat_idx,
                original_line=instruction.line.original_line,
            )
            if isinstance(instruction, Element):
                new_instructions.append(
                    SuperposedPlaceHolderElt(
                        dat_line,
                        idx_in_lattice=idx_in_lattice,
                        lattice=lattice,
                        section=section,
                    )
                )
                continue
            new_instructions.append(SuperposedPlaceHolderCmd(dat_line))
        return new_instructions

    def _re_set_indexes(
        self,
        elts_after_self: Sequence[Element],
        number_of_superposed: int,
    ) -> None:
        """Decrement lattice numbers to take merged elements into account.

        ..todo::
            Not robust...

        """
        elements_reduced = number_of_superposed - 1
        for i, elt in enumerate(elts_after_self):
            if elt.idx["lattice"] < 0:
                continue

            if not elt.increment_lattice_idx:
                continue

            elt.idx["idx_in_lattice"] -= elements_reduced

            if elt.idx["idx_in_lattice"] < 0:
                if i == 0:
                    raise IOError(
                        "Detected a SUPERPOSE_MAP at the end of a lattice. Not"
                        "supported for now."
                    )

                # Recompute the number of elements per lattice
                previous_element = elts_after_self[i - 1]

                current_section = elt.idx["section"]
                previous_section = previous_element.idx["section"]
                if current_section != previous_section:
                    raise NotImplementedError(
                        "Detected a Section change around a SUPERPOSE_MAP."
                        " Not supported for now."
                    )

                # This will work only if previous element is the last of its
                # lattice. Which may not always be true...
                number_of_elements_in_lattice = previous_element.idx[
                    "idx_in_lattice"
                ]

                elt.idx["idx_in_lattice"] += number_of_elements_in_lattice
                elt.idx["lattice"] -= 1


def _starting_positions(
    instructions_to_merge: Collection[Instruction],
) -> list[float]:
    """Get the starting position of every field map."""
    starting_positions = [
        x.z_0 for x in instructions_to_merge if isinstance(x, SuperposeMap)
    ]
    return starting_positions
