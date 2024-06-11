"""Define a command to superpose longitudinal field maps.

.. note::
    As for now, the transverse motion in field maps is not implemented, even
    with :class:`.Envelope3D`.

"""

import logging
from collections.abc import Sequence

from core.commands.command import Command
from core.commands.dummy_command import DummyCommand
from core.electric_field import RfField
from core.elements.dummy import DummyElement
from core.elements.element import Element
from core.elements.field_maps.field_map import FieldMap
from core.elements.field_maps.superposed_field_map import (
    SuperposedFieldMap,
    SuperposedPlaceHolderCmd,
    SuperposedPlaceHolderElt,
)
from core.instruction import Instruction
from tracewin_utils.line import DatLine


class SuperposeMap(Command):
    """Command to merge several field maps.

    Attributes
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
        Only the first of the ``SUPERPOSE_MAP`` command will have the entire
        valid range of elements.

        """
        start = self.idx["dat_idx"] - 1
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
        # instructions_to_merge = list(
        #     filter(
        #         lambda x: isinstance(x, (Element, SuperposeMap)),
        #         instructions[self.influenced],
        #     )
        # )
        instructions_to_merge = instructions[self.influenced]
        total_length = self._total_length(instructions_to_merge)

        # instructions[self.influenced], number_of_superposed = (
        #     self._update_class(instructions_to_merge, total_length)
        # )
        new_instructions = self._generate_new_instructions(
            total_length, instructions_to_merge
        )

        instructions[self.influenced] = new_instructions
        number_of_superposed = int(len(new_instructions) / 2)

        elts_after_self = list(
            filter(
                lambda elt: isinstance(elt, Element),
                instructions[self.idx["dat_idx"] + 1 :],
            )
        )
        self._decrement_lattice_indexes(elts_after_self, number_of_superposed)

        instructions[self.influenced] = instructions_to_merge
        return instructions

    def _total_length(self, instructions_to_merge: list[Instruction]) -> float:
        """Compute length of the superposed field maps."""
        z_max = 0.0
        z_0 = None
        for instruction in instructions_to_merge:
            if isinstance(instruction, SuperposeMap):
                z_0 = instruction.z_0
                continue

            if isinstance(instruction, FieldMap):
                if z_0 is None:
                    logging.error(
                        "There is no SUPERPOSE_MAP for current FIELD_MAP.\n"
                        f"{instruction.line}"
                    )
                    z_0 = 0.0

                z_1 = z_0 + instruction.length_m
                if z_1 > z_max:
                    z_max = z_1
                z_0 = None
        return z_max

    def _generate_new_instructions(
        self, total_length: float, instructions_to_merge: list[Instruction]
    ) -> list[Instruction]:
        """Create the instructions replacing superpose and field maps."""
        indexes = [x.idx["dat_idx"] for x in instructions_to_merge]

        new_instructions: list[Instruction] = [
            SuperposedFieldMap.from_field_maps(
                instructions_to_merge,
                dat_idx=indexes.pop(0),
                total_length=total_length,
            )
        ]

        for instruction, dat_idx in zip(instructions_to_merge[1:], indexes):
            dat_line = DatLine("SUPERPOSE_PLACE_HOLDER 0", dat_idx)
            if isinstance(instruction, Element):
                new_instructions.append(SuperposedPlaceHolderElt(dat_line))
                continue
            new_instructions.append(SuperposedPlaceHolderCmd(dat_line))
        return new_instructions

    def _update_class(
        self, instructions_to_merge: list[Instruction], total_length: float
    ) -> tuple[list[Instruction], int]:
        """Replace elements and commands by dummies, except first field map."""
        number_of_superposed = 0
        superposed_field_map_is_already_inserted = False
        for i, instruction in enumerate(instructions_to_merge):
            args = (instruction.line, instruction.idx["dat_idx"])

            if isinstance(instruction, Command):
                instructions_to_merge[i] = DummyCommand(*args)
                continue

            if superposed_field_map_is_already_inserted:
                instructions_to_merge[i] = DummyElement(*args)
                instructions_to_merge[i].nature = "SUPERPOSED_FIELD_MAP"
                instructions_to_merge[i].rf_field = RfField()
                number_of_superposed += 1
                continue

            instructions_to_merge[i] = SuperposedFieldMap(
                *args, total_length=total_length
            )
            instructions_to_merge[i].nature = "SUPERPOSED_FIELD_MAP"
            instructions_to_merge[i].rf_field = RfField()
            superposed_field_map_is_already_inserted = True
        return instructions_to_merge, number_of_superposed

    def _decrement_lattice_indexes(
        self, elts_after_self: Sequence[Element], number_of_superposed: int
    ) -> None:
        """Decrement some lattice numbers to take removed elts into account.

        .. todo::
            Check if this still works, as lattice and idx_in_lattice are now
            initialized with -1 instead of None.

        """
        for i, elt in enumerate(elts_after_self):
            if elt.idx["lattice"] < 0:
                continue

            if not elt.increment_lattice_idx:
                continue

            elt.idx["idx_in_lattice"] -= number_of_superposed - 1

            if elt.idx["idx_in_lattice"] < 0:
                previous_elt = elts_after_self[i - 1]
                elt.idx["idx_in_lattice"] = (
                    previous_elt.idx["idx_in_lattice"] + 1
                )
