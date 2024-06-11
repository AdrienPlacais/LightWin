"""Define a :class:`SuperposedFieldMap`.

.. note::
    The initialisation of this class is particular, as it does not correspond
    to a specific line of the ``.dat`` file.

"""

import logging
from collections.abc import Collection
from pathlib import Path
from typing import Self, override

from core.commands.dummy_command import DummyCommand
from core.electric_field import NewRfField
from core.elements.dummy import DummyElement
from core.elements.element import Element
from core.elements.field_maps.cavity_settings import CavitySettings
from core.elements.field_maps.field_map import FieldMap
from core.instruction import Instruction
from tracewin_utils.line import DatLine


class SuperposedFieldMap(Element):
    """A single element holding several field maps.

    We override its type to make Python believe it is a :class:`.FieldMap`,
    while is is just an :class:`.Element`. So take care of keeping their
    methods consistent!

    """

    is_implemented = True
    n_attributes = range(0, 100)

    def __init__(
        self,
        line: DatLine,
        cavities_settings: Collection[CavitySettings],
        field_map_file_names: Collection[Path],
        is_accelerating: bool,
        dat_idx: int | None = None,
        **kwargs: str,
    ) -> None:
        """Save length of the superposed field maps."""
        super().__init__(line, dat_idx=dat_idx, **kwargs)

        # self.geometry: int        # useless
        # self.length_m: float      # already set by super
        # self.aperture_flag: int   # useless
        self.cavities_settings = list(cavities_settings)

        self.field_map_file_names = field_map_file_names

        self.new_rf_fields: list[NewRfField]
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
    ) -> Self:
        """Instantiate object from several field maps.

        This is the only way this object should be instantiated; called by
        :class:`.SuperposeMap`.

        """
        field_maps = [
            x for x in field_maps_n_superpose if isinstance(x, FieldMap)
        ]
        args = cls._extract_args_from_field_maps(field_maps)
        cavity_settings, field_map_file_names, rf_fields, is_accelerating = (
            args
        )

        # original_lines = [x.line.line for x in field_maps_n_superpose]

        return cls.from_args(
            dat_idx,
            total_length,
            cavity_settings=cavity_settings,
            field_map_file_names=field_map_file_names,
            rf_fields=rf_fields,
            is_accelerating=is_accelerating,
        )

    @classmethod
    def from_args(
        cls, dat_idx: int, total_length: float, *args, **kwargs
    ) -> Self:
        """Insantiate object from his properties."""
        line = cls._args_to_line(total_length)
        dat_line = DatLine(line, dat_idx)
        return cls(dat_line, *args, **kwargs)

    @classmethod
    def _args_to_line(cls, total_length: float, *args, **kwargs) -> str:
        """Generate hypothetical line."""
        return f"SUPERPOSED_PLACEHOLDER {total_length}"

    @classmethod
    def _extract_args_from_field_maps(
        cls, field_maps: Collection[FieldMap]
    ) -> tuple[list[CavitySettings], list[Path], list[NewRfField], bool]:
        """Go over the field maps to gather essential arguments."""
        cavity_settings = [
            field_map.cavity_settings for field_map in field_maps
        ]
        field_map_file_names = [
            field_map.field_map_file_name for field_map in field_maps
        ]
        rf_fields = [field_map.new_rf_field for field_map in field_maps]

        are_accelerating = [x.is_accelerating for x in field_maps]
        is_accelerating = any(are_accelerating)
        return (
            cavity_settings,
            field_map_file_names,
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


class SuperposedPlaceHolderCmd(DummyCommand):
    """Inserted in place of field maps and superpose map commands."""
