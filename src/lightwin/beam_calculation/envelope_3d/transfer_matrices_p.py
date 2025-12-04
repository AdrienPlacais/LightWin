"""Define every element transfer matrix.

Units are taken exactly as in TraceWin, i.e. fifth line is ``z (m)`` and
sixth line is ``dp/p``.

.. todo::
    3D field maps?

.. todo::
    Maybe it would be clearer to compose r_xx, r_yy, r_zz. As an example, the
    zz_drift is used in several places.

.. todo::
    Will be necessary to separate this module into several sub-packages

"""

import math

import numpy as np
from numpy.typing import NDArray

from lightwin.beam_calculation.integrators.rk4 import rk4
from lightwin.constants import c
from lightwin.core.em_fields.types import (
    FieldFuncComplexTimedComponent,
    FieldFuncComponent,
    FieldFuncTimedComponent,
)


def dummy(
    gamma_in: float, *args, **kwargs
) -> tuple[NDArray[np.float64], NDArray[np.float64], None]:
    """Return an eye transfer matrix."""
    return np.eye(6), np.array([[gamma_in, 0.0]]), None


def drift(
    gamma_in: float,
    delta_s: float,
    omega_0_bunch: float,
    n_steps: int = 1,
) -> tuple[NDArray[np.float64], NDArray[np.float64], None]:
    """Calculate the transfer matrix of a drift.

    Parameters
    ----------
    gamma_in :
        Lorentz gamma at entry of drift.
    delta_s :
        Size of the drift in :unit:`mm`.
    omega_0_bunch :
        Pulsation of the beam.
    n_steps :
        Number of integration steps. The number of integration steps has no
        influence on the results. The default is one. It is different from
        unity when crossing a failed field map, as it allows to keep the same
        size of ``transfer_matrix`` and ``gamma_phi`` between nominal and fixed
        linacs.

    Returns
    -------
    NDArray[np.float64]
        ``(n_steps, 6, 6)`` array containing the transfer matrices.
    NDArray[np.float64]
        ``(n_steps, 2)`` with Lorentz gamma in first column and relative phase in
        second column.
    None
        Dummy variable for consistency with the field map function.

    """
    gamma_in_min2 = gamma_in**-2
    transfer_matrix = np.full(
        (n_steps, 6, 6),
        np.array(
            [
                [1.0, delta_s, 0.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, delta_s, 0.0, 0.0],
                [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 1.0, delta_s * gamma_in_min2],
                [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
            ]
        ),
    )
    beta_in = math.sqrt(1.0 - gamma_in_min2)
    delta_phi = omega_0_bunch * delta_s / (beta_in * c)

    gamma_phi = np.empty((n_steps, 2))
    gamma_phi[:, 0] = gamma_in
    gamma_phi[:, 1] = np.arange(0.0, n_steps) * delta_phi + delta_phi
    return transfer_matrix, gamma_phi, None


def quad(
    gamma_in: float,
    delta_s: float,
    gradient: float,
    omega_0_bunch: float,
    q_adim: float,
    e_rest_mev: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64], None]:
    """Calculate the transfer matrix of a quadrupole.

    .. todo::
       There is room for speeding up this function. Could have one function for
       focusing and one for defocusing. Magnetic rigidity, focusing strength
       could be calculated inline.

    Parameters
    ----------
    delta_s :
        Size of the drift in :unit:`m`.
    gamma_in :
        Lorentz gamma at entry of drift.
    n_steps :
        Number of integration steps. The number of integration steps has no
        influence on the results. The default is one. It is different from
        unity when crossing a failed field map, as it allows to keep the same
        size of ``transfer_matrix`` and ``gamma_phi`` between nominal and fixed
        linacs.
    gradient :
        Quadrupole gradient in :unit:`T/m`.
    omega_0_bunch :
        Pulsation of the beam.
    q_adim :
        Adimensioned charge of accelerated particle.
    e_rest_mev :
        Rest energy of the accelerated particle.

    Returns
    -------
    NDArray[np.float64]
        ``(1, 6, 6)`` array containing the transfer matrices.
    NDArray[np.float64]
        ``(1, 2)`` array with Lorentz factor in first column and relative phase
        in second column.
    None
        Dummy variable for consistency with the field map function.

    """
    gamma_in_min2 = gamma_in**-2
    beta_in = math.sqrt(1.0 - gamma_in_min2)

    delta_phi = omega_0_bunch * delta_s / (beta_in * c)
    gamma_phi = np.empty((1, 2))
    gamma_phi[:, 0] = gamma_in
    gamma_phi[:, 1] = np.arange(0.0, 1) * delta_phi + delta_phi

    magnetic_rigidity = _magnetic_rigidity(
        beta_in, gamma_in, e_rest_mev=e_rest_mev
    )
    focusing_strength = _focusing_strength(gradient, magnetic_rigidity)

    if q_adim * gradient > 0.0:
        transfer_matrix = _horizontal_focusing_quadrupole(
            focusing_strength, delta_s, gamma_in_min2
        )
        return transfer_matrix, gamma_phi, None

    transfer_matrix = _horizontal_defocusing_quadrupole(
        focusing_strength, delta_s, gamma_in_min2
    )
    return transfer_matrix, gamma_phi, None


