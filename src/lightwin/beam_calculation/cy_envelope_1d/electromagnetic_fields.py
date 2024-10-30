"""Define Cython specific functions to pre-load electromagnetic fields.

Used to speed up caclulations.

"""

import logging
from collections.abc import Collection
from pathlib import Path

from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.util import helper


def load_electromagnetic_fields_for_cython(
    field_maps: Collection[FieldMap], loadable: Collection[Path]
) -> None:
    """Load one electric field per section."""
    files = [
        field_map.field_map_file_name
        for field_map in field_maps
        if hasattr(field_map, "rf_field") and field_map.rf_field.is_loaded
    ]
    flattened_files = helper.flatten(files)
    unique_files = helper.remove_duplicates(flattened_files)
    loadable_files = list(
        filter(lambda file: file.suffix in loadable, unique_files)
    )
    try:
        import lightwin.beam_calculation.cy_envelope_1d.transfer_matrices as cy_transfer_matrices  # type: ignore
    except ImportError as e:
        logging.error(
            "Could not import the Cython version of transfer matrices."
        )
        raise ImportError(e)

    cy_transfer_matrices.init_arrays(loadable_files)
