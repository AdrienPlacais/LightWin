"""Define every element longitudinal transfer matrix.

Units are taken exactly as in TraceWin, i.e. first line is ``z (m)`` and second
line is ``dp/p``.

.. todo::
   Send beta as argument to avoid recomputing it each time

.. todo::
    electric field interpolated twice: a first time for acceleration, and a
    second time to iterate itg_field. Maybe this could be done only once.

.. todo::
    Integrate my doc with demonstration of transfer matrix for field map form.

"""

import math
from typing import Callable

import numpy as np
from numpy.typing import NDArray

from lightwin.beam_calculation.integrators.rk4 import rk4_2d
from lightwin.constants import c
from lightwin.core.em_fields.types import (
    FieldFuncComplexTimedComponent,
    FieldFuncTimedComponent,
)


def z_dummy(
    gamma_in: float, *args, **kwargs
) -> tuple[NDArray[np.float64], NDArray[np.float64], None]:
    """Return an eye transfer matrix."""
    r_zz = [[[1, 0], [0, 1]]]
    gamma_phi = [[gamma_in, 0.0]]
    return np.array(r_zz), np.array(gamma_phi), None


def _drift_matrix(gamma: float, half_dz: float) -> NDArray[np.float64]:
    return np.array([[1.0, half_dz * gamma**-2], [0.0, 1.0]], dtype=np.float64)


def z_drift(
    gamma_in: float,
    delta_s: float,
    omega_0_bunch: float,
    n_steps: int = 1,
) -> tuple[NDArray[np.float64], NDArray[np.float64], None]:
    """Calculate the transfer matrix of a drift."""
    gamma_in_min2 = gamma_in**-2
    r_zz = np.full(
        (n_steps, 2, 2), np.array([[1.0, delta_s * gamma_in_min2], [0.0, 1.0]])
    )
    beta_in = math.sqrt(1.0 - gamma_in_min2)
    delta_phi = omega_0_bunch * delta_s / (beta_in * c)

    gamma_phi = np.empty((n_steps, 2))
    gamma_phi[:, 0] = gamma_in
    gamma_phi[:, 1] = np.arange(0.0, n_steps) * delta_phi + delta_phi
    return r_zz, gamma_phi, None


def z_field_map_rk4(
    gamma_in: float,
    d_z: float,
    n_steps: int,
    omega0_rf: float,
    delta_phi_norm: float,
    delta_gamma_norm: float,
    complex_e_func: FieldFuncComplexTimedComponent,
    real_e_func: FieldFuncTimedComponent,
) -> tuple[NDArray[np.float64], NDArray[np.float64], complex]:
    r"""Calculate the transfer matrix of :class:`.FieldMap` using Runge-Kutta.

    We slice the field map in a serie of drift-thin acceleration gap-drift. We
    pre-compute some constants to speed up the calculation:

    Parameters
    ----------
    gamma_in :
        Lorentz factor at entry of field map.
    d_z :
        Size of the integration step in :unit:`m`.
    n_steps :
        Number of integration steps.
    omega0_rf :
        RF pulsation in :unit:`rad/s`.
    delta_phi_norm :
        Constant to speed up calculation.

        .. math::
            \Delta\phi_\mathrm{norm} = \frac{\omega_0 \Delta z}{c}

    delta_gamma_norm :
        Constant to speed up calculation.

        .. math::
            \Delta\gamma_\mathrm{norm} = \frac{q_\mathrm{adim} \Delta z}
            {E_\mathrm{rest}}

    complex_e_func :
        Takes in the z-position of the particle and the phase, return the
        complex field component at this phase and position.
    real_e_func :
        Takes in the z-position of the particle and the phase, return the
        real field component at this phase and position.

    Returns
    -------
    NDArray[np.float64]
        :math:`2\times 2 \times n` matrix, holding the :math:`2\times2`
        longitudinal transfer matrix of every field map slice along the field
        map.
    NDArray[np.float64]
        :math:`2\times n` array, holding Lorentz factor and phase of the
        synchronous particle along the linac.
    complex
        Complex integral of the field experienced by the synchronous particle
        when crossing the cavity.

    """
    z_rel = 0.0
    itg_field = 0.0
    half_dz = 0.5 * d_z

    r_zz = np.empty((n_steps, 2, 2))
    gamma = np.empty(n_steps + 1)
    gamma[0] = gamma_in
    phi = np.empty(n_steps + 1)
    phi[0] = 0.0

    def du_scalar(z: float, gamma: float, phi: float) -> tuple[float, float]:
        beta = math.sqrt(1.0 - gamma**-2)
        v0 = delta_gamma_norm * real_e_func(z, phi)
        v1 = delta_phi_norm / beta
        return v0, v1

    for i in range(n_steps):
        delta_gamma, delta_phi = rk4_2d(
            gamma[i], phi[i], delta=du_scalar, x=z_rel, dx=d_z
        )
        gamma[i + 1] = gamma[i] + delta_gamma
        phi[i + 1] = phi[i] + delta_phi
        itg_field += complex_e_func(z_rel, phi[i]) * d_z

        scaled_e_middle = delta_gamma_norm * complex_e_func(
            z_rel + half_dz, phi[i] + 0.5 * delta_phi
        )
        r_zz[i, :, :] = z_thin_lense(
            scaled_e_middle,
            gamma[i],
            gamma[i + 1],
            gamma[i] + 0.5 * delta_gamma,
            half_dz,
            omega0_rf,
        )

        z_rel += d_z

    gamma_phi = np.empty((n_steps, 2))
    gamma_phi[:, 0] = gamma[1:]
    gamma_phi[:, 1] = phi[1:]
    return r_zz, gamma_phi, itg_field


