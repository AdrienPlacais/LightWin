"""Define functions to compute 1D longitudinal electric fields."""

import math
from collections.abc import Callable, Collection
from functools import partial

# Spatial component of longitudinal E field, takes in z pos
longitudinal_e_spat_t = Callable[[float], float]


def default_longitudinal_e_spat(z_pos: float) -> float:
    """Define a null electric field."""
    return 0.0


def normalized_longitudinal_e(
    z_pos: float, long_e_spat: longitudinal_e_spat_t, phi: float, phi_0: float
) -> float:
    """Compute electric field, normalized."""
    return long_e_spat(z_pos) * math.cos(phi + phi_0)


def longitudinal_e(
    z_pos: float,
    long_e_spat: longitudinal_e_spat_t,
    phi: float,
    phi_0: float,
    k_e: float,
) -> float:
    """Compute normed longitudinal electric field."""
    return k_e * long_e_spat(z_pos) * math.cos(phi + phi_0)


def superpose_longitudinal_e_spats(
    e_spats: Collection[longitudinal_e_spat_t], z_0s: Collection[float]
) -> list[longitudinal_e_spat_t]:
    """Superpose the given electric fields.

    This is used by the ``SUPERPOSE_MAP ``command. We extend every electric
    field so that it spans over the whole range of positions, but electric
    fields are null outside of the range they were defined.

    """
    shifted_e_spats = [
        partial(shifted_e_spat, e_spat=e_spat, z_shift=z_0)
        for e_spat, z_0 in zip(e_spats, z_0s, strict=True)
    ]
    return shifted_e_spats


def shifted_e_spat(
    e_spat: longitudinal_e_spat_t, z_shift: float, z_pos: float
) -> float:
    """Shift electric field by ``z_shift``."""
    return e_spat(z_pos + z_shift)
