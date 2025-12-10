#cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True
import math

cimport cython
cimport numpy as np
from libc.math cimport cos, sin, sqrt

import numpy as np

# This would need special .pxd file
# from lightwin.core.em_fields.cy_field_helpers cimport RealEzFuncCython, ComplexEzFuncCython
from lightwin.core.em_fields.cy_field_helpers import (
    ComplexEzFuncCython,
    RealEzFuncCython,
)

# Typedef for convenience
ctypedef np.float64_t DTYPE_t
cdef double c = 299792458.0  # speed of light
from cython.view cimport array as cvarray


def z_dummy(double gamma_in):
    """Return an identity transfer matrix (dummy)."""
    cdef np.ndarray[DTYPE_t, ndim=3] r_zz = np.array(
        [
            [
                [1.0, 0.0],
                [0.0, 1.0]
            ]
        ],
        dtype=np.float64)
    cdef np.ndarray[DTYPE_t, ndim=2] gamma_phi = np.array([[gamma_in, 0.0]],
                                                          dtype=np.float64)
    return r_zz, gamma_phi, None

def z_drift(
        double gamma_in,
        double delta_s,
        double omega_0_bunch,
        int n_steps = 1,
    ):
    """Calculate the transfer matrix of a drift."""
    cdef double gamma_in_min2 = 1.0 / (gamma_in * gamma_in)
    cdef double beta_in = sqrt(1.0 - gamma_in_min2)
    cdef double delta_phi = omega_0_bunch * delta_s / (beta_in * c)

    cdef np.ndarray[DTYPE_t, ndim=3] r_zz = np.empty((n_steps, 2, 2),
                                                     dtype=np.float64)
    cdef int i
    for i in range(n_steps):
        r_zz[i, 0, 0] = 1.0
        r_zz[i, 0, 1] = delta_s * gamma_in_min2
        r_zz[i, 1, 0] = 0.0
        r_zz[i, 1, 1] = 1.0

    cdef np.ndarray[DTYPE_t, ndim=2] gamma_phi = np.empty((n_steps, 2),
                                                          dtype=np.float64)
    for i in range(n_steps):
        gamma_phi[i, 0] = gamma_in
        gamma_phi[i, 1] = delta_phi * (i + 1)

    return r_zz, gamma_phi, None

