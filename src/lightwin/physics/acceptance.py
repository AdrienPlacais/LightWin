"""Define functions related to acceptance calculation.

.. todo::
   Show equations and references in the docstrings.

"""

import logging
from math import cos, pi, sin, sqrt

import numpy as np

from lightwin.constants import c
from lightwin.physics.converters import energy
from lightwin.util.solvers import (
    solve_scalar_equation_brent,
)
from lightwin.util.typing import BeamKwargs


def compute_acceptances(
    phi_s: float,
    freq_cavity_mhz: float,
    w_kin: float | None,
    v_cav_mv: float,
    length_m: float,
    beam_kwargs: BeamKwargs,
) -> tuple[float, float]:
    r"""Compute acceptances in phase and energy.

    Handles off-limits synchronous phases.

    Parameters
    ----------
    phi_s
        Synchronous phase; if it is outside :math:`(-\pi / 2,~0)`, both
        acceptances are ``nan``.
    freq_cavity_mhz
        Cavity frequency in :unit:`MHz`.
    w_kin
        Beam energy at the cavity exit in :unit:`MeV`.
    v_cav_mv
        Cavity accelerating voltage in :unit:`MV`.
    length_m
        Cavity length in :unit:`m`.
    beam_kwargs
        Dict holding beam parameters, and in particular the adimensionned
        charge ``q_adim`` and the rest energy ``e_rest_mev``.

    Returns
    -------
    acceptance_phi
        Acceptance in phase in :unit:`rad`.
    acceptance_energy
        Acceptance in energy in :unit:`MeV`.

    """
    if not (-0.5 * pi <= phi_s <= 0.0):
        return np.nan, np.nan
    if w_kin is None:
        logging.error(
            "The kinetic energy of current cavity was not set. Is it a failed "
            "cavity? Returning ``np.nan`` acceptances."
        )
        return np.nan, np.nan

    return _compute_acceptance_phase(phi_s), _compute_acceptance_energy(
        phi_s, freq_cavity_mhz, w_kin, v_cav_mv, length_m, **beam_kwargs
    )


def _compute_acceptance_phase(phi_s: float) -> float:
    r"""Compute the acceptance in phase using Brent method.

    Parameters
    ----------
    phi_s
        Synchronous phase, must be in :math:`(-\pi / 2,~0)`.

    Returns
    -------
        Cavity acceptance in phase, in :unit:`rad`.

    """
    return -(
        phi_s
        + solve_scalar_equation_brent(
            _compute_phi_2, phi_s, x_bounds=(-1.5 * pi, 0)
        )
    )


def _compute_phi_2(phi_2: float, phi_s: float) -> float:
    """Compute the left boundary of the phase acceptance (phi_2).

    Parameters
    ----------
    phi_2
        Phase value in radians to test as the boundary.
    phi_s
        Synchronous phase in radians.

    Returns
    -------
    float
        Function value to be used in root-finding (zero crossing corresponds to
        phi_2).

    """
    term1 = sin(phi_2) - phi_2 * cos(phi_s)
    term2 = sin(phi_s) - phi_s * cos(phi_s)
    return term1 + term2


def _compute_acceptance_energy(
    phi_s: float,
    freq_cavity_mhz: float,
    w_kin: float,
    v_cav_mv: float,
    length_m: float,
    q_adim: float,
    e_rest_mev: float,
    **beam_kwargs,
) -> float:
    r"""Compute the acceptance in energy.

    Parameters
    ----------
    phi_s
        Synchronous phase, must be in :math:`(-\pi / 2,~0)`.
    freq_cavity_mhz
        Cavity frequency in :unit:`MHz`.
    w_kin
        Beam energy at the cavity exit in :unit:`MeV`.
    v_cav_mv
        Cavity accelerating voltage in :unit:`MV`.
    length_m
        Cavity length in :unit:`m`.
    q_adim
        Beam adimensionned charge.
    e_rest_mev
        Beam rest energy in :unit:`MeV`.

    Returns
    -------
        Cavity acceptance in energy, in :unit:`MeV`.

    """
    # q_over_m and m_over_q are not used... Even if they are mandatory args!
    beta_kin = energy(
        w_kin, "kin to beta", q_over_m=0.0, m_over_q=0, e_rest_mev=e_rest_mev
    )
    gamma_kin = energy(
        w_kin, "kin to gamma", q_over_m=0, m_over_q=0, e_rest_mev=e_rest_mev
    )
    factor = (
        q_adim * v_cav_mv * (beta_kin * gamma_kin) ** 3 * e_rest_mev * c
    ) / (pi * freq_cavity_mhz * 1e6 * length_m)
    trig_term = phi_s * cos(phi_s) - sin(phi_s)
    return sqrt(2 * factor * trig_term)
