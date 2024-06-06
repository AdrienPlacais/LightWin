"""Define every element longitudinal transfer matrix.

Units are taken exactly as in TraceWin, i.e. first line is ``z (m)`` and second
line is ``dp/p``.

.. todo::
    Possible to use only lists here. May speed up the code, especially in _c.
    But numpy is fast, no?

.. todo::
    send beta as argument to avoid recomputing it each time

"""

import math
from typing import Callable

import numpy as np

import config_manager as con
from beam_calculation.integrators.rk4 import rk4
from constants import c


# =============================================================================
# Electric field functions
# =============================================================================
def e_func(
    z: float, e_spat: Callable[[float], float], phi: float, phi_0: float
) -> float:
    """Give the electric field at position z and phase phi.

    The field is normalized and should be multiplied by k_e.

    """
    return e_spat(z) * math.cos(phi + phi_0)


# =============================================================================
# Transfer matrices
# =============================================================================
def z_drift(
    gamma_in: float, delta_s: float, n_steps: int = 1
) -> tuple[np.ndarray, np.ndarray, None]:
    """Calculate the transfer matrix of a drift."""
    gamma_in_min2 = gamma_in**-2
    r_zz = np.full(
        (n_steps, 2, 2), np.array([[1.0, delta_s * gamma_in_min2], [0.0, 1.0]])
    )
    beta_in = math.sqrt(1.0 - gamma_in_min2)
    delta_phi = con.OMEGA_0_BUNCH * delta_s / (beta_in * c)

    # Two possibilites: second one is faster
    # l_gamman = [gamma for i in range(n_steps)]
    # l_phi_rel = [(i+1)*delta_phi for i in range(n_steps)]
    # gamma_phi = np.empty((n_steps, 2))
    # gamma_phi[:, 0] = l_W_kin
    # gamma_phi[:, 1] = l_phi_rel
    gamma_phi = np.empty((n_steps, 2))
    gamma_phi[:, 0] = gamma_in
    gamma_phi[:, 1] = np.arange(0.0, n_steps) * delta_phi + delta_phi
    return r_zz, gamma_phi, None


def z_field_map_rk4(
    gamma_in: float,
    d_z: float,
    n_steps: int,
    omega0_rf: float,
    k_e: float,
    phi_0_rel: float,
    e_spat: Callable[[float], float],
    **kwargs,
) -> tuple[np.ndarray, np.ndarray, complex]:
    """Calculate the transfer matrix of a FIELD_MAP using Runge-Kutta."""
    z_rel = 0.0
    itg_field = 0.0
    half_dz = 0.5 * d_z

    # Constants to speed up calculation
    delta_phi_norm = omega0_rf * d_z / c
    delta_gamma_norm = con.Q_ADIM * d_z * con.INV_E_REST_MEV
    k_k = delta_gamma_norm * k_e

    r_zz = np.empty((n_steps, 2, 2))
    gamma_phi = np.empty((n_steps + 1, 2))
    gamma_phi[0, 0] = gamma_in
    gamma_phi[0, 1] = 0.0

    # Define the motion function to integrate
    def du(z: float, u: np.ndarray) -> np.ndarray:
        r"""
        Compute variation of energy and phase.

        Parameters
        ----------
        z : float
            Position where variation is calculated.
        u : np.ndarray
            First component is gamma. Second is phase in rad.

        Return
        ------
        v : np.ndarray
            First component is :math:`\Delta \gamma / \Delta z` in
            :math:`\mathrm{MeV / m}`.
            Second is :math:`\Delta \phi / \Delta z` in
            :math:`\mathrm{rad / m}`.

        """
        v0 = k_k * e_func(z, e_spat, u[1], phi_0_rel)
        beta = np.sqrt(1.0 - u[0] ** -2)
        v1 = delta_phi_norm / beta
        return np.array([v0, v1])

    for i in range(n_steps):
        # Compute gamma and phase changes
        delta_gamma_phi = rk4(u=gamma_phi[i, :], du=du, x=z_rel, dx=d_z)

        gamma_phi[i + 1, :] = gamma_phi[i, :] + delta_gamma_phi

        itg_field += (
            k_e
            * e_func(z_rel, e_spat, gamma_phi[i, 1], phi_0_rel)
            * (1.0 + 1j * math.tan(gamma_phi[i, 1] + phi_0_rel))
            * d_z
        )

        # Compute gamma and phi at the middle of the thin lense
        gamma_phi_middle = gamma_phi[i, :] + 0.5 * delta_gamma_phi

        # To speed up (corresponds to the gamma_variation at the middle of the
        # thin lense at cos(phi + phi_0) = 1
        delta_gamma_middle_max = k_k * e_spat(z_rel + half_dz)

        # Compute thin lense transfer matrix
        r_zz[i, :, :] = z_thin_lense(
            gamma_phi[i, 0],
            gamma_phi[i + 1, 0],
            gamma_phi_middle,
            half_dz,
            delta_gamma_middle_max,
            phi_0_rel,
            omega0_rf,
        )

        z_rel += d_z

    return r_zz, gamma_phi[1:, :], itg_field


