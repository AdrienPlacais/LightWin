"""Define functions to compute 1D longitudinal electric fields.

The ones used by :class:`.Field` will be in :file:`field_helpers.py` from now
on.

"""

import math
from collections.abc import Callable
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
) -> Callable[[float], float]:
    """Create the function to get spatial component of electric field."""
    xp = np.asarray(corresponding_positions, dtype=float)
    fp = np.asarray(field_values, dtype=float)

    def field_func(pos: Pos1D) -> float:
        return float(np.interp(x=pos, xp=xp, fp=fp, left=0.0, right=0.0))

    return field_func


def normalized_e_1d(
    pos: float, e_func: Callable[[float], float], phi: float, phi_0: float
) -> float:
    """Compute electric field, normalized."""
    return e_func(pos) * math.cos(phi + phi_0)


def normalized_e_1d_complex(
    pos: float, e_func: Callable[[float], float], phi: float, phi_0: float
) -> complex:
    """Compute electric field, normalized."""
    return e_func(pos) * (math.cos(phi + phi_0) + 1j * math.sin(phi + phi_0))


def e_1d(
    pos: float,
    e_func: Callable[[float], float],
    phi: float,
    amplitude: float,
    phi_0: float,
) -> float:
    """Compute normed 1D electric field."""
    return amplitude * normalized_e_1d(pos, e_func, phi, phi_0)


def e_1d_complex(
    pos: float,
    e_func: Callable[[float], float],
    phi: float,
    amplitude: float,
    phi_0: float,
) -> complex:
    """Compute normed 1D electric field."""
    return amplitude * normalized_e_1d_complex(pos, e_func, phi, phi_0)


# def superpose_longitudinal_e_spats(
#     e_spats: Collection[FieldFuncComponent1D], z_0s: Collection[float]
# ) -> list[FieldFuncComponent1D]:
#     """Superpose the given electric fields.
#
#     This is used by the ``SUPERPOSE_MAP`` command. We extend every electric
#     field so that it spans over the whole range of positions, but electric
#     fields are null outside of the range they were defined.
#
#     """
#     shifted_e_spats = [
#         partial(shifted_e_spat, e_spat=e_spat, z_shift=z_0)
#         for e_spat, z_0 in zip(e_spats, z_0s, strict=True)
#     ]
#     return shifted_e_spats


def shifted_e_spat(
    e_spat: FieldFuncComponent1D, z_shift: float, z_pos: float
) -> float:
    """Shift electric field by ``z_shift``."""
    return e_spat(z_pos + z_shift)
