#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 24 12:51:15 2022.

@author: placais

Module holding all the individual Fault functions.
If several close cavities fail, they are regrouped in the same Fault object and
are fixed together.

brok_lin: holds for "broken_linac", the linac with faults.
ref_lin: holds for "reference_linac", the ideal linac brok_lin should tend to.
"""
import numpy as np
from scipy.optimize import minimize, least_squares
from constants import FLAG_PHI_ABS, STR_PHI_ABS


dict_phase = {
    True: lambda elt: elt.acc_field.phi_0['abs'],
    False: lambda elt: elt.acc_field.phi_0['rel']
    }

n_comp_latt_per_fault = 2
debugs = {
    'fit': True,
    'cav': False,
    }


class Fault():
    """A class to hold one or several close Faults."""

    def __init__(self, ref_lin, brok_lin, fail_idx):
        self.ref_lin = ref_lin
        self.brok_lin = brok_lin
        self.fail = {'l_cav': [], 'l_idx': fail_idx}
        self.comp = {'l_cav': [], 'l_all_elts': None}
        self.info = {'sol': None, 'initial_guesses': None, 'bounds': None}

    def select_compensating_cavities(self):
        """Determine the cavitites to compensate the failed cav(s)."""
        comp_lattices_idx = []
        l_lattices = [lattice
                      for section in self.brok_lin.elements['sections']
                      for lattice in section
                      ]
        # Get lattices neighboring each faulty cavity
        # FIXME: too many lattices for faults in Section 3
        for idx in self.fail['l_idx']:
            failed_cav = self.brok_lin.elements['list'][idx]
            idx_lattice = failed_cav.info['lattice_number'] - 1
            for shift in [-1, +1]:
                idx = idx_lattice + shift
                while ((idx in comp_lattices_idx)
                       and (idx in range(0, len(l_lattices)))):
                    idx += shift
                # FIXME: dirty hack
                if abs(idx - idx_lattice) < 3:
                    comp_lattices_idx.append(idx)
                # Also add the lattice with the fault. Will be used if there
                # is a least one working cavity inside
                if idx_lattice not in comp_lattices_idx:
                    comp_lattices_idx.append(idx_lattice)
        comp_lattices_idx.sort()

        # List of all elements of the compensating zone
        self.comp['l_all_elts'] = [elt
                                   for latt_idx in comp_lattices_idx
                                   for elt in l_lattices[latt_idx]
                                   ]
        # List of compensating (+ broken) cavitites
        l_comp_cav = [cav
                      for cav in self.comp['l_all_elts']
                      if cav.info['nature'] == 'FIELD_MAP'
                      ]
        # TODO: handle manual_lists
        return l_comp_cav

    def update_status_cavities(self, l_comp_cav):
        """Give status 'compensate' and 'broken' to proper cavities."""
        for idx in self.fail['l_idx']:
            cav = self.brok_lin.elements['list'][idx]
            cav.update_status('failed')
            l_comp_cav.remove(cav)
            self.fail['l_cav'].append(cav)

        for cav in l_comp_cav:
            if cav.info['status'] != 'nominal':
                print('warning check fault.update_status_cavities: ',
                      'several faults want the same compensating cavity!')
            cav.update_status('compensate')
            self.comp['l_cav'].append(cav)

    def _select_cavities_to_rephase(self):
        """
        Change the status of some cavities to 'rephased'.

        If the calculation is in relative phase, all cavities that are after
        the the first failed one are rephased.
        Even in the case of an absolute phase calculation, cavities in the
        HEBT are rephased.
        """
        # We get first failed cav
        ffc = min([
            self.brok_lin.where_is(fail_cav)
            for fail_cav in self.fail_list
            ])
        after_ffc = self.brok_lin.elements['list'][ffc:]

        cav_to_rephase = [cav
                          for cav in after_ffc
                          if (cav.info['nature'] == 'FIELD_MAP'
                              and cav.info['status'] == 'nominal')
                          and (cav.info['zone'] == 'HEBT'
                               or not FLAG_PHI_ABS)
                          ]
        for cav in cav_to_rephase:
            cav.update_status('rephased')

    def _select_comp_modules(self, modules_with_fail):
        """Give failed modules and their neighbors."""
        modules = self.brok_lin.elements['list_lattice']
        neighbor_modules = []
        for module in modules_with_fail:
            idx = modules.index(module)
            if idx > 0:
                neighbor_modules.append(modules[idx-1])
            if idx < len(modules) - 1:
                neighbor_modules.append(modules[idx+1])
        # We return all modules that could help to compensation, ie neighbors
        # as well as faulty modules
        return neighbor_modules + modules_with_fail

    def fix_single(self, method, what_to_fit, manual_list=None):
        """
        Try to compensate the faulty cavities.

        Parameters
        ----------
        method : str
            Tells which algorithm should be used to compute transfer matrices.
        what_to_fit : dict
            Holds the strategies of optimisation.
        manual_list : list, optional
            List of the indices of the cavities that compensate the fault when
            'strategy' == 'manual'. The default is None.
        """
        self.what_to_fit = what_to_fit
        print("Starting fit with parameters:", self.what_to_fit)

        # Set the fit variables
        initial_guesses, bounds = self._set_fit_parameters()
        self.info['initial_guesses'], self.info['bounds'] = \
            initial_guesses, bounds
        fun_objective, idx_objective = self._select_objective(
            self.what_to_fit['position'],
            self.what_to_fit['objective'])

        dict_fitter = {
            'energy': [minimize, initial_guesses, bounds],
            'phase': [minimize, initial_guesses, bounds],
            'energy_phase': [least_squares, initial_guesses,
                             (bounds[:, 0], bounds[:, 1])],
            'transfer_matrix': [least_squares, initial_guesses,
                                (bounds[:, 0], bounds[:, 1])],
            'all': [least_squares, initial_guesses,
                    (bounds[:, 0], bounds[:, 1])],
            }  # minimize and least_squares do not take the same bounds format
        fitter = dict_fitter[self.what_to_fit['objective']]
        sol = fitter[0](wrapper, x0=fitter[1], bounds=fitter[2],
                        args=(self, method, fun_objective, idx_objective),
                        x_scale='jac')
        # TODO check methods
        # TODO check Jacobian
        # TODO check x_scale

        for i, cav in enumerate(self.comp['l_cav']):
            cav.acc_field.phi_0[STR_PHI_ABS] = sol.x[i]
            cav.acc_field.norm = sol.x[i + len(self.comp['l_cav'])]

        print('\n', sol)
        self.info['sol'] = sol

        return sol.success

    def _set_fit_parameters(self):
        """
        Set initial conditions and boundaries for the fit.

        In the returned arrays, first half of components are initial phases
        phi_0, while second half of components are norms.

        Returns
        -------
        initial_guess: np.array
            Initial guess for the initial phase and norm of the compensating
            cavities.
        bounds: np.array of bounds
            Array of (min, max) bounds for the electric fields of the
            compensating cavities.
        """
        initial_guess = []
        bounds = []

        # Handle phase
        limits_phase = (0., 2.*np.pi)
        for elt in self.comp['l_cav']:
            initial_guess.append(dict_phase[FLAG_PHI_ABS](elt))
            bounds.append(limits_phase)

        # Handle norm
        limits_norm = {
            'relative': [0.5, 1.3],    # [90%, 130%] of norm
            'absolute': [1., np.inf]   # ridiculous abs limits
            }   # TODO: personnalize limits according to zone, technology
        limits_norm_up = {
            'low beta': 1.3 * 3.03726,
            'medium beta': 1.3 * 4.45899,
            'high beta': 1.3 * 6.67386,
            }
        for elt in self.comp['l_cav']:
            norm = elt.acc_field.norm
            # initial_guess.append(norm)
            down = max(limits_norm['relative'][0] * norm,
                       limits_norm['absolute'][0])
            # upp = min(limits_norm['relative'][1] * norm,
                      # limits_norm['absolute'][1])
            upp = limits_norm_up[elt.info['zone']]

            initial_guess.append(norm)
            bounds.append((down, upp))

        initial_guess = np.array(initial_guess)
        bounds = np.array(bounds)
        return initial_guess, bounds

    def _select_objective(self, position_str, objective_str):
        """Select the objective to fit."""
        # Where do you want to verify that the objective is matched?
        all_list = self.brok_lin.elements['list']
        # FIXME
        n_latt = 10 #self.brok_lin.elements['n_per_lattice']
        dict_position = {
            'end_of_last_comp_cav': lambda c_list:
                [c_list[-1].idx['out'] - 1],
            'one_module_after_last_comp_cav': lambda c_list:
                [all_list[all_list.index(c_list[-1]) + n_latt].idx['out'] - 1],
            }
        dict_position['both'] = lambda c_list: \
            dict_position['end_of_last_comp_cav'](c_list) \
            + dict_position['one_module_after_last_comp_cav'](c_list)

        # What do you want to match?
        dict_objective = {
            'energy': lambda linac, idx:
                [linac.synch.energy['kin_array_mev'][idx]],
            'phase': lambda linac, idx:
                [linac.synch.phi['abs_array'][idx]],
            'transfer_matrix': lambda linac, idx:
                list(linac.transf_mat['cumul'][idx, :, :].flatten()),
                }
        dict_objective['energy_phase'] = lambda linac, idx: \
            dict_objective['energy'](linac, idx) \
            + dict_objective['phase'](linac, idx)
        dict_objective['all'] = lambda linac, idx: \
            dict_objective['energy_phase'](linac, idx) \
            + dict_objective['transfer_matrix'](linac, idx)

        idx_pos_list = dict_position[position_str](self.comp['l_cav'])
        fun_simple = dict_objective[objective_str]

        def fun_multi_objective(linac, idx_list):
            obj = fun_simple(linac, idx_list[0])
            for idx in idx_list[1:]:
                obj = obj + fun_simple(linac, idx)
            return np.array(obj)

        for idx in idx_pos_list:
            elt = self.brok_lin.where_is_this_index(idx)
            print('\nWe try to match at synch index:', idx, 'which is',
                  elt.info, ".\n")
        return fun_multi_objective, idx_pos_list


def wrapper(prop_array, fault, method, fun_objective, idx_objective):
    """Fit function."""
    # Unpack
    for i, cav in enumerate(fault.comp['l_cav']):
        acc_f = cav.acc_field
        acc_f.phi_0[STR_PHI_ABS] = prop_array[i]
        acc_f.norm = prop_array[i+len(fault.comp['l_cav'])]

    # Update transfer matrices
    fault.brok_lin.compute_transfer_matrices(method, fault.comp['l_all_elts'])

    obj = np.abs(fun_objective(fault.ref_lin, idx_objective)
                 - fun_objective(fault.brok_lin, idx_objective))
    # TODO: could be cleaner?
    if False:
        for cav in fault.comp['l_cav']:
            if cav.acc_field.cav_params['phi_s_deg'] > 0.:
                obj *= 1e8
    # print(obj)
    return obj
