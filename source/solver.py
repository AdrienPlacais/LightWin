#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 26 15:41:00 2021

@author: placais
"""

import numpy as np
from constants import c, q_adim, E_rest_MeV
import helper


# =============================================================================
# RK4
# =============================================================================
def init_rk4_cavity(cavity, gamma, synch):
    """Init RK4 methods to compute transfer matrix of a cavity."""
    gamma['out'] = gamma['in']
    synch.z['rel'] = 0.
    synch.phi['rel'] = 0.
    # TODO two last lines in enter_cavity?

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
        # v0 = q_adim * cavity.acc_field['e_func'](z, u[1])
        v0 = q_adim * cavity.acc_field.e_func(z, u[1])

        gamma_float = helper.kin_to_gamma(u[0], E_rest_MeV)
        beta = helper.gamma_to_beta(gamma_float)
        # v1 = cavity.acc_field['n_cell'] * synch.omega0['bunch'] / (beta * c)
        v1 = cavity.acc_field.n_cell * synch.omega0['bunch'] / (beta * c)
        return np.array(([v0, v1]))
    return du_dz


def rk4(u, du_dx, x, dx):
    """
    4-th order Runge-Kutta integration.

    This function calculates the variation of u between x and x+dx.

    Parameters
    ----------
    u: np.array
        Holds the value of the function to integrate in x.
    df_dx: function
        Gives the variation of u components with x.
    x: real
        Where u is known.
    dx: real
        Integration step.

    Return
    ------
    delta_u: real
        Variation of u between x and x+dx.
    """
    half_dx = .5 * dx
    k_1 = du_dx(x, u)
    k_2 = du_dx(x + half_dx, u + half_dx * k_1)
    k_3 = du_dx(x + half_dx, u + half_dx * k_2)
    k_4 = du_dx(x + dx, u + dx * k_3)
    delta_u = (k_1 + 2.*k_2 + 2.*k_3 + k_4) * dx / 6.
    return delta_u


# =============================================================================
# Leapfrog
# =============================================================================
def init_leapfrog_cavity(cavity, gamma, dz, synch):
    """Init leapfrog method to compute transfer matrix of cavity."""
    # Leapfrog method:
    #   pos(i+1) = pos(i) + speed(i+0.5) * dt
    #   speed(i+0.5) = speed(i-0.5) * accel(i) * dt
    # Here, dt is not fixed but dz.
    #   z(i+1) += dz
    #   t(i+1) = t(i) + dz / (c beta(i+1/2))
    #       (time and space variables are on whole steps)
    #   beta calculated from W(i+1/2) = W(i-1/2) + qE(i)dz
    #       (speed/energy are on half steps)
    # e_0_mev = cavity.energy['kin_array_mev'][0]

    # Remove last array element as it is on i and should be on i-1/2
    synch.energy['kin_array_mev'].pop(-1)
    synch.energy['gamma_array'].pop(-1)
    # Rewind energy
    # synch.set_energy(-q_adim * cavity.acc_field['e_func'](
    synch.set_energy(-q_adim * cavity.acc_field.e_func(
        synch.z['rel'], 0.) * .5 * dz, delta_e=True)
    # TODO in enter_cavity?
    synch.z['rel'] = 0.
    synch.phi['rel'] = 0.

    gamma['out'] = synch.energy['gamma']
