"""Define the rf field corresponding to ``FIELD_MAP 7700``.

This is 1D longitudinal field along ``z``. The only one that is completely
implemented for now.

"""

from pathlib import Path

import numpy as np

from lightwin.core.em_fields.field import Field, rescale_array
from lightwin.core.em_fields.field_helpers import (
    create_1d_field_func,
    shifted_e_spat,
)
from lightwin.core.em_fields.types import FieldFuncComponent1D
from lightwin.tracewin_utils.field_map_loaders import (
    field_values_on_axis,
    get_number_of_cells,
    is_a_valid_3d_field,
    load_field_3d,
)


class Field7700(Field):
    """Define a RF field, 1D longitudinal."""

    extensions = (".edx", ".edy", ".edz", ".bdx", ".bdy", ".bdz")
    is_implemented = True

    def _load_fieldmap(
        self, path: Path, **validity_check_kwargs
    ) -> tuple[FieldFuncComponent1D, tuple[int], int]:
        r"""Load a 3D field.

        .. warning::
            The field will be calculated on the axis only. We remove any
            transverse component for now.

        Parameters
        ----------
        path : pathlib.Path
            The path to the file to load.

        Returns
        -------
        field : Callable[[Pos3D], float]
            Function that takes in position and returns corresponding field, at
            null phase, for amplitude of :math:`1\,\mathrm{MV/m}`.
        n_xyz : tuple[int, int, int]
            Number of interpolation points in the three directions.
        n_cell : int
            Number of cell for cavities.

        """
        n_z, zmax, n_x, xmin, xmax, n_y, ymin, ymax, norm, field_values = (
            load_field_3d(path)
        )

        assert is_a_valid_3d_field(
            zmax, n_x, n_y, n_z, field_values, self._length_m
        ), f"Error loading {path}'s field map."

        field_values = rescale_array(field_values, norm)
        on_axis = field_values_on_axis(field_values, n_x, n_y)
        n_cell = get_number_of_cells(on_axis)
        z_positions = np.linspace(0.0, zmax, n_z + 1, dtype=np.float64)
        e_z = create_1d_field_func(on_axis, z_positions)
        return e_z, (n_z,), n_cell

    def shift(self) -> None:
        """Shift the electric field map.

        .. warning::
            You must ensure that for ``z < 0`` and ``z > element.length_m`` the
            electric field is null. Interpolation can lead to funny results!

        """
        assert hasattr(
            self, "z_0"
        ), "You need to set the starting_position attribute of the Field."
        shifted = shifted_e_spat(self._e_z_spat_rf, z_shift=self.z_0)
        self._e_z_spat_rf = shifted
