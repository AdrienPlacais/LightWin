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
    corresponding_positions: NDArray[np.float64],
) -> FieldFuncComponent1D:
    """Create the function to get spatial component of electric field."""
    field_values = np.asarray(field_values, dtype=float)
    corresponding_positions = np.asarray(corresponding_positions, dtype=float)

    def interp_func(pos: Pos1D) -> float:
        return float(
            np.interp(
                pos, corresponding_positions, field_values, left=0.0, right=0.0
            )
        )

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
