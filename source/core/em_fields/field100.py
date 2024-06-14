"""Define the rf field corresponding to ``FIELD_MAP 100``.

This is 1D longitudinal field along ``z``. The only one that is completely
implemented for now.

"""

import functools
import math
from pathlib import Path

import numpy as np

from core.em_fields.field import Field
from core.em_fields.helper import create_1d_field_func, shifted_e_spat
from core.em_fields.types import FieldFuncComponent1D
from tracewin_utils.electromagnetic_fields import (
    is_a_valid_1d_electric_field,
    rescale,
)
from tracewin_utils.load import load_1d_field


class Field100(Field):
    """Define a RF field, 1D longitudinal."""

    extensions = (".edz",)

    def _load_fieldmap(
        self, path: Path, **validity_check_kwargs
    ) -> tuple[FieldFuncComponent1D, int, int]:
        r"""Load a 1D field (``.edz`` extension).

        Parameters
        ----------
        path : Path
            The path to the ``.edz`` file to load.

        Returns
        -------
        e_z : FieldFuncComponent1D
            Function that takes in ``z`` position and returns corresponding
            field, at null phase, for amplitude of :math:`1\,\mathrm{MV/m}`.
        n_z : int
            Number of interpolation points.
        n_cell : int
            Number of cell for cavities.

        """
        n_z, zmax, norm, f_z, n_cell = load_1d_field(path)

        assert is_a_valid_1d_electric_field(
            n_z, zmax, f_z, self._length_m
        ), f"Error loading {path}'s field map."

        f_z = rescale(f_z, norm)
        z_positions = np.linspace(0.0, zmax, n_z + 1)
        e_z = create_1d_field_func(f_z, z_positions)
        return e_z, n_z, n_cell

    def shift(self) -> None:
        """Shift the electric field map.

        .. warning::
            You must ensure that for ``z < 0`` and ``z > element.length_m`` the
            electric field is null. Interpolation can lead to funny results!

        """
        assert hasattr(
            self, "z_0"
        ), "You need to set the starting_position attribute of the Field."
        shifted = functools.partial(
            shifted_e_spat, e_spat=self._e_z_spat_rf, z_shift=self.z_0
        )
        self._e_z_spat_rf = shifted

    def e_z(
        self, pos: float, phi: float, amplitude: float, phi_0_rel: float
    ) -> float:
        """Give longitudinal electric field value."""
        return amplitude * self._e_z_spat_rf(pos) * math.cos(phi + phi_0_rel)
