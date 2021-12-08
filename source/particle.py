#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  2 13:44:00 2021

@author: placais
"""

import numpy as np
import helper
from constants import m_MeV, c


class Particle():
    """Class to hold the position, energy, etc of a particle."""

    def __init__(self, z, e_mev, omega0_bunch):
        print('part init to: ', z, e_mev)
        self.z = {
            'abs': z,           # Position from the start of the line
            'rel': z,           # Position from the start of the element
            'abs_array': [z],
            }

        self.energy = {
            'e_mev': None,
            'gamma': None,
            'beta': None,
            'p': None,
            'e_array_mev': [],
            'gamma_array': [],
            'p_array': [],
            }
        self.set_energy(e_mev, delta_e=False)

        self.omega0 = {
            'ref': omega0_bunch,        # The one we use
            'bunch': omega0_bunch,      # Should match 'ref' outside cavities
            'rf': None,                 # Should match 'ref' inside cavities
            }

        self.phi = {
            'abs': None,
            'rel': None,
            'abs_deg': None,
            # Used to keep the delta phi on the whole cavity:
            'before_cavity': None
            }
        self.init_phi()

        self.phase_space = {
            'z_array': None,      # z_abs - s_abs or z_rel - s_rel
            'delta_array': None,  # (p - p_s) / p_s
            'both_array': None,
            }

    def set_energy(self, e_mev, delta_e=False):
        """
        Update the energy dict.

        If delta_e is True energy is increased by e_mev.
        If False, energy is set to e_mev.
        """
        if delta_e:
            if(delta_e < 0.):
                print('+ ', e_mev, 'MeV')
            self.energy['e_mev'] += e_mev
        else:
            # print('set to ', e_mev, 'MeV')
            self.energy['e_mev'] = e_mev

        self.energy['gamma'] = helper.mev_to_gamma(self.energy['e_mev'], m_MeV)
        self.energy['beta'] = helper.gamma_to_beta(self.energy['gamma'])
        self.energy['p'] = helper.gamma_and_beta_to_p(self.energy['gamma'],
                                                      self.energy['beta'])
        self.energy['e_array_mev'].append(self.energy['e_mev'])
        self.energy['gamma_array'].append(self.energy['gamma'])
        self.energy['p_array'].append(self.energy['p'])

    def advance_position(self, delta_pos):
        """Advance particle by delt_pos."""
        self.z['abs'] += delta_pos
        self.z['rel'] += delta_pos
        self.z['abs_array'].append(self.z['abs'])

    def init_phi(self):
        """Init phi by taking z_rel and beta."""
        self.phi['abs'] = self.omega0['ref'] * self.z['rel'] \
            / (self.energy['beta'] * c)
        self.phi['rel'] = self.phi['abs']
        self.phi['abs_deg'] = np.rad2deg(self.phi['abs'])

    def advance_phi(self, delta_phi):
        """Increase relative and absolute phase by delta_phi."""
        self.phi['abs'] += delta_phi
        self.phi['rel'] += delta_phi
        self.phi['abs_deg'] += np.rad2deg(delta_phi)

    def compute_phase_space(self, synch):
        """
        Compute phase-space array.

        synch_particle is an instance of Particle corresponding to the
        synchronous particle.
        """
        self.phase_space['z_array'] = self.z['abs_array'] \
            - synch.z['abs_array']
        self.phase_space['delta_array'] = (self.energy['p_array']
                                           - synch.energy['p_array']) \
            / synch.energy['p_array']

        self.phase_space['both_array'] = np.vstack(
            (self.phase_space['z_array'],
             self.phase_space['delta_array'])
            )
        self.phase_space['both_array'] = np.swapaxes(
            self.phase_space['both_array'], 0, 1)

    def enter_cavity(self, omega0_rf):
        """Change the omega0 and save the phase at the entrance."""
        self.phi['before_cavity'] = self.phi['abs']
        self.omega0['ref'] = omega0_rf
        self.omega0['rf'] = omega0_rf
        self.save_E = self.energy['e_mev']

    def exit_cavity(self):
        """Recompute phi with the proper omega0, reset omega0."""
        # Helpers
        delta_phi = self.phi['abs'] - self.phi['before_cavity']
        frac_omega = self.omega0['bunch'] / self.omega0['rf']
        # Reset proper phi
        correct_phi = self.phi['before_cavity'] + frac_omega * delta_phi
        self.phi['abs'] = correct_phi
        self.phi['abs_deg'] = np.rad2deg(correct_phi)
        # Reset proper omega
        self.omega0['ref'] = self.omega0['bunch']
        # Remove unsused variables
        print('delta_phi: ', delta_phi, '\t delta_E: ', self.energy['e_mev'] - self.save_E)
        self.phi['before_cavity'] = None
        self.omega0['rf'] = None

    def list_to_array(self):
        """Convert lists into arrays."""
        self.z['abs_array'] = np.array(self.z['abs_array'])
        self.energy['e_array_mev'] = np.array(self.energy['e_array_mev'])
        self.energy['gamma_array'] = np.array(self.energy['gamma_array'])
        self.energy['p_array'] = np.array(self.energy['p_array'])
        self.energy['gamma_array'] = np.array(self.energy['gamma_array'])