def _horizontal_focusing_quadrupole(
    focusing_strength: float, delta_s: float, gamma_in_min2: float
) -> NDArray[np.float64]:
    """Transfer matrix of a quadrupole focusing in horizontal plane."""
    _cos, _cosh, _sin, _sinh = _quadrupole_trigo_hyperbolic(
        focusing_strength, delta_s
    )
    transfer_matrix = np.full(
        (1, 6, 6),
        np.array(
            [
                [_cos, _sin / focusing_strength, 0.0, 0.0, 0.0, 0.0],
                [-focusing_strength * _sin, _cos, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, _cosh, _sinh / focusing_strength, 0.0, 0.0],
                [0.0, 0.0, focusing_strength * _sinh, _cosh, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 1.0, delta_s * gamma_in_min2],
                [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
            ]
        ),
    )
    return transfer_matrix


def _horizontal_defocusing_quadrupole(
    focusing_strength: float, delta_s: float, gamma_in_min2: float
) -> NDArray[np.float64]:
    """Transfer matrix of a quadrupole defocusing in horizontal plane."""
    _cos, _cosh, _sin, _sinh = _quadrupole_trigo_hyperbolic(
        focusing_strength, delta_s
    )
    transfer_matrix = np.full(
        (1, 6, 6),
        np.array(
            [
                [_cosh, _sinh / focusing_strength, 0.0, 0.0, 0.0, 0.0],
                [focusing_strength * _sinh, _cosh, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, _cos, _sin / focusing_strength, 0.0, 0.0],
                [0.0, 0.0, -focusing_strength * _sin, _cos, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 1.0, delta_s * gamma_in_min2],
                [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
            ]
        ),
    )
    return transfer_matrix


def field_map_rk4(
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
        :math:`6\times 6 \times n` matrix, holding the :math:`2\times2`
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

    transfer_matrix = np.empty([n_steps, 6, 6])
    gamma_phi = np.empty((n_steps + 1, 2))
    gamma_phi[0, :] = [gamma_in, 0.0]

    def du(z: float, u: NDArray[np.float64]) -> NDArray[np.float64]:
        r"""Compute variation of energy and phase.

        Parameters
        ----------
        z :
            Position where variation is calculated.
        u :
            First component is gamma. Second is phase in :unit:`rad`.

        Return
        ------
            First component is :math:`\delta gamma / \delta z` in :unit:`MeV/m`.
            Second is :math:`\delta \phi / \delta z` in :unit:`rad/m`.

        """
        v0 = delta_gamma_norm * real_e_func(z, u[1])
        beta = math.sqrt(1.0 - u[0] ** -2)
        v1 = delta_phi_norm / beta
        return np.array([v0, v1])

    for i in range(n_steps):
        delta_gamma_phi = rk4(u=gamma_phi[i, :], du=du, x=z_rel, dx=d_z)
        gamma_phi[i + 1, :] = gamma_phi[i, :] + delta_gamma_phi
        itg_field += complex_e_func(z_rel, gamma_phi[i, 1]) * d_z

        gamma_phi_middle = gamma_phi[i, :] + 0.5 * delta_gamma_phi
        gamma_m = gamma_phi_middle[0]
        phi_m = gamma_phi_middle[1]

        scaled_e_middle = delta_gamma_norm * complex_e_func(
            z_rel + half_dz, phi_m
        )
        scaled_delta_e = (
            delta_gamma_norm
            * (
                real_e_func(z_rel + 0.9999998 * d_z, phi_m)
                - real_e_func(z_rel, phi_m)
            )
            / d_z
        )
        # The term 0.9999998 to ensure the final step in inside the range for
        # the interpolation

        transfer_matrix[i, :, :] = thin_lense(
            scaled_e_middle,
            scaled_delta_e,
            gamma_phi[i, 0],
            gamma_phi[i + 1, 0],
            gamma_m,
            half_dz,
            omega0_rf,
        )

        z_rel += d_z

    return transfer_matrix, gamma_phi[1:, :], itg_field


def thin_lense(
    scaled_e_middle: complex,
    scaled_delta_e: float,
    gamma_in: float,
    gamma_out: float,
    gamma_m: float,
    half_dz: float,
    omega0_rf: float,
) -> NDArray[np.float64]:
    r"""
    Compute propagation in a slice of field map using thin lense approximation.

    Thin lense approximation: drift-acceleration-drift. The transfer matrix of
    the thin accelerating gap is:

    .. math::

        \begin{bmatrix}
            1       & 1       & 0       & 0       & 0       & 0      \\
            k_{1xy} & k_{2xy} & 0       & 0       & 0       & 0      \\
            0       & 0       & 1       & 1       & 0       & 0      \\
            0       & 0       & k_{1xy} & k_{2xy} & 0       & 0      \\
            0       & 0       & 0       & 0       & k_{3z}  & 1      \\
            0       & 0       & 0       & 0       & k_{1z}  & k_{2z} \\
        \end{bmatrix}

    Where:

    .. math::

        \left\{
        \begin{aligned}
            k_{1z} &= \Im(\widetilde{E}) \frac{\omega_0}{\beta_m c} \\
            k_{2z} &= 1 - (2 - \beta_m^2)\Re(\widetilde{E}) \\
            k_{3z} &= \frac{1 - \Re(\widetilde{E})}{k_{2z}}
        \end{aligned}
        \right.

    and:

    .. math::

        \left\{
        \begin{aligned}
            k_{1xy} &=
                \frac{1}{2}
                \left(
                \Im(\widetilde{E}) \frac{\omega_0 \beta_m}{c} - \Delta E
                \right) \\
            k_{2xy} &= 1 - \Re(\widetilde{E})
        \end{aligned}
        \right.

    We use:

    .. math::
        \left\{
        \begin{aligned}
            \widetilde{E} &=
                \frac{\Delta\gamma_\mathrm{norm}}{\gamma_m\beta_m^2}
                \widetilde{E_z}\left(z + \frac{\Delta z}{2}, \phi_m\right) \\
            \Delta E &=
                \frac{\Delta\gamma_\mathrm{norm}}{\gamma_m\beta_m^2}
                \Re\left(
                \widetilde{E_z}(z + \Delta z, \phi_m) - \widetilde{E_z}(z, \phi_m)
                \right)
        \end{aligned}
        \right.

    In the script, :math:`\widetilde{E}` is ``scaled_e_middle_norm``, and
    :math:`\gamma_m\beta_m^2\Delta E` is ``scaled_delta_e``.

    Quantities with a :math:`m` subscript are taken at the middle of the
    accelerating gap. :math:`i` are in the first drift, :math:`i+1` in the
    second.

    .. note::
       **In TraceWin documentation:**

          - :math:`k_{1z}` and :math:`k_{2z}` are called :math:`K_1` and
            :math:`K_2`. They miss a :math:`\Delta z` term.
          - :math:`k_{1xy}` and :math:`k_{2xy}` are called :math:`k_1` and
            :math:`k_2`.
          - Our complex electric field :math:`\widetilde{E_z}` would be
            written:

            .. math::

                \widetilde{E_z} = E_0
                    \sin{
                        \left( \frac{Kz}{\beta_c} \right)
                    }
                    \left[
                        \cos{(\omega t_s + \varphi_0)}
                        + j\sin{(\omega t_s + \varphi_0)}
                    \right]

          - Constants used to speed up calculations:

            .. math::
                \left\{
                \begin{aligned}
                    \Delta\gamma_\mathrm{norm} &= \frac{q_\mathrm{adim} \Delta z}
                    {E_\mathrm{rest}}\\
                    \Delta\phi_\mathrm{norm} &= \frac{\omega_0 \Delta z}{c}
                \end{aligned}
                \right.

    Parameters
    ----------
    scaled_e_middle :
        Complex electric field in the accelerating gap multiplied by
        :math:`\Delta\gamma_\mathrm{norm}`. We normalize this quantity by
        :math:`\gamma_m\beta_m^2` in the routine to obtain
        :math:`\widetilde{E}`.

        .. math::
           \Delta\gamma_\mathrm{norm}
           \widetilde{E_z}\left(z + \frac{\Delta z}{2}, \phi_m\right)

    scaled_delta_e :
        Electric field multiplied by :math:`\Delta\gamma_\mathrm{norm}` and
        differenciated between start and and of the thin lense.

        .. math::
           \Delta\gamma_\mathrm{norm} \frac{
                E_z(z + \Delta z, \phi_m) - E_z(z, \phi_m)
            }{
                \Delta z
            }

    gamma_in :
        Lorentz factor at entrance of first drift.
    gamma_out :
        Lorentz factor at exit of first drift.
    gamma_m :
        Lorentz factor at the thin acceleration gap.
    half_dz :
        Half a spatial step in :unit:`m`.
    omega0_rf :
        Pulsation of the cavity.

    Return
    ------
        ``(1, 6, 6)`` transfer matrix of the thin lense.

    """
    beta_m = math.sqrt(1.0 - gamma_m**-2)
    denom = gamma_m * beta_m**2

    scaled_e_middle_norm = scaled_e_middle / denom

    k_1z = scaled_e_middle_norm.imag * omega0_rf / (beta_m * c)
    k_2z = 1.0 - (2.0 - beta_m**2) * scaled_e_middle_norm.real
    k_3z = (1.0 - scaled_e_middle_norm.real) / k_2z

    k_1xy = 0.5 * (
        scaled_e_middle_norm.imag * omega0_rf * beta_m / c
        - scaled_delta_e / denom
    )
    k_2xy = 1 - scaled_e_middle_norm.real

    r = _drift_matrix(gamma_out, half_dz)
    g = _drift_matrix(gamma_in, half_dz)
    thin = np.array(
        [
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [k_1xy, k_2xy, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, k_1xy, k_2xy, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, k_3z, 0.0],
            [0.0, 0.0, 0.0, 0.0, k_1z, k_2z],
        ]
    )
    return r @ thin @ g


# =============================================================================
# Helpers
# =============================================================================
def _magnetic_rigidity(beta: float, gamma: float, e_rest_mev: float) -> float:
    """Compute magnetic rigidity of particle."""
    return 1e6 * e_rest_mev * beta * gamma / c


def _focusing_strength(gradient: float, magnetic_rigidity: float) -> float:
    """Compute focusing strength of the quadrupole."""
    return math.sqrt(abs(gradient / magnetic_rigidity))


def _quadrupole_trigo_hyperbolic(
    focusing_strength: float, delta_s: float
) -> tuple[float, float, float, float]:
    """Pre-compute some parameters for the quadrupole transfer matrix."""
    kdelta_s = focusing_strength * delta_s
    return (
        math.cos(kdelta_s),
        math.cosh(kdelta_s),
        math.sin(kdelta_s),
        math.sinh(kdelta_s),
    )


def _drift_matrix(gamma: float, half_dz: float) -> NDArray[np.float64]:
    return np.array(
        [
            [1.0, half_dz, 0.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, half_dz, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 1.0, half_dz * gamma**-2],
            [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
