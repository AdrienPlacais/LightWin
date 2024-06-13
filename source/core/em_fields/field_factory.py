"""Define a factory to easily create the :class:`.Field` objects."""

from abc import ABCMeta
from collections.abc import Collection
from pathlib import Path
from typing import Any

from core.elements.field_maps.field_map import FieldMap
from core.elements.field_maps.field_map_70 import FieldMap70
from core.elements.field_maps.field_map_100 import FieldMap100
from core.elements.field_maps.field_map_1100 import FieldMap1100
from core.elements.field_maps.field_map_7700 import FieldMap7700
from core.elements.field_maps.superposed_field_map import SuperposedFieldMap
from core.em_fields.field import AnyDimFloat, Field
from core.em_fields.field100 import Field100

FIELDS = {
    FieldMap: Field100,  # default, should not be used
    FieldMap70: Field100,
    FieldMap100: Field100,
    FieldMap1100: Field100,
    FieldMap7700: Field100,
}


class FieldFactory:

    def __init__(self, default_field_map_folder: Path, n_steps: int) -> None:
        """Instantiate factory."""
        self.default_field_map_folder = default_field_map_folder
        self.n_steps = n_steps

    def gather_files_to_load(
        self, field_maps: Collection[FieldMap]
    ) -> dict[Path, tuple[FieldMap, ...]]:
        """Associate :class:`.FieldMap` objects using the same fields."""
        field_map_names: dict[Path, list[FieldMap]] = {}
        for field_map in field_maps:
            if isinstance(field_map, SuperposedFieldMap):
                raise NotImplementedError
            assert isinstance(field_map.field_map_file_name, Path)
            file_name = (
                field_map.field_map_folder / field_map.field_map_file_name
            )
            if file_name not in field_map_names:
                field_map_names[file_name] = []

            field_map_names[file_name].append(field_map)

        self._check_uniformity_of_types(field_map_names)
        to_load = {key: tuple(val) for key, val in field_map_names.items()}
        return to_load

    def _check_uniformity_of_types(
        self, field_map_names: dict[Path, list[FieldMap]]
    ) -> None:
        """Check that for a file name, all corresp. object have same geom."""
        for filename, field_maps in field_map_names.items():
            different_types = set([type(x) for x in field_maps])
            assert len(different_types) == 1, (
                "Several FIELD_MAP with different types use the same filename"
                f"{filename}, which is not supported for now."
            )

    def run(
        self,
        constructor: ABCMeta,
        field_map_path: Path,
        length_m: float,
        z_0: AnyDimFloat = 0.0,
        **kwargs,
    ) -> Field:
        """Create a single :class:`.Field`."""
        return constructor(
            field_map_path=field_map_path,
            n_steps=self.n_steps,
            length_m=length_m,
            z_0=z_0,
        )

    def get_run_kwargs(self, field_map: FieldMap) -> dict[str, Any]:
        """Get the kwargs necessary for :meth:`run`."""
        kwargs = {
            "z_0": 0.0,
            "length_m": field_map.length_m,
        }
        return kwargs

    def run_all(self, to_load: dict[Path, tuple[FieldMap, ...]]) -> None:
        """Generate the :class:`.Field` objects and store it in field maps."""
        for path, field_maps in to_load.items():
            field = field_maps[0]
            class_name = field.__class__
            constructor = FIELDS[class_name]

            kwargs = self.get_run_kwargs(field)
            field = self.run(constructor, field_map_path=path, **kwargs)

            for field_map in field_maps:
                field_map.field = field
