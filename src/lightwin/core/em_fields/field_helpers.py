"""Define functions to compute 1D longitudinal electric fields."""

import math
from typing import Any

import numpy as np
from numpy.typing import NDArray

from lightwin.core.em_fields.types import FieldFuncComponent1D, Pos1D


def null_field_1d(pos: Any) -> float:
    """Define a null electric/magnetic field."""
    return 0.0


def create_1d_field_func(
    field_values: NDArray[np.float64],
    pos_max: float,
    n_intervals: int,
    pos_min: float = 0.0,
) -> FieldFuncComponent1D:
    """Create functions computing field for a given position.

    Parameters
    ----------
    field_values :
        Field values on en evenly spaced grid.
    pos_max :
        Ending position of the field.
    n_intervals :
        Number of intervals in the field map; it is ``n_points - 1``.
    pos_min :
        Starting position of the field.

    Returns
    -------
    FieldFuncComponent1D
        Function giving a field component at a given 1D position. It also have
        a ``xp`` and a ``fp`` attributes holding positions and field values.
        This is used for Cython implementations.

    .. todo::
        Clean this ``xp`` ``fp`` thingy, not clean at all.

    """
    field_values = np.asarray(field_values, dtype=float)

    total_length = pos_max - pos_min
    inv_dx = n_intervals / total_length

    def interp_func(pos: float) -> float:
        idx_float = (pos - pos_min) * inv_dx
        idx = int(idx_float)
        if idx < 0 or idx >= n_intervals:
            return 0.0
        t = idx_float - idx
        return field_values[idx] * (1.0 - t) + field_values[idx + 1] * t

    # Attach xp and fp as it is used by Cython
    interp_func.xp = np.linspace(pos_min, pos_max, n_intervals + 1)
    interp_func.fp = field_values

    return interp_func


def e_1d(
    pos: Pos1D,
    e_func: FieldFuncComponent1D,
    phi: float,
    amplitude: float,
    phi_0: float,
) -> float:
    """Compute normed 1D electric field."""
    return amplitude * e_func(pos) * math.cos(phi + phi_0)


def e_1d_complex(
    pos: Pos1D,
    e_func: FieldFuncComponent1D,
    phi: float,
    amplitude: float,
    phi_0: float,
) -> complex:
    """Compute normed 1D electric field."""
    phase = phi + phi_0
    return amplitude * e_func(pos) * (math.cos(phase) + 1j * math.sin(phase))


def shifted_e_spat(
    e_spat: FieldFuncComponent1D, z_shift: float
) -> FieldFuncComponent1D:
    """Shift electric field by ``z_shift``."""

    def shifted(z_pos: float) -> float:
        return e_spat(z_pos - z_shift)

    return shifted


def rescale_array(
    array: NDArray[np.float64], norm: float, tol: float = 1e-6
) -> NDArray[np.float64]:
    """Rescale given array if ``norm`` is different from unity."""
    if abs(norm - 1.0) > tol:
        array /= norm
    return array
