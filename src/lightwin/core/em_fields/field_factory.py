"""Define a factory to easily create the :class:`.Field` objects.

.. todo::
    Implement :class:`.SuperposedFieldMap`.

"""

from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path

from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.elements.field_maps.field_map_70 import FieldMap70
from lightwin.core.elements.field_maps.field_map_100 import FieldMap100
from lightwin.core.elements.field_maps.field_map_1100 import FieldMap1100
from lightwin.core.elements.field_maps.field_map_7700 import FieldMap7700
from lightwin.core.elements.field_maps.superposed_field_map import (
    SuperposedFieldMap,
)
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
        self, field_maps: Collection[FieldMap | SuperposedFieldMap]
    ) -> dict[tuple[Path, float, float], list[FieldMap]]:
        """Associate :class:`.FieldMap` objects using the same fields.

        :class:`.SuperposedFieldMap` are replaced by the list of
        :class:`.FieldMap` they superpose.

        Parameters
        ----------
        field_maps : Collection[FieldMap | SuperposedFieldMap]
            All the :class:`.FieldMap` instances requiring a :class:`.Field`.

        Returns
        -------
        dict[tuple[pathlib.Path, float, float], list[FieldMap]]
            A dictionary where each key is a path to a field map file, a field
            map length, a z_0 shift and each value is a list of
            :class:`.FieldMap` instances that use those `Field.__init__` args.

        """
        unpacked = _unpack_superposed_field_maps(field_maps)

        to_load: dict[tuple[Path, float, float], list[FieldMap]] = {}
        for field_map in unpacked:
            assert isinstance(field_map.field_map_file_name, Path)
            file_path = (
                field_map.field_map_folder / field_map.field_map_file_name
            )
            args = (file_path, field_map.length_m, field_map.z_0)
            if args not in to_load:
                to_load[args] = []

            to_load[args].append(field_map)

        self._check_uniformity_of_types(to_load)
        return to_load

    def _check_uniformity_of_types(
        self, to_load: dict[tuple[Path, float, float], list[FieldMap]]
    ) -> None:
        """Check that for a file name, all corresp. object have same geom."""
        for (path, _, _), field_maps in to_load.items():
            different_types = set([type(x) for x in field_maps])
            if len(different_types) != 1:
                raise NotImplementedError(
                    "Several FIELD_MAP with different types use the same "
                    f"filename = {path}, which is not supported for now."
                )

    def run_all(self, field_maps: Collection[FieldMap]) -> None:
        """Generate the :class:`.Field` objects and store it in field maps."""
        to_load = self._gather_files_to_load(field_maps)
        for (path, length_m, z_0), field_maps in to_load.items():
            field_map = field_maps[0]
            constructor = FIELDS[field_map.__class__]
            field = constructor(
                field_map_path=path, length_m=length_m, z_0=z_0
            )

            for fm in field_maps:
                fm.field = field
                fm.cavity_settings.field = field
        return


def _unpack_superposed_field_maps(
    packed: Collection[FieldMap | SuperposedFieldMap],
) -> list[FieldMap]:
    """Extract the :class:`.FieldMap` from :class:`.SuperposedFieldMap`."""
    unpacked = [
        elt
        for obj in packed
        for elt in (
            obj.field_maps if isinstance(obj, SuperposedFieldMap) else [obj]
        )
    ]

    return unpacked
