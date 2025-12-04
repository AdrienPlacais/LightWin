"""Define functions to switch between the various phases.

Mainly used by :class:`.CavitySettings`.

"""

import math
from typing import overload

import numpy as np
from numpy.typing import NDArray


def diff_angle(phi_1: float, phi_2: float) -> float:
    """Compute smallest difference between two angles."""
    delta_phi = math.atan2(math.sin(phi_2 - phi_1), math.cos(phi_2 - phi_1))
    return delta_phi


# =============================================================================
# Conversion between different phases
# =============================================================================
def phi_0_abs_to_rel(phi_0_abs: float, phi_rf: float) -> float:
    """Compute relative entry phase from absolute."""
    phi_0_rel = (phi_0_abs + phi_rf) % (2.0 * math.pi)
    return phi_0_rel


def phi_0_rel_to_abs(phi_0_rel: float, phi_rf: float) -> float:
    """Compute relative entry phase from absolute."""
    phi_0_abs = (phi_0_rel - phi_rf) % (2.0 * math.pi)
    return phi_0_abs


@overload
def phi_bunch_to_phi_rf(
    phi_bunch: NDArray[np.float64], rf_over_bunch_frequencies: float
) -> NDArray[np.float64]: ...


@overload
def phi_bunch_to_phi_rf(
    phi_bunch: float,
    rf_over_bunch_frequencies: float,
) -> float: ...


def phi_bunch_to_phi_rf(
    phi_bunch: float | NDArray[np.float64],
    rf_over_bunch_frequencies: float,
) -> float | NDArray[np.float64]:
    """Convert the bunch phase to a rf phase."""
    return phi_bunch * rf_over_bunch_frequencies


@overload
def phi_rf_to_phi_bunch(
    phi_rf: NDArray[np.float64], bunch_over_rf_frequencies: float
) -> NDArray[np.float64]: ...


@overload
def phi_rf_to_phi_bunch(
    phi_rf: float,
    bunch_over_rf_frequencies: float,
) -> float: ...


def phi_rf_to_phi_bunch(
    phi_rf: float | NDArray[np.float64],
    bunch_over_rf_frequencies: float,
) -> float | NDArray[np.float64]:
    """Convert the bunch phase to rf phase."""
    return phi_rf * bunch_over_rf_frequencies
