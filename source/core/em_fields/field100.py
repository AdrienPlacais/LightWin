"""Define the rf field corresponding to ``FIELD_MAP 100``.

This is 1D longitudinal field along ``z``. The only one that is completely
implemented for now.

"""

from collections.abc import Callable
from pathlib import Path
from typing import override

import numpy as np

from core.em_fields.field import Field, FieldFuncComponent
from tracewin_utils.load import load_1d_field


class Field100(Field):
    """Define a RF field, 1D longitudinal."""

    extensions = (".edz",)

    @override
    def _load_fieldmap(self, path: Path) -> tuple[FieldFuncComponent1D, int]:
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

        """
        n_z, zmax, norm, f_z, n_cell = load_1d_field(path)
        e_z: Callable

        return e_z, n_z

    def _data_to_function(self, data: np.ndarray) -> FieldFuncComponent1D:
        """Give the function to compute field."""

    def shift(self) -> None:
        """Shift the electric field map.

        .. warning::
            You must ensure that for ``z < 0`` and ``z > element.length_m`` the
            electric field is null. Interpolation can lead to funny results!

        """
        assert hasattr(
            self, "starting_position"
        ), "You need to set the starting_position attribute of the RfField."
        if not hasattr(self, "_original_e_spat"):
            self._original_e_spat = self.e_spat
        self.e_spat = partial(
            shifted_e_spat, e_spat=self.e_spat, z_shift=self.starting_position
        )
