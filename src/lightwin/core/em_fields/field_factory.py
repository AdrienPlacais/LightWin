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
    unpack_superposed,
)
from lightwin.core.em_fields.field70 import Field70
from lightwin.core.em_fields.field100 import Field100
from lightwin.core.em_fields.field7700 import Field7700
from lightwin.core.em_fields.superposed_fields import SuperposedFields

FIELDS = {
    FieldMap: Field100,  # default, should not be used
    FieldMap70: Field70,
    FieldMap100: Field100,
    FieldMap1100: Field100,  # TODO
    FieldMap7700: Field7700,
}


@dataclass
class FieldFactory:
    """Create the :class:`.Field` and load the field maps."""

    default_field_map_folder: Path

    def _gather_primary_files_to_load(
        self, field_maps: Collection[FieldMap | SuperposedFieldMap]
    ) -> dict[tuple[Path, str, float, float], list[FieldMap]]:
        """Associate :class:`.FieldMap` objects using the same fields.

        :class:`.SuperposedFieldMap` are replaced by the list of
        :class:`.FieldMap` they superpose.

        Parameters
        ----------
        field_maps : Collection[FieldMap | SuperposedFieldMap]
            All the :class:`.FieldMap` instances requiring a :class:`.Field`.

        Returns
        -------
        dict[tuple[pathlib.Path, str, float, float], list[FieldMap]]
            A dictionary where each key is the tuple of arguments to
            instantiate a :class:`.Field`, and value is the list of
            :class:`.FieldMap` that will share this object.

        """
        all_field_maps = unpack_superposed(field_maps)

        to_load: dict[tuple[Path, str, float, float], list[FieldMap]] = {}
        for field_map in all_field_maps:
            args = (
                field_map.field_map_folder,
                field_map.filename,
                field_map.length_m,
                field_map.z_0,
            )
            if args not in to_load:
                to_load[args] = []

            to_load[args].append(field_map)

        self._check_uniformity_of_types(to_load)
        return to_load

    def _check_uniformity_of_types(
        self, to_load: dict[tuple[Path, str, float, float], list[FieldMap]]
    ) -> None:
        """Check that for a file name, all corresp. object have same geom."""
        for (_, filename, _, _), field_maps in to_load.items():
            different_types = set([type(x) for x in field_maps])
            if len(different_types) != 1:
                raise NotImplementedError(
                    "Several FIELD_MAP with different types use the same "
                    f"{filename = }, which is not supported for now."
                )

    def run_all(self, field_maps: Collection[FieldMap]) -> None:
        """Generate the :class:`.Field` objects and store it in field maps."""
        to_load = self._gather_primary_files_to_load(field_maps)
        for (folder, filename, length_m, z_0), corresp_maps in to_load.items():
            field_map = corresp_maps[0]
            constructor = FIELDS[field_map.__class__]
            field = constructor(
                folder=folder, filename=filename, length_m=length_m, z_0=z_0
            )

            for fm in corresp_maps:
                fm.cavity_settings.field = field
        self._create_superposed(field_maps)
        return

    def _create_superposed(self, field_maps: Collection[FieldMap]) -> None:
        """Create :class:`.SuperposedFieldMap` from :class:`FieldMap`.

        Classic :class:`.FieldMap` remain untouched.

        """
        superposed = [
            x for x in field_maps if isinstance(x, SuperposedFieldMap)
        ]
        for elt in superposed:
            fields = [fm.cavity_settings.field for fm in elt.field_maps]
            superposed_fields = SuperposedFields(fields)
            elt.field = superposed_fields
