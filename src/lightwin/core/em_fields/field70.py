"""Define the dc field corresponding to ``FIELD_MAP 70``.

This is 3D magnetic field along. Not really implemented as 3D field maps is not
implemented, but can serve as a place holder for non-accelerating fields.

"""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from lightwin.core.em_fields.field import Field
from lightwin.core.em_fields.field_helpers import null_field_1d


class Field70(Field):
    """Define a RF field, 1D longitudinal."""

    extensions = (".bsx", ".bsy", ".bsz")
    is_implemented = False

    def __init__(
        self,
        folder: Path,
        filename: str,
        length_m: float,
        z_0: float = 0,
        flag_cython: bool = False,
    ) -> None:
        super().__init__(folder, filename, length_m, z_0, flag_cython)
        if self.flag_cython:
            logging.error("Cython not implemented for Field70.")

    def _load_fieldmap(
        self,
        path: Path,
        **validity_check_kwargs,
    ) -> tuple[Callable[..., float], Any, int]:
        """Return dummy fields."""
        return null_field_1d, 60, 1
