"""Define a :class:`SuperposedFieldMap`.

.. note::
    The initialisation of this class is particular, as it does not correspond
    to a specific line of the ``.dat`` file.

"""

from collections.abc import Collection
from pathlib import Path
from typing import Self

from core.commands.dummy_command import DummyCommand
from core.elements.dummy import DummyElement
from core.elements.field_maps.cavity_settings import CavitySettings
from core.elements.field_maps.field_map import FieldMap
from core.instruction import Instruction
from tracewin_utils.line import DatLine


class SuperposedFieldMap(FieldMap):
    """A single element holding several field maps."""

    is_implemented = True
    n_attributes = range(0, 100)

    def __init__(
        self,
        line: DatLine,
        default_field_map_folder: Path,
        cavity_settings: CavitySettings,
        dat_idx: int | None = None,
        **kwargs: str,
    ) -> None:
        """Save length of the superposed field maps."""
        super().__init__(
            line,
            default_field_map_folder,
            cavity_settings,
            dat_idx=dat_idx,
            **kwargs,
        )
        self.length_m = total_length

        self.field_map_file_names: list[Path]
        self.field_maps_settings: list[CavitySettings]

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
        return cls.from_args(dat_idx, total_length)

    @classmethod
    def from_args(cls, dat_idx: int, total_length: float) -> Self:
        """Insantiate object from his properties."""
        line = cls._args_to_line(total_length)
        dat_line = DatLine(line, dat_idx)
        return cls(dat_line)

    @classmethod
    def _args_to_line(
        cls, total_length: float, cavity_settings: CavitySettings, **kwargs
    ) -> str:
        """Generate hypothetical line."""
        geometry = -1
        aperture_flag = 0

        return f"SUPERPOSED_PLACEHOLDER {total_length}"

    @property
    def is_accelerating(self) -> bool:
        """Indicate that this element cannot accelerate."""
        return False


class SuperposedPlaceHolderElt(DummyElement):
    """Inserted in place of field maps and superpose map commands."""


class SuperposedPlaceHolderCmd(DummyCommand):
    """Inserted in place of field maps and superpose map commands."""
