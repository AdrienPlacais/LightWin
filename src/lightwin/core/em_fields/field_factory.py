"""Define a factory to easily create the :class:`.Field` objects.

.. todo::
    Implement :class:`.SuperposedFieldMap`.

"""

from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.elements.field_maps.field_map_70 import FieldMap70
from lightwin.core.elements.field_maps.field_map_100 import FieldMap100
from lightwin.core.elements.field_maps.field_map_1100 import FieldMap1100
from lightwin.core.elements.field_maps.field_map_7700 import FieldMap7700
from lightwin.core.elements.field_maps.superposed_field_map import (
    SuperposedFieldMap,
)
from lightwin.core.em_fields.field import Field
from lightwin.core.em_fields.field70 import Field70
from lightwin.core.em_fields.field100 import Field100

FIELDS = {
    FieldMap: Field100,  # default, should not be used
    FieldMap70: Field70,
    FieldMap100: Field100,
    FieldMap1100: Field100,
    FieldMap7700: Field100,
}


@dataclass
class FieldFactory:
    """Create the :class:`.Field` and load the field maps."""

    default_field_map_folder: Path

    def _gather_files_to_load(
        self, field_maps: Collection[FieldMap]
    ) -> dict[Path, list[FieldMap]]:
        """Associate :class:`.FieldMap` objects using the same fields.

        Parameters
        ----------
        field_maps : Collection[FieldMap]
            All the :class:`.FieldMap` instances requiring a :class:`.Field`.

        Returns
        -------
        dict[pathlib.Path, list[FieldMap]]
            A dictionary where each key is a path to a field map file, and each
            value is a list of :class:`.FieldMap` instances that use that file.

        Raises
        ------
        NotImplementedError
            If a :class:`.SuperposedFieldMap` is encountered, as it's not yet
            supported.

        """
        to_load: dict[Path, list[FieldMap]] = {}
        for field_map in field_maps:
            if isinstance(field_map, SuperposedFieldMap):
                raise NotImplementedError(
                    "Loading of field maps not yet implemented for Superposed."
                )
            assert isinstance(field_map.field_map_file_name, Path)
            file_path = (
                field_map.field_map_folder / field_map.field_map_file_name
            )
            if file_path not in to_load:
                to_load[file_path] = []

            to_load[file_path].append(field_map)

        self._check_uniformity_of_types(to_load)
        return to_load

    def _check_uniformity_of_types(
        self, to_load: dict[Path, list[FieldMap]]
    ) -> None:
        """Check that for a file name, all corresp. object have same geom."""
        for filename, field_maps in to_load.items():
            different_types = set([type(x) for x in field_maps])
            if len(different_types) != 1:
                raise NotImplementedError(
                    "Several FIELD_MAP with different types use the same "
                    f"{filename = }, which is not supported for now."
                )

    def _run(
        self,
        constructor: type[Field],
        field_map_path: Path,
        length_m: float,
        z_0: float = 0.0,
        **kwargs,
    ) -> Field:
        """Create a single :class:`.Field`."""
        return constructor(
            field_map_path=field_map_path,
            length_m=length_m,
            z_0=z_0,
        )

    def _run_kwargs(self, field_map: FieldMap) -> dict[str, Any]:
        """Get the kwargs necessary for ``_run``."""
        kwargs = {"z_0": 0.0, "length_m": field_map.length_m}
        return kwargs

    def run_all(self, field_maps: Collection[FieldMap]) -> None:
        """Generate the :class:`.Field` objects and store it in field maps."""
        to_load = self._gather_files_to_load(field_maps)
        for path, field_maps in to_load.items():
            field_map = field_maps[0]

            constructor = FIELDS[field_map.__class__]
            kwargs = self._run_kwargs(field_map)

            field = self._run(constructor, field_map_path=path, **kwargs)

            for fm in field_maps:
                fm.field = field
        return
