"""Define various functions to compute the synchronous phase."""

import cmath
import logging
import math
from typing import Literal

import numpy as np


def phi_s_legacy(
    integrated_field: complex | None, *args, **kwargs
) -> tuple[float, float]:
    """Compute the cavity parameters with phi_s historical definition.

    Parameters
    ----------
    integrated_field
        Complex electric field felt by the synchronous particle. It is None
        if the cavity is failed.

    Returns
    -------
    v_cav_mv
        Accelerating voltage in MV. It is ``np.nan`` if ``integrated_field`` is
        None.
    phi_s
        Synchronous phase of the cavity in rad. It is ``np.nan`` if
        ``integrated_field`` is None.

    """
    if integrated_field is None:
        return np.nan, np.nan
    polar_itg = cmath.polar(integrated_field)
    return polar_itg[0], polar_itg[1]


def phi_s_lagniel(
    simulation_output: object, *args, **kwargs
) -> tuple[float, float]:
    """Compute cavity parameters with new phi_s model :cite:`Lagniel2021`.

    Parameters
    ----------
    simulation_output
        Holds results of a simulation.

    Returns
    -------
        Corrected synchronous phase of the cavity.

    """
    raise NotImplementedError
    logging.error("phi_s_lagniel not implemented")
    transf_mat_21 = simulation_output.transf_mat_21
    delta_w_kin = simulation_output.delta_w_kin
    return transf_mat_21 / delta_w_kin


def phi_s_from_tracewin_file(
    simulation_output: object, *args, **kwargs
) -> tuple[float, float]:
    """Get the synchronous phase from a TraceWin output file.

    It is up to you to edit the ``tracewin.ini`` file in order to have the
    synchronous phase that you want.

    """
    raise NotImplementedError
    logging.error("phi_s_tracewin not implemented")
    filepath = simulation_output.filepath
    del filepath
    return 14.0, -math.pi / 4.0


SYNCHRONOUS_PHASE_FUNCTIONS = {
    "legacy": phi_s_legacy,
    "historical": phi_s_legacy,
    "lagniel": phi_s_lagniel,
    "tracewin": phi_s_from_tracewin_file,
}
PHI_S_MODELS = Literal["historical", "lagniel"]  #:
