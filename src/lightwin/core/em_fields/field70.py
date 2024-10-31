"""Define the dc field corresponding to ``FIELD_MAP 70``.

This is 3D magnetic field along. Not really implemented as 3D field maps is not
implemented, but can serve as a place holder for non-accelerating fields.

"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from lightwin.core.em_fields.field import Field
from lightwin.core.em_fields.field_helpers import null_field_1d


class Field70(Field):
    """Define a RF field, 1D longitudinal."""

    extensions = (".bsx", ".bsy", ".bsz")
    is_implemented = False

    def _load_fieldmap(
        self,
        path: Path,
        **validity_check_kwargs,
    ) -> tuple[Callable[..., float], Any, int]:
        """Return dummy fields."""
        return null_field_1d, 60, 1

    def b_x(
        self,
        pos: tuple[float, float, float],
        phi: float,
        amplitude: float,
        phi_0_rel: float,
    ) -> float:
        """Give magnetic field value."""
        return amplitude * self._b_x_dc(pos)

    def b_y(
        self,
        pos: tuple[float, float, float],
        phi: float,
        amplitude: float,
        phi_0_rel: float,
    ) -> float:
        """Give magnetic field value."""
        return amplitude * self._b_y_dc(pos)

    def b_z(
        self,
        pos: tuple[float, float, float],
        phi: float,
        amplitude: float,
        phi_0_rel: float,
    ) -> float:
        """Give magnetic field value."""
        return amplitude * self._b_z_dc(pos)
