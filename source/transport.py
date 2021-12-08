#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 9 14:26:45 2021

@author: placais
"""

import numpy as np
from palettable.colorbrewer.qualitative import Set1_9
import helper
from constants import q_adim, m_MeV, c
import solver
import particle
import debug


def transport_beam(accelerator):
    """
    Compute transfer matrices by the transport method.

    The idea is to transport the synchronous particle and two random particles.
    With the difference between synch and rand particles (phase_space) we can
    find the transfer matrix.

    Warning
    -------
        In this routine we track the phase of the particles:
            phi = omega0 * delta_z / (beta * c)
        Outside cavities, omega0 corresponds to the bunch pulsation. In
        cavities, it is the RF pulsation. When exiting the cavity, we recompute
        the phase with the bunch pulsation.
    """
    omega0_bunch = accelerator.list_of_elements[0].omega0_bunch

    synch, rand_1, rand_2 = particle.create_synch_and_rand_particles(
        16.6, omega0_bunch)

    for elt in accelerator.list_of_elements:
        n_steps = elt.solver_transf_mat.n_steps
        z_step = elt.solver_transf_mat.d_z

        if elt.accelerating:
            # Warning: in accelerating cavities, omega0 corresponds to the RF!
            omega0 = elt.acc_field.omega0_rf
            # Also warning: phi is computed with omega0... Thus the cavities
            # delta_phis shall be recomputed with omega0_bunch.
            for part in [synch, rand_1, rand_2]:
                part.enter_cavity(omega0)
        else:
            omega0 = omega0_bunch

        def du_dz(z, u):
            """
            Compute derivative of system energy/time.

            Parameters
            ----------
            u: np.array(2)
                First component is e_mev(i).
                Second component is phi(i).

            Return
            ------
            v: np.array(2)
                First component is (e_mev(i+1) - e_mev(i)) / dz.
                Second component is (phi(i+1) - phi(i)) / dz.
            """
            v0 = q_adim * elt.acc_field.e_func(z, u[1])

            gamma_float = helper.mev_to_gamma(u[0], m_MeV)
            beta = helper.gamma_to_beta(gamma_float)

            v1 = omega0 / (beta * c)

            return np.array(([v0, v1]))

        entrance_phase = synch.phi['rel']
        entrance_pos = synch.z['rel']

        for i in range(n_steps):
            # Compute energy, position and phase evolution during a time step
            for part in [synch, rand_1, rand_2]:
                if i == 0:
                    # Set relative phase and positions to 0.
                    part.z['rel'] -= entrance_pos
                    part.phi['rel'] -= entrance_phase

                u_rk = np.array(([part.energy['e_mev'], part.phi['rel']]))
                delta_u = solver.rk4(u_rk, du_dz, part.z['rel'], z_step)

                part.set_energy(delta_u[0], delta_e=True)
                part.advance_phi(delta_u[1])
                part.advance_position(z_step)

        # If this element was a cavity, we have to change the phase reference.
        if elt.accelerating:
            for part in [synch, rand_1, rand_2]:
                part.exit_cavity()

        # Raise some arrays to element
        elt.energy['gamma_array'] \
            = np.array(synch.energy['gamma_array'])[-n_steps:]
        elt.energy['e_array_mev'] \
            = np.array(synch.energy['e_array_mev'])[-n_steps:]

    for part in [synch, rand_1, rand_2]:
        # Convert lists into arrays:
        part.list_to_array()
        debug.simple_plot(synch.z['abs_array'],
                          part.energy['e_array_mev'],
                          'z_s', 'E mev', 34)
    for part in [rand_1, rand_2]:
        part.compute_phase_space(synch)

    accelerator.transfer_matrix_indiv = compute_transfer_matrix(rand_1, rand_2)


def compute_transfer_matrix(rand_1, rand_2):
    """Compute transfer matrix from the phase-space arrays."""
    n_steps = rand_1.phase_space['z_array'].size

    phase_space_matrix = np.dstack((rand_1.phase_space['both_array'],
                                    rand_2.phase_space['both_array']))

    transfer_matrix = np.full((n_steps, 2, 2), np.NaN)
    transfer_matrix[0, :, :] = np.eye(2)
    for i in range(1, n_steps):
        transfer_matrix[i, :, :] = phase_space_matrix[i, :, :] \
            @ np.linalg.inv(phase_space_matrix[i-1, :, :])
    return transfer_matrix


def compute_envelope(accelerator):
    """
    Compute the z | dp/p array evolution accross the accelerator.

    Parameters
    ----------
    accelerator: Accelerator object
        Longitudinal transfer matrices must have been calculated.
    """
    flag_compare = True

    fignum = 32
    axnum = range(211, 213)
    fig, axlist = helper.create_fig_if_not_exist(fignum, axnum)
    axlist[0].set_ylabel(r'$\phi$ [deg]')
    axlist[1].set_ylabel(r'd$p/p$ [%]')
    axlist[1].set_xlabel(r'$z_s$ [m]')

    if flag_compare:
        # @TODO auto import of correct file
        filepath = '/home/placais/TraceWin/work_field_map/results/envelope.txt'
        # File must be generated from Envelope Plot -> Save chart -> DATA ASCII
        # file
        data = np.loadtxt(filepath, skiprows=2, usecols=(0, 19, 17, 16))
        col = 'k'
        ls = '--'
        axlist[0].plot(data[:, 0], data[:, 3], ls=ls, c=col, label='TW')
        axlist[1].plot(data[:, 0], data[:, 2], ls=ls, c=col)

    transfer_matrix = accelerator.transfer_matrix_cumul
    pos = accelerator.get_from_elements('pos_m')

    n = transfer_matrix.shape[0]
    gamma = accelerator.get_from_elements('gamma_array')
    beta = helper.gamma_to_beta(gamma)

    # Assumption that the frequency won't change
    lambda_rf = accelerator.list_of_elements[5].acc_field.lambda_rf

    # Vectors of transverse dynamics
    transv = np.full((4, 2, n), np.NaN)

    # Initial delta phase of 11.5deg
    if flag_compare:
        delta_phi_0_deg = data[0, 1]
        delta_p_0 = data[0, 2]
        delta_z_0 = data[0, 3]

    else:
        delta_phi_0_deg = 11.55
        delta_p_0 = 0.005
        delta_z_0 = -beta[0] * lambda_rf * delta_phi_0_deg / 360.

    transv[0, :, 0] = np.array(([+delta_z_0, +delta_p_0]))
    transv[1, :, 0] = np.array(([+delta_z_0, -delta_p_0]))
    transv[2, :, 0] = np.array(([-delta_z_0, +delta_p_0]))
    transv[3, :, 0] = np.array(([-delta_z_0, -delta_p_0]))

    # Transport beam
    for i in range(n - 1):
        for j in range(4):
            transv[j, :, i + 1] = transfer_matrix[i + 1, :, :] \
                @ transv[j, :, 0]

    # Convert delta_z in phase
    col = (Set1_9.colors[0][0] / 256., Set1_9.colors[0][1] / 256.,
           Set1_9.colors[0][1] / 256.)
    ls = '-'
    label = ['LightWin', '']
    for i in range(2):
        axlist[i].plot(pos, np.max(transv[:, i, :], axis=0),
                       ls=ls, c=col, label=label[i])
        axlist[i].plot(pos, np.min(transv[:, i, :], axis=0),
                       ls=ls, c=col)
        axlist[i].grid(True)
    axlist[0].legend()
