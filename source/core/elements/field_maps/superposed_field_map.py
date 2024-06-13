"""Define a :class:`SuperposedFieldMap`.

.. note::
    The initialisation of this class is particular, as it does not correspond
    to a specific line of the ``.dat`` file.

.. todo::
    Could be cleaned and simplified.

"""

import logging
from collections.abc import Collection
from typing import Self, override

from core.commands.dummy_command import DummyCommand
from core.elements.dummy import DummyElement
from core.elements.element import Element
from core.elements.field_maps.cavity_settings import CavitySettings
from core.elements.field_maps.field_map import FieldMap
from core.em_fields.rf_field import RfField
from core.instruction import Instruction
from tracewin_utils.line import DatLine


class SuperposedFieldMap(Element):
    """A single element holding several field maps.

    We override its type to make Python believe it is a :class:`.FieldMap`,
    while is is just an :class:`.Element`. So take care of keeping their
    methods consistent!

    .. todo::
        Remove idx in lattice, lattice, section arguments. can take this from
        new attribute: ``field_maps``.

    """

    is_implemented = True
    n_attributes = range(0, 100)

    def __init__(
        self,
        line: DatLine,
        cavities_settings: Collection[CavitySettings],
        is_accelerating: bool,
        dat_idx: int,
        idx_in_lattice: int,
        lattice: int,
        section: int,
        field_maps: Collection[FieldMap],
        rf_fields: Collection[RfField],
        **kwargs,
    ) -> None:
        """Save length of the superposed field maps."""
        super().__init__(
            line,
            dat_idx=dat_idx,
            idx_in_lattice=idx_in_lattice,
            lattice=lattice,
            section=section,
            **kwargs,
        )
        self.field_maps = list(field_maps)

        # self.geometry: int        # useless
        # self.length_m: float      # already set by super
        # self.aperture_flag: int   # useless
        self.cavities_settings = list(cavities_settings)

        self.rf_fields = list(rf_fields)
        self._can_be_retuned: bool = False

        self._is_accelerating = is_accelerating

    @property
    def __class__(self) -> type:  # type: ignore
        """Override the default type.

        ``isinstance(superposed_field_map, some_type)`` will return ``True``
        both with ``some_type = SuperposedFieldMap`` and ``FieldMap``.

        """
        return FieldMap

    @classmethod
    def from_field_maps(
        cls,
        field_maps_n_superpose: Collection[Instruction],
        dat_idx: int,
        total_length: float,
        starting_positions: Collection[float],
    ) -> Self:
        """Instantiate object from several field maps.

        This is the only way this object should be instantiated; called by
        :class:`.SuperposeMap`.

        """
        field_maps = [
            x for x in field_maps_n_superpose if isinstance(x, FieldMap)
        ]
        args = cls._extract_args_from_field_maps(field_maps)
        cavities_settings, rf_fields, is_accelerating = args

        for rf_field, starting_position in zip(
            rf_fields, starting_positions, strict=True
        ):
            rf_field.starting_position = starting_position

        # original_lines = [x.line.line for x in field_maps_n_superpose]
        idx_in_lattice = field_maps[0].idx["idx_in_lattice"]
        lattice = field_maps[0].idx["lattice"]
        section = field_maps[0].idx["section"]

        return cls.from_args(
            dat_idx=dat_idx,
            total_length=total_length,
            cavities_settings=cavities_settings,
            rf_fields=rf_fields,
            is_accelerating=is_accelerating,
            idx_in_lattice=idx_in_lattice,
            lattice=lattice,
            section=section,
            field_maps=field_maps,
        )

    @classmethod
    def from_args(
        cls, dat_idx: int, total_length: float, *args, **kwargs
    ) -> Self:
        """Insantiate object from his properties."""
        line = cls._args_to_line(total_length)
        dat_line = DatLine(line, dat_idx)
        return cls(
            dat_line,
            dat_idx=dat_idx,
            total_length=total_length,
            *args,
            **kwargs,
        )

    @classmethod
    def _args_to_line(cls, total_length: float, *args, **kwargs) -> str:
        """Generate hypothetical line."""
        return f"SUPERPOSED_FIELD_MAP {total_length}"

    @classmethod
    def _extract_args_from_field_maps(
        cls, field_maps: Collection[FieldMap]
    ) -> tuple[list[CavitySettings], list[RfField], bool]:
        """Go over the field maps to gather essential arguments."""
        cavity_settings = [
            field_map.cavity_settings for field_map in field_maps
        ]
        rf_fields = [field_map.rf_field for field_map in field_maps]

        are_accelerating = [x.is_accelerating for x in field_maps]
        is_accelerating = any(are_accelerating)
        return (
            cavity_settings,
            rf_fields,
            is_accelerating,
        )

    @property
    def status(self) -> str:
        """Tell that everything is working, always (for now)."""
        return "nominal"

    @property
    @override
    def is_accelerating(self) -> bool:
        """Indicate if this element has a longitudinal effect."""
        return self._is_accelerating

    @property
    @override
    def can_be_retuned(self) -> bool:
        """Tell if we can modify the element's tuning."""
        return False

    @can_be_retuned.setter
    @override
    def can_be_retuned(self, value: bool) -> None:
        """Forbid this cavity from being retuned (or re-allow it)."""
        if value:
            logging.critical(
                "Trying to allow a SuperposedFieldMap to be retuned."
            )
        self._can_be_retuned = value

    def set_full_path(self, *args, **kwargs) -> None:
        """Raise an error."""
        raise NotImplementedError

    def to_line(self, *args, **kwargs):
        """Convert the object back into a line in the ``.dat`` file."""
        logging.warning("Calling the to_line for superpose")
        return super().to_line(*args, **kwargs)


class SuperposedPlaceHolderElt(DummyElement):
    """Inserted in place of field maps and superpose map commands."""

    increment_lattice_idx = False

    def __init__(
        self,
        line: DatLine,
        idx_in_lattice: int,
        lattice: int,
        dat_idx: int | None = None,
        **kwargs,
    ) -> None:
        """Instantiate object, with lattice information."""
        super().__init__(
            line,
            dat_idx,
            idx_in_lattice=idx_in_lattice,
            lattice=lattice,
            **kwargs,
        )


class SuperposedPlaceHolderCmd(DummyCommand):
    """Inserted in place of field maps and superpose map commands."""
