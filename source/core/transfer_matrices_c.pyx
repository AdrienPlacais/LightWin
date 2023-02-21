#!/usr/bin/env python3
#cython: language_level=3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 22 16:04:34 2021.

@author: placais

This file holds the same functions as transfer_matrices_p, but in Cython.

Cython needs to be compiled to work. Check the instrutions in setup.py.

Currently adapted to MYRRHA only:
    electric fields are hard-coded;
    energy at linac entrance is hard-coded.

# TODO field maps better to create the transfer matrix in one passage at the end?
# TODO try to put more cdef functions
"""
import cython
from libc.math cimport sin, cos, sqrt, tan, floor
import numpy as np
cimport numpy as np
np.import_array()
from constants import c, E_REST_MEV, INV_E_REST_MEV, Q_ADIM, OMEGA_0_BUNCH, \
    GAMMA_INIT

# Must be changed to double if C float is replaced by double
DTYPE = np.float64
#  ctypedef np.float64_t DTYPE_t
# DTYPE = double
ctypedef double DTYPE_t

cdef DTYPE_t c_cdef = c
cdef DTYPE_t E_rest_MeV_cdef = E_REST_MEV
cdef DTYPE_t inv_E_rest_MeV_cdef = INV_E_REST_MEV
cdef DTYPE_t OMEGA_0_BUNCH_cdef = OMEGA_0_BUNCH
cdef DTYPE_t q_adim_cdef = Q_ADIM
cdef DTYPE_t GAMMA_cdef = GAMMA_INIT
# cdef DTYPE_t c_cdef = 2.99792458e8
# cdef DTYPE_t E_rest_MeV_cdef = 938.27203
# cdef DTYPE_t inv_E_rest_MeV_cdef = 0.0010657889908537506
# cdef DTYPE_t OMEGA_0_BUNCH_cdef = 1106468932.594325
# cdef DTYPE_t q_adim_cdef = 1.
# cdef DTYPE_t E_MEV_cdef = 16.6
# cdef DTYPE_t GAMMA_cdef = 1. + E_MEV_cdef / E_rest_MeV_cdef


cpdef init_arrays(list l_filepaths):
    """Initialize electric fields for efficiency."""
    cdef int n_points = 0
    cdef Py_ssize_t i
    cdef DTYPE_t inv_dz = 0.
    cdef DTYPE_t[:] e_z
    global l_d_ez

    l_d_ez = []
    for filepath in l_filepaths:
        with open(filepath) as file:
            for i, line in enumerate(file):
                if i == 0:
                    n_points = int(line.split()[0]) + 1
                    inv_dz = float(n_points - 1) / float(line.split()[1])
                    e_z = np.empty([n_points], dtype=DTYPE)
                elif i > 1:
                    e_z[i - 2] = float(line)
        l_d_ez.append({"e_z": e_z, "n_points": n_points, "inv_dz": inv_dz})


# =============================================================================
# Helpers
# =============================================================================
cdef DTYPE_t interp(DTYPE_t z, DTYPE_t[:] e_z, DTYPE_t inv_dz_e, int n_points_e):
    """Interpolation function."""
    cdef Py_ssize_t i
    cdef DTYPE_t delta_e_z, slope, offset
    cdef out

    if z < 0. or z > (n_points_e - 1) / inv_dz_e:
        out = 0.

    else:
        i =  int(floor(z * inv_dz_e))
        if i < n_points_e - 1:
            # Faster with array of delta electric field?
            delta_e_z = e_z[i + 1] - e_z[i]
            slope = delta_e_z * inv_dz_e
            offset = e_z[i] - i * delta_e_z
            out = slope * z + offset
        else:
            out = e_z[n_points_e]

    return out


# =============================================================================
# Electric field functions
# =============================================================================
cdef DTYPE_t e_func(DTYPE_t z, DTYPE_t[:] e_z, DTYPE_t inv_dz_e,
                    int n_points_e, DTYPE_t phi, DTYPE_t phi_0):
    """
    Give the electric field at position z and phase phi.

    The field is normalized and should be multiplied by k_e.
    """
    return interp(z, e_z, inv_dz_e, n_points_e) * cos(phi + phi_0)


# =============================================================================
# Motion integration functions
# =============================================================================
cdef rk4(DTYPE_t z, DTYPE_t[:] u,
         DTYPE_t dz_s, DTYPE_t k_k, DTYPE_t[:] e_z, DTYPE_t inv_dz_e,
         int n_points_e, DTYPE_t phi_0_rel, DTYPE_t delta_phi_norm):
    """
    Integrate the motion over the space step.

    Warning: this is a slightly modified version of the RK. The k_i are
    proportional to delta_u instead of du_dz.
    """
    # Variables:
    cdef DTYPE_t half_dz_s = .5 * dz_s
    cdef Py_ssize_t i

    # Memory views:
    delta_u_array = np.empty(2, dtype=DTYPE)
    cdef DTYPE_t[:] delta_u = delta_u_array

    k_i_array = np.zeros((4, 2), dtype=DTYPE)
    cdef DTYPE_t[:, :] k_i = k_i_array

    delta_u_i_array = np.zeros((2), dtype=DTYPE)
    cdef DTYPE_t[:] delta_u_i = delta_u_i_array

    tmp_array = np.zeros((2), dtype=DTYPE)
    cdef DTYPE_t[:] tmp = tmp_array

    # Equiv of k_1 = du_dx(x, u):
    delta_u_i = du(z, u,
                   k_k, e_z, inv_dz_e, n_points_e, phi_0_rel, delta_phi_norm)
    k_i[0, 0] = delta_u_i[0]
    k_i[0, 1] = delta_u_i[1]

    # Compute tmp = u + half_dx * k_1
    # Equiv of k_2 = du_dx(x + half_dx, u + half_dx * k_1)
    # Compute tmp = u + half_dx * k_2
    # Equiv of k_3 = du_dx(x + half_dx, u + half_dx * k_2)
    for i in [1, 2]:
        tmp[0] = u[0] + .5 * k_i[i - 1, 0]
        tmp[1] = u[1] + .5 * k_i[i - 1, 1]
        delta_u_i = du(z + half_dz_s, tmp,
                        k_k, e_z, inv_dz_e, n_points_e, phi_0_rel, delta_phi_norm)
        k_i[i, 0] = delta_u_i[0]
        k_i[i, 1] = delta_u_i[1]

    # Compute u + dx * k_3
    tmp[0] = u[0] + k_i[2, 0]
    tmp[1] = u[1] + k_i[2, 1]
    # Equiv of k_4 = du_dx(x + dx, u + dx * k_3)
    delta_u_i = du(z + dz_s, tmp,
                    k_k, e_z, inv_dz_e, n_points_e, phi_0_rel, delta_phi_norm)
    k_i[3, 0] = delta_u_i[0]
    k_i[3, 1] = delta_u_i[1]

    # Equiv of delta_u = (k_1 + 2. * k_2 + 2. * k_3 + k_4) * dx / 6.
    delta_u[0] = (k_i[0, 0] + 2. * k_i[1, 0] + 2. * k_i[2, 0] + k_i[3, 0]) / 6.
    delta_u[1] = (k_i[0, 1] + 2. * k_i[1, 1] + 2. * k_i[2, 1] + k_i[3, 1]) / 6.
    return delta_u_array


cdef du(DTYPE_t z_rel, DTYPE_t[:] u,
           DTYPE_t k_k, DTYPE_t[:] e_z, DTYPE_t inv_dz_e, int n_points_e,
           DTYPE_t phi_0_rel, DTYPE_t delta_phi_norm):
    """Variation of u during spatial step."""
    # Variables:
    cdef DTYPE_t beta = sqrt(1. - u[0]**-2)

    # Memory views:
    v_array = np.empty(2, dtype=DTYPE)
    cdef DTYPE_t[:] v = v_array

    v[0] = k_k * e_func(z_rel, e_z, inv_dz_e, n_points_e, u[1], phi_0_rel)
    v[1] = delta_phi_norm / beta
    return v_array

# =============================================================================
# Transfer matrices
# =============================================================================
cpdef z_drift(DTYPE_t delta_s, DTYPE_t gamma_in, np.int64_t n_steps=1):
    """Calculate the transfer matrix of a drift."""
    # Variables:
    cdef DTYPE_t gamma_in_min2 = gamma_in**-2
    cdef DTYPE_t beta_in = sqrt(1. - gamma_in_min2)
    cdef DTYPE_t delta_phi = OMEGA_0_BUNCH_cdef * delta_s / (beta_in * c_cdef)
    cdef Py_ssize_t i

    # Memory views:
    gamma_phi_array = np.empty([n_steps, 2], dtype=DTYPE)
    cdef DTYPE_t[:, :] gamma_phi = gamma_phi_array

    cdef np.ndarray[DTYPE_t, ndim=3] r_zz_array = np.full(
        [n_steps, 2, 2],
        np.array([[1., delta_s * gamma_in_min2],
                  [0., 1.]], dtype=DTYPE),
        dtype=DTYPE)

    for i in range(n_steps):
        gamma_phi[i, 0] = gamma_in
        gamma_phi[i, 1] = (i + 1) * delta_phi
    return r_zz_array, gamma_phi_array, None


cpdef z_field_map_rk4(DTYPE_t dz_s, DTYPE_t gamma_in, np.int64_t n_steps,
                      dict_rf_field):
    """Calculate the transfer matrix of a field map using Runge-Kutta."""
    cdef DTYPE_t omega0_rf = dict_rf_field['omega0_rf']
    cdef DTYPE_t k_e = dict_rf_field['k_e']
    cdef DTYPE_t phi_0_rel = dict_rf_field['phi_0_rel']
    cdef np.int64_t section_idx = dict_rf_field['section_idx']

    # Variables:
    cdef DTYPE_t z_rel = 0.
    cdef complex itg_field = 0.
    cdef DTYPE_t half_dz_s = .5 * dz_s
    cdef DTYPE_t beta = sqrt(1. - gamma_in**-2)
    cdef np.int64_t i
    cdef DTYPE_t tmp
    cdef DTYPE_t gamma_middle, phi_middle

    # Arrays:
    cdef np.ndarray[DTYPE_t, ndim=3] r_zz_array = np.empty([n_steps, 2, 2],
                                                           dtype=DTYPE)

    # Memory views:
    gamma_phi_array = np.empty((n_steps + 1, 2), dtype=DTYPE)
    delta_gamma_phi_array = np.zeros((2), dtype=DTYPE)
    cdef DTYPE_t[:, :] gamma_phi = gamma_phi_array
    cdef DTYPE_t[:] delta_gammma_phi = delta_gamma_phi_array
    cdef DTYPE_t[:] e_z
    cdef DTYPE_t inv_dz_e
    cdef int n_points_e

    # Constants to speed up calculation
    cdef DTYPE_t delta_phi_norm = omega0_rf * dz_s / c_cdef
    cdef DTYPE_t delta_gamma_norm = q_adim_cdef * dz_s * inv_E_rest_MeV_cdef
    cdef DTYPE_t k_k = delta_gamma_norm * k_e
    cdef DTYPE_t delta_gamma_m_max

    inv_dz_e = l_d_ez[section_idx]["inv_dz"]
    e_z = l_d_ez[section_idx]["e_z"]
    n_points_e = l_d_ez[section_idx]["n_points"]

    # Initial values for gamma and relative phase
    gamma_phi[0, 0] = gamma_in
    gamma_phi[0, 1] = 0.

    for i in range(n_steps):
        # Compute gamma and phase changes
        delta_gamma_phi = rk4(z_rel, gamma_phi[i, :],
                              dz_s, k_k, e_z, inv_dz_e, n_points_e, phi_0_rel,
                              delta_phi_norm)

        # Update
        gamma_phi[i + 1, 0] = gamma_phi[i, 0] + delta_gamma_phi[0]
        gamma_phi[i + 1, 1] = gamma_phi[i, 1] + delta_gamma_phi[1]

        # For synchronous phase and accelerating potential
        itg_field += k_e * e_func(z_rel, e_z, inv_dz_e, n_points_e,
                                  gamma_phi[i, 1], phi_0_rel) \
            * (1. + 1j * tan(gamma_phi[i, 1] + phi_0_rel)) * dz_s

        # Compute gamma and phi at the middle of the thin lense
        gamma_middle = .5 * (gamma_phi[i, 0] + gamma_phi[i + 1, 0])
        phi_middle = gamma_phi[i, 1] + .5 * delta_gamma_phi[1]

        # To speed up (corresponds to the gamma_variation at the middle of the
        # thin lense at cos(phi + phi_0) = 1
        delta_gamma_middle_max = k_k * interp(z_rel + half_dz_s, e_z,
                                              inv_dz_e, n_points_e)

        # Compute thin lense transfer matrix
        r_zz_array[i, :, :] = z_thin_lense(
            gamma_phi[i, 0], gamma_middle, gamma_phi[i + 1, 0], phi_middle,
            half_dz_s, delta_gamma_middle_max, phi_0_rel, omega0_rf)

        z_rel += dz_s

    return r_zz_array, gamma_phi_array[1:, :], itg_field


cpdef z_field_map_leapfrog(DTYPE_t dz_s, DTYPE_t gamma_in, np.int64_t n_steps,
                           dict_rf_field):
    """Calculate the transfer matrix of a field map using leapfrog."""
    cdef DTYPE_t omega0_rf = dict_rf_field['omega0_rf']
    cdef DTYPE_t k_e = dict_rf_field['k_e']
    cdef DTYPE_t phi_0_rel = dict_rf_field['phi_0_rel']
    cdef np.int64_t section_idx = dict_rf_field['section_idx']
    # Variables:
    cdef DTYPE_t z_rel = 0.
    cdef complex itg_field = 0.
    cdef DTYPE_t beta_next
    cdef DTYPE_t beta = sqrt(1. - gamma_in**-2)
    cdef np.int64_t i
    cdef DTYPE_t tmp
    cdef DTYPE_t delta_gamma, delta_phi
    cdef DTYPE_t half_dz_s = .5 * dz_s

    # Arrays:
    cdef np.ndarray[DTYPE_t, ndim=3] r_zz_array = np.empty([n_steps, 2, 2],
                                                           dtype=DTYPE)

    # Memory views:
    gamma_phi_array = np.empty((n_steps + 1, 2), dtype=DTYPE)
    cdef DTYPE_t[:, :] gamma_phi = gamma_phi_array
    cdef DTYPE_t[:] e_z
    cdef DTYPE_t inv_dz_e
    cdef int n_points_e

    # Constants to speed up calculation
    cdef DTYPE_t delta_phi_norm = omega0_rf * dz_s / c_cdef
    cdef DTYPE_t delta_gamma_norm = q_adim_cdef * dz_s * inv_E_rest_MeV_cdef
    cdef DTYPE_t k_k = delta_gamma_norm * k_e
    cdef DTYPE_t delta_gamma_middle_max
    cdef DTYPE_t gamma_middle, phi_middle

    inv_dz_e = l_d_ez[section_idx]["inv_dz"]
    e_z = l_d_ez[section_idx]["e_z"]
    n_points_e = l_d_ez[section_idx]["n_points"]

    # Initial values for gamma and relative phase
    gamma_phi[0, 1] = 0.
    # Rewind energy from i=0 to i=-0.5 if we are at the first cavity:
    # FIXME must be cleaner
    if gamma_in == GAMMA_cdef:
        gamma_phi[0, 0] = gamma_in - 0.5 * k_k * e_func(
            z_rel, e_z, inv_dz_e, n_points_e, gamma_phi[0, 1], phi_0_rel)
    else:
        gamma_phi[0, 0] = gamma_in

    for i in range(n_steps):
        # Compute gamma change
        delta_gamma = k_k * e_func(z_rel, e_z, inv_dz_e, n_points_e,
                                   gamma_phi[i, 1], phi_0_rel)
        # New gamma at i + 0.5
        gamma_phi[i + 1, 0] = gamma_phi[i, 0] + delta_gamma
        beta = sqrt(1. - gamma_phi[i + 1, 0]**-2)

        # Compute phase at step i + 1
        delta_phi = delta_phi_norm / beta
        gamma_phi[i + 1, 1] = gamma_phi[i, 1] + delta_phi

        # For synchronous phase and accelerating potential
        itg_field += k_e * e_func(z_rel, e_z,
                                  inv_dz_e, n_points_e, gamma_phi[i, 1],
                                  phi_0_rel) \
            * (1. + 1j * tan(gamma_phi[i, 1] + phi_0_rel)) * dz_s

        # Compute gamma and phi at the middle of the thin lense
        gamma_middle = gamma_phi[i, 0]
        phi_middle = gamma_phi[i, 1] + .5 * delta_phi
        # We already are at the step i + 0.5, so gamma_middle and beta_middle
        # are the same as gamma and beta

        # To speed up (corresponds to the gamma_variation at the middle of the
        # thin lense at cos(phi + phi_0) = 1
        delta_gamma_middle_max = k_k * interp(z_rel + half_dz_s, e_z,
                                              inv_dz_e, n_points_e)
        # Compute thin lense transfer matrix
        r_zz_array[i, :, :] = z_thin_lense(
            gamma_phi[i, 0], gamma_middle, gamma_phi[i + 1, 0],
            phi_middle, half_dz_s, delta_gamma_middle_max, phi_0_rel,
            omega0_rf)

        z_rel += dz_s

    return r_zz_array, gamma_phi_array[1:, :], itg_field


cdef z_thin_lense(gamma_in, gamma_m, gamma_out, phi_m, half_dz_s,
                  delta_gamma_m_max, phi_0, omega0_rf):
    # Used for tm components
    cdef DTYPE_t beta_m = sqrt(1. - gamma_m**-2)
    cdef DTYPE_t k_speed1 = delta_gamma_m_max / (gamma_m * beta_m**2)
    cdef DTYPE_t k_speed2 = k_speed1 * cos(phi_m + phi_0)

    # Thin lense transfer matrices components
    cdef DTYPE_t k_1 = k_speed1 * omega0_rf / (beta_m * c_cdef) * sin(phi_m + phi_0)
    cdef DTYPE_t k_2 = 1. - (2. - beta_m**2) * k_speed2
    cdef DTYPE_t k_3 = (1. - k_speed2) / k_2

    # Middle transfer matrix components
    k_1 = k_speed1 * omega0_rf / (beta_m * c_cdef) * sin(phi_m + phi_0)
    k_2 = 1. - (2. - beta_m**2) * k_speed2
    k_3 = (1. - k_speed2) / k_2

    # Faster than matmul or matprod_22
    r_zz_array = z_drift(half_dz_s, gamma_out)[0][0] \
                 @ (np.array(([k_3, 0.], [k_1, k_2]), dtype=DTYPE) \
                    @ z_drift(half_dz_s, gamma_in)[0][0])
    return r_zz_array