def z_field_map_leapfrog(
    d_z: float,
    gamma_in: float,
    n_steps: int,
    omega0_rf: float,
    k_e: float,
    phi_0_rel: float,
    e_spat: Callable[[float], float],
    **kwargs,
) -> tuple[np.ndarray, np.ndarray, float]:
    """
    Calculate the transfer matrix of a ``FIELD_MAP`` using leapfrog.

    .. todo::
        clean, fix, separate leapfrog integration in dedicated module

    This method is less precise than RK4. However, it is much faster.

    Classic leapfrog method:
    speed(i+0.5) = speed(i-0.5) + accel(i) * dt
    pos(i+1)     = pos(i)       + speed(i+0.5) * dt

    Here, dt is not fixed but dz.
    z(i+1) += dz
    t(i+1) = t(i) + dz / (c beta(i+1/2))
    (time and space variables are on whole steps)
    beta calculated from W(i+1/2) = W(i-1/2) + qE(i)dz
    (speed/energy is on half steps)

    """
    z_rel = 0.0
    itg_field = 0.0
    half_dz = 0.5 * d_z

    # Constants to speed up calculation
    delta_phi_norm = omega0_rf * d_z / c
    delta_gamma_norm = con.Q_ADIM * d_z * con.INV_E_REST_MEV
    k_k = delta_gamma_norm * k_e

    r_zz = np.empty((n_steps, 2, 2))
    gamma_phi = np.empty((n_steps + 1, 2))
    gamma_phi[0, 1] = 0.0
    # Rewind energy from i=0 to i=-0.5 if we are at the first cavity:
    # FIXME must be cleaner
    if gamma_in == con.GAMMA_INIT:
        gamma_phi[0, 0] = gamma_in - 0.5 * k_k * e_func(
            z_rel, e_spat, gamma_phi[0, 1], phi_0_rel
        )
    else:
        gamma_phi[0, 0] = gamma_in

    for i in range(n_steps):
        # Compute gamma change
        delta_gamma = k_k * e_func(z_rel, e_spat, gamma_phi[i, 1], phi_0_rel)

        # New gamma at i+0.5
        gamma_phi[i + 1, 0] = gamma_phi[i, 0] + delta_gamma
        beta = np.sqrt(1.0 - gamma_phi[i + 1, 0] ** -2)

        # Compute phase at step i + 1
        delta_phi = delta_phi_norm / beta
        gamma_phi[i + 1, 1] = gamma_phi[i, 1] + delta_phi

        # Update itg_field. Used to compute V_cav and phi_s.
        itg_field += (
            k_e
            * e_func(z_rel, e_spat, gamma_phi[i, 1], phi_0_rel)
            * (1.0 + 1j * np.tan(gamma_phi[i, 1] + phi_0_rel))
            * d_z
        )

        # Compute gamma and phi at the middle of the thin lense
        gamma_phi_middle = np.array(
            [gamma_phi[i, 0], gamma_phi[i, 1] + 0.5 * delta_phi]
        )
        # We already are at the step i + 0.5, so gamma_middle and beta_middle
        # are the same as gamma and beta

        # To speed up (corresponds to the gamma_variation at the middle of the
        # thin lense at cos(phi + phi_0) = 1
        delta_gamma_middle_max = k_k * e_spat(z_rel + half_dz)

        # Compute thin lense transfer matrix
        r_zz[i, :, :] = z_thin_lense(
            gamma_phi[i, 0],
            gamma_phi[i + 1, 0],
            gamma_phi_middle,
            half_dz,
            delta_gamma_middle_max,
            phi_0_rel,
            omega0_rf,
        )

        z_rel += d_z

    return r_zz, gamma_phi[1:, :], itg_field