def z_field_map_rk4(
        double gamma_in,
        double d_z,
        int n_steps,
        double omega0_rf,
        double delta_phi_norm,
        double delta_gamma_norm,
        object complex_e_func,
        object real_e_func,
    ):
    cdef double z_rel = 0.0
    cdef complex itg_field = 0.0
    cdef double half_dz = 0.5 * d_z

    cdef np.ndarray[np.float64_t, ndim=3] r_zz = np.empty((n_steps, 2, 2), dtype=np.float64)
    cdef np.ndarray[np.float64_t, ndim=1] gamma = np.empty(n_steps+1, dtype=np.float64)
    gamma[0] = gamma_in

    cdef np.ndarray[np.float64_t, ndim=1] phi = np.empty(n_steps+1, dtype=np.float64)
    phi[0] = 0.0

    cdef np.ndarray[np.float64_t, ndim=2] gamma_phi = np.empty((n_steps, 2), dtype=np.float64)

    cdef double gamma_middle, phi_middle
    cdef double k1u, k1v, k2u, k2v, k3u, k3v, k4u, k4v
    cdef double u, v, beta, du1, du2, dz_local
    cdef int i
    cdef double delta_gamma, delta_phi

    cdef complex scaled_e_middle

    for i in range(n_steps):
        k1u = delta_gamma_norm * real_e_func(z_rel, phi[i])
        beta = sqrt(1.0 - gamma[i]**-2)
        k1v = delta_phi_norm / beta

        k2u = delta_gamma_norm * real_e_func(
            z_rel + half_dz,
            phi[i] + 0.5 * k1v
        )
        beta = sqrt(1.0 - (gamma[i] + 0.5 * k1u)**-2)
        k2v = delta_phi_norm / beta

        k3u = delta_gamma_norm * real_e_func(
            z_rel + half_dz,
            phi[i] + 0.5 * k2v
        )
        beta = sqrt(1.0 - (gamma[i] + 0.5 * k2u)**-2)
        k3v = delta_phi_norm / beta

        k4u = delta_gamma_norm * real_e_func(z_rel + d_z, phi[i] + k3v)
        beta = sqrt(1.0 - (gamma[i] + k3u)**-2)
        k4v = delta_phi_norm / beta

        delta_gamma = (k1u + 2.0 * k2u + 2.0 * k3u + k4u) / 6.0
        delta_phi = (k1v + 2.0 * k2v + 2.0 * k3v + k4v) / 6.0
        gamma[i + 1] = gamma[i] + delta_gamma
        phi[i + 1] = phi[i] + delta_phi

        itg_field += complex_e_func(z_rel, phi[i]) * d_z

        scaled_e_middle = delta_gamma_norm * complex_e_func(
            z_rel + half_dz,
            phi[i] + 0.5 * delta_phi,
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

    gamma_phi[:, 0] = gamma[1:]
    gamma_phi[:, 1] = phi[1:]
    return r_zz, gamma_phi, itg_field

def z_thin_lense(
    complex scaled_e_middle,
    double gamma_in,
    double gamma_out,
    double gamma_middle,
    double half_dz,
    double omega0_rf,
) -> object:
    """
    Compute 2x2 thin lens transfer matrix in Cython.

    scaled_e_middle_real/imag: real and imag of scaled complex E field
    """
    cdef double beta_m = math.sqrt(1.0 - 1.0 / (gamma_middle * gamma_middle))
    cdef double k1, k2, k3

    scaled_e_middle /= gamma_middle * beta_m * beta_m

    k1 = scaled_e_middle.imag * omega0_rf / (beta_m * c)
    k2 = 1.0 - (2.0 - beta_m * beta_m) * scaled_e_middle.real
    k3 = (1.0 - scaled_e_middle.real) / k2

    # build drift matrices
    cdef double g00 = 1.0
    cdef double g01 = half_dz / (gamma_in * gamma_in)
    cdef double g10 = 0.0
    cdef double g11 = 1.0

    cdef double r00 = 1.0
    cdef double r01 = half_dz / (gamma_out * gamma_out)
    cdef double r10 = 0.0
    cdef double r11 = 1.0

    # thin lens matrix
    cdef double t00 = k3
    cdef double t01 = 0.0
    cdef double t10 = k1
    cdef double t11 = k2

    # explicit multiplication r @ t @ g
    cdef double m00, m01, m10, m11

    # temp = t @ g
    cdef double tmp00 = t00 * g00 + t01 * g10
    cdef double tmp01 = t00 * g01 + t01 * g11
    cdef double tmp10 = t10 * g00 + t11 * g10
    cdef double tmp11 = t10 * g01 + t11 * g11

    # m = r @ tmp
    m00 = r00 * tmp00 + r01 * tmp10
    m01 = r00 * tmp01 + r01 * tmp11
    m10 = r10 * tmp00 + r11 * tmp10
    m11 = r10 * tmp01 + r11 * tmp11

    cdef np.ndarray[np.float64_t, ndim=2] mat = np.empty((2, 2), dtype=np.float64)
    mat[0, 0] = m00
    mat[0, 1] = m01
    mat[1, 0] = m10
    mat[1, 1] = m11

    return mat

def z_superposed_field_maps_rk4(
    double gamma_in,
    double d_z,
    int n_steps,
    double omega0_rf,
    object complex_e_func,
    object real_e_func,
    double q_adim,
    double inv_e_rest_mev,
    double omega_0_bunch,
):
    """Call classic RK4; placeholder to match Python signature."""
    return z_field_map_rk4(
        gamma_in, 0.0, d_z, n_steps,
        q_adim * d_z * inv_e_rest_mev,
        omega0_rf * d_z / 3e8,
        real_e_func,
        complex_e_func,
        omega_0_bunch
    )


def z_bend(double gamma_in, double delta_s,
           double factor_1, double factor_2, double factor_3,
           double omega_0_bunch):
    """Compute longitudinal transfer matrix of a bend."""
    cdef double gamma_in_min2 = 1.0 / (gamma_in * gamma_in)
    cdef double beta_in_squared = 1.0 - gamma_in_min2

    cdef double topright = factor_1 * beta_in_squared + factor_2 + factor_3 * gamma_in_min2

    cdef np.ndarray[DTYPE_t, ndim=3] r_zz = np.eye(2, dtype=np.float64)[np.newaxis, :, :]
    r_zz[0, 0, 1] = topright

    cdef np.ndarray[DTYPE_t, ndim=2] gamma_phi = np.empty((1, 2), dtype=np.float64)
    gamma_phi[0, 0] = gamma_in
    gamma_phi[0, 1] = omega_0_bunch * delta_s / sqrt(beta_in_squared * 3e8**2)

    return r_zz, gamma_phi, None
