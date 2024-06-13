"""Define a factory to easily create the :class:`.Field` objects."""

from collections.abc import Collection
from pathlib import Path

from core.elements.field_maps.field_map import FieldMap
from core.em_fields.field import AnyDimFloat, AnyDimInt, Field


class FieldFactory:

    def __init__(self, default_field_map_folder: Path) -> None:
        """Instantiate factory."""
        self.default_field_map_folder = default_field_map_folder

    def gather_files_to_load(
        self, field_maps: Collection[FieldMap]
    ) -> dict[Path, tuple[FieldMap]]:
        """Associate :class:`.FieldMap` objects using the same fields."""
        raise NotImplementedError

    def run(
        self,
        field_map_path: Path,
        n_cell: int,
        n_steps: AnyDimInt,
        starting_pos: AnyDimFloat = 0.0,
    ) -> Field:
        """Create a single :class:`.Field`."""
        raise NotImplementedError

    def get_run_kwargs(
        self, field_map: FieldMap
    ) -> tuple[int, AnyDimInt, AnyDimFloat]:
        """Get the kwargs necessary for :meth:`run`."""

    def run_all(self, to_load: dict[Path, tuple[FieldMap]]) -> None:
        """Generate the :class:`.Field` objects and store it in field maps."""
        raise NotImplementedError