def z_thin_lense(
    gamma_in: float,
    gamma_out: float,
    gamma_phi_m: np.ndarray,
    half_dz: float,
    delta_gamma_m_max: float,
    phi_0: float,
    omega0_rf: float,
) -> np.ndarray:
    """
    Thin lense approximation: drift-acceleration-drift.

    Parameters
    ----------
    gamma_in : float
        gamma at entrance of first drift.
    gamma_out : float
        gamma at exit of first drift.
    gamma_phi_m : np.ndarray
        gamma and phase at the thin acceleration drift.
    half_dz : float
        Half a spatial step in m.
    delta_gamma_m_max : float
        Max gamma increase if the cos(phi + phi_0) of the acc. field is 1.
    phi_0 : float
        Input phase of the cavity.
    omega0_rf : float
        Pulsation of the cavity.

    Return
    ------
    r_zz_array : np.ndarray
        Transfer matrix of the thin lense.

    """
    # Used for tm components
    beta_m = math.sqrt(1.0 - gamma_phi_m[0] ** -2)
    k_speed1 = delta_gamma_m_max / (gamma_phi_m[0] * beta_m**2)
    k_speed2 = k_speed1 * math.cos(gamma_phi_m[1] + phi_0)

    # Thin lense transfer matrices components
    k_1 = (
        k_speed1 * omega0_rf / (beta_m * c) * math.sin(gamma_phi_m[1] + phi_0)
    )
    k_2 = 1.0 - (2.0 - beta_m**2) * k_speed2
    k_3 = (1.0 - k_speed2) / k_2

    # Faster than matmul or matprod_22
    r_zz_array = z_drift(gamma_out, half_dz)[0][0] @ (
        np.array(([k_3, 0.0], [k_1, k_2])) @ z_drift(gamma_in, half_dz)[0][0]
    )
    return r_zz_array


def z_bend(
    gamma_in: float,
    delta_s: float,
    factor_1: float,
    factor_2: float,
    factor_3: float,
) -> tuple[np.ndarray, np.ndarray, None]:
    r"""Compute the longitudinal transfer matrix of a bend.

    ``factor_1`` is:

    .. math::
        \frac{-h^2\Delta s}{k_x^2}

    ``factor_2`` is:

    .. math::
        \frac{h^2 \sin{(k_x\Delta s)}}{k_x^3}

    ``factor_3`` is:

    .. math::
        \Delta s \left(1 - \frac{h^2}{k_x^2}\right)

    """
    gamma_in_min2 = gamma_in**-2
    beta_in_squared = 1.0 - gamma_in_min2

    topright = factor_1 * beta_in_squared + factor_2 + factor_3 * gamma_in_min2
    r_zz = np.eye(2)
    r_zz[0, 1] = topright

    delta_phi = con.OMEGA_0_BUNCH * delta_s / (math.sqrt(beta_in_squared) * c)
    gamma_phi = np.array([gamma_in, delta_phi])
    return r_zz[np.newaxis, :], gamma_phi[np.newaxis, :], None