def z_thin_lense(
    scaled_e_middle: complex,
    gamma_in: float,
    gamma_out: float,
    gamma_middle: float,
    half_dz: float,
    omega0_rf: float,
) -> NDArray[np.float64]:
    r"""
    Compute propagation in a slice of field map using thin lense approximation.

    Thin lense approximation: drift-acceleration-drift. The transfer matrix of
    the thin accelerating gap is:

    .. math::

        \begin{bmatrix}
            k_3 & 1   \\
            k_1 & k_2 \\
        \end{bmatrix}

    Where:

    .. math::

        \left\{
        \begin{aligned}
            k_1 &= \Im(\widetilde{E}_\mathrm{scaled}^\mathrm{norm}) \frac{\omega_0}{\beta_m c} \\
            k_2 &= 1 - (2 - \beta_m^2)\Re(\widetilde{E}_\mathrm{scaled}^\mathrm{norm}) \\
            k_3 &= \frac{1 - \Re(\widetilde{E}_\mathrm{scaled}^\mathrm{norm})}{k_2}
        \end{aligned}
        \right.

    :math:`\widetilde{E}_\mathrm{scaled}^\mathrm{norm}` is proportional to the
    complex electric field at the middle of the accelerating gap:

    .. math::

        \widetilde{E}_\mathrm{scaled}^\mathrm{norm} =
            \frac{\Delta\gamma_\mathrm{norm}}{\gamma_m\beta_m^2}
            \widetilde{E}(z + \frac{\Delta z}{2}, \phi_m)

    Quantities with a :math:`m` subscript are taken at the middle of the
    accelerating gap. :math:`i` are in the first drift, :math:`i+1` in the
    second.

    .. note::
       **In TraceWin documentation:**

          - :math:`k_1` and :math:`k_2` are called :math:`K_1` and :math:`K_2`.
            They miss a :math:`\Delta z` term.
          - Our complex electric field :math:`\widetilde{E}` would be written:

            .. math::

                \widetilde{E} = E_0
                    \sin{
                        \left( \frac{Kz}{\beta_c} \right)
                    }
                    \left[
                        \cos{(\omega t_s + \varphi_0)}
                        + j\sin{(\omega t_s + \varphi_0)}
                    \right]

    Parameters
    ----------
    scaled_e_middle :
        Complex electric field in the accelerating gap multiplied by
        :math:`\Delta\gamma_\mathrm{norm}`:

        .. math::
           \widetilde{E}_\mathrm{scaled} = \Delta\gamma_\mathrm{norm}
           \widetilde{E}_z\left( z + \Delta z, \phi_m \right)

        where

        .. math::
            \Delta\gamma_\mathrm{norm} = \frac{q_\mathrm{adim} \Delta z}
            {E_\mathrm{rest}}

        In the routine, we define:

        .. math::
           \widetilde{E}_\mathrm{scaled}^\mathrm{norm} = \frac{
              \widetilde{E}_\mathrm{scaled}
           }{
              \gamma_m \beta_m^2
           }

    gamma_in :
        gamma at entrance of first drift.
    gamma_out :
        gamma at exit of first drift.
    gamma_middle :
        gamma at the thin acceleration drift.
    half_dz :
        Half a spatial step in :unit:`m`.
    omega0_rf :
        Pulsation of the cavity.
    omega_0_bunch :
        Pulsation of the beam.

    Returns
    -------
        Transfer matrix of the thin lense.

    """
    beta_m = math.sqrt(1.0 - gamma_middle**-2)
    scaled_e_middle /= gamma_middle * beta_m**2
    k_1 = scaled_e_middle.imag * omega0_rf / (beta_m * c)
    k_2 = 1.0 - (2.0 - beta_m**2) * scaled_e_middle.real
    k_3 = (1.0 - scaled_e_middle.real) / k_2
    r = _drift_matrix(gamma_out, half_dz)
    g = _drift_matrix(gamma_in, half_dz)
    thin = np.array([[k_3, 0.0], [k_1, k_2]])
    return r @ thin @ g


def z_bend(
    gamma_in: float,
    delta_s: float,
    factor_1: float,
    factor_2: float,
    factor_3: float,
    omega_0_bunch: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64], None]:
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

    delta_phi = omega_0_bunch * delta_s / (math.sqrt(beta_in_squared) * c)
    gamma_phi = np.array([gamma_in, delta_phi])
    return r_zz[np.newaxis, :], gamma_phi[np.newaxis, :], None


def z_superposed_field_maps_rk4(
    gamma_in: float,
    d_z: float,
    n_steps: int,
    omega0_rf: float,
    delta_phi_norm: float,
    delta_gamma_norm: float,
    complex_e_func: FieldFuncComplexTimedComponent,
    real_e_func: FieldFuncTimedComponent,
) -> tuple[NDArray[np.float64], NDArray[np.float64], complex]:
    """Calculate the transfer matrix of superposed FIELD_MAP using RK."""
    return z_field_map_rk4(
        gamma_in=gamma_in,
        d_z=d_z,
        n_steps=n_steps,
        omega0_rf=omega0_rf,
        delta_phi_norm=delta_phi_norm,
        delta_gamma_norm=delta_gamma_norm,
        complex_e_func=complex_e_func,
        real_e_func=real_e_func,
    )


def z_field_map_leapfrog(
    d_z: float,
    gamma_in: float,
    n_steps: int,
    omega0_rf: float,
    k_e: float,
    phi_0_rel: float,
    e_spat: Callable[[float], float],
    q_adim: float,
    inv_e_rest_mev: float,
    gamma_init: float,
    omega_0_bunch: float,
    **kwargs,
) -> tuple[NDArray[np.float64], NDArray[np.float64], float]:
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
    raise NotImplementedError
