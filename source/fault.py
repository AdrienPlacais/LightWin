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

TODO : try to fit gamma instead of W_kin
TODO : at init of Fault, say self.brok_lin = brok_lin.deepcopy() (or copy)
       Return self.brok_lin at the end of fix_all()
       It could also be called fix_linac...
       AH no in fact, maybe plutôt self.fixed_linac = brok_lin after it is
       broken, end of __init__. And then fix only fixed?
       Or can the breakage be done at the init of the Accelerator?
"""
import numpy as np
from scipy.optimize import minimize, least_squares
import PSO as pso
from constants import FLAG_PHI_ABS, FLAG_PHI_S_FIT, OPTI_METHOD, WHAT_TO_FIT
import debug


dict_phase = {
    True: lambda elt: elt.acc_field.phi_0['abs'],
    False: lambda elt: elt.acc_field.phi_0['rel']
}

N_COMP_LATT_PER_FAULT = 2
debugs = {
    'fit_complete': False,
    'fit_compact': False,
    'fit_progression': False,
    'cav': True,
    'verbose': 1,
}


class Fault():
    """A class to hold one or several close Faults."""

    def __init__(self, ref_lin, brok_lin, fail_idx):
        self.ref_lin = ref_lin
        self.brok_lin = brok_lin
        self.fail = {'l_cav': [], 'l_idx': fail_idx}
        self.comp = {'l_cav': [], 'l_all_elts': [], 'l_recompute': None,
                     'n_cav': None}
        self.info = {'sol': None, 'initial_guesses': None, 'bounds': None,
                     'jac': None, 'l_obj_label': [], 'l_prop_label': [],
                     'resume': None}
        self.count = None

        # We directly break the proper cavities
        self._set_broken_cavities()

    def fix_single(self):
        """Try to compensate the faulty cavities."""
        # Set the fit variables
        initial_guesses, bounds, phi_s_limits, l_prop_label \
            = self._set_fit_parameters()
        l_elts, d_idx = self._select_zone_to_recompute(WHAT_TO_FIT['position'])

        fun_residual, l_obj_label = _select_objective(WHAT_TO_FIT['objective'])
        # l_obj_label = _set_labels(WHAT_TO_FIT['objective'])

        # Save some data for debug and output purposes
        self.info['initial_guesses'] = initial_guesses
        self.info['bounds'] = bounds
        self.info['l_prop_label'] = l_prop_label
        self.info['l_obj_label'] = l_obj_label
        self.comp['l_recompute'] = l_elts

        wrapper_args = (self, fun_residual, d_idx)

        self.count = 0
        if OPTI_METHOD == 'least_squares':
            flag_success, opti_sol = self._proper_fix_lsq_opt(
                initial_guesses, bounds, wrapper_args)

        elif OPTI_METHOD == 'PSO':
            flag_success, opti_sol = self._proper_fix_pso(
                initial_guesses, bounds, wrapper_args, phi_s_limits)

        return flag_success, opti_sol

    def _proper_fix_lsq_opt(self, init_guess, bounds, wrapper_args):
        """
        Fix with classic least_squares optimisation.

        The least_squares algorithm does not allow to add constraint functions.
        In particular, if you want to control the synchronous phase, you should
        directly optimise phi_s (FLAG_PHI_S_FIT == True) or use PSO algorithm
        (OPTI_METHOD == 'PSO').
        """
        if init_guess.shape[0] == 1:
            kwargs = minimize
            # TODO: recheck
            solver = {}
        else:
            solver = least_squares
            bounds = (bounds[:, 0], bounds[:, 1])
            kwargs = {'jac': '2-point',     # Default
                      # 'trf' not ideal as jac is not sparse. 'dogbox' may have
                      # difficulties with rank-defficient jacobian.
                      'method': 'dogbox',
                      'ftol': 1e-8, 'gtol': 1e-8,   # Default
                      # Solver is sometimes 'lazy' and ends with xtol
                      # termination condition, while settings are clearly not
                      #  optimized
                      'xtol': 1e-8,
                      # TODO: check these args
                      'x_scale': 'jac', 'loss': 'linear', 'f_scale': 1.0,
                      'diff_step': None, 'tr_solver': None, 'tr_options': {},
                      'jac_sparsity': None,
                      'verbose': debugs['verbose']
                      }
        sol = solver(fun=wrapper, x0=init_guess, bounds=bounds,
                     args=wrapper_args, **kwargs)

        if debugs['fit_progression']:
            debug.output_fit_progress(self.count, sol.fun, final=True)

        print(f"""\nmessage: {sol.message}\nnfev: {sol.nfev}\tnjev: {sol.njev}
              \noptimality: {sol.optimality}\nstatus: {sol.status}\t
              success: {sol.success}\nx: {sol.x}\n\n""")
        self.info['sol'] = sol
        self.info['jac'] = sol.jac

        return sol.success, sol.x

    def _proper_fix_pso(self, init_guess, bounds, wrapper_args,
                        phi_s_limits=None):
        """Fix with multi-PSO algorithm."""
        n_obj = 6  # FIXME
        if FLAG_PHI_S_FIT:
            n_constr = 0
        else:
            assert phi_s_limits is not None
            n_constr = 2 * phi_s_limits.shape[0]

        problem = pso.MyProblem(wrapper_pso, init_guess.shape[0], n_obj,
                                n_constr,
                                bounds, wrapper_args, phi_s_limits)
        res = pso.perform_pso(problem)

        weights = pso.set_weights(WHAT_TO_FIT['objective'])
        opti_sol, approx_ideal, approx_nadir = pso.mcdm(res, weights,
                                                        self.info)

        if pso.flag_convergence_history:
            pso.convergence_history(res.history, approx_ideal, approx_nadir)
        if pso.flag_convergence_callback:
            pso.convergence_callback(res.algorithm.callback,
                                     self.info['l_obj_label'])

        return True, opti_sol

    def select_neighboring_cavities(self):
        """
        Select the cavities neighboring the failed one(s).

        More precisely:
        Select the lattices with comp cav, extract cavities from it.

        As for now, N_COMP_LATT_PER_FAULT is the number of compensating
        lattices per faulty cavity. This number is however too high for
        MYRRHA's high beta section.

        # TODO: get this function out of the Class?
        Would be better for consistency w/ manual list
        Required arguments:
            l_lattices from brok_lin.elements['l_sections'] list of lattices
            list of elements of brok_lin
            index in lattice reference
            self.fail['l_idx'] indexes of failed cavities

        Return
        ------
        l_comp_cav : list
            List of the cavities (_Element object) used for compensation.
        """
        comp_lattices_idx = []
        l_lattices = [lattice
                      for section in self.brok_lin.elements['l_sections']
                      for lattice in section
                      ]
        # Get lattices neighboring each faulty cavity
        # FIXME: too many lattices for faults in Section 3
        for idx in self.fail['l_idx']:
            failed_cav = self.brok_lin.elements['list'][idx]
            idx_lattice = failed_cav.idx['lattice'][0]
            for shift in [-1, +1]:
                idx = idx_lattice + shift
                while ((idx in comp_lattices_idx)
                       and (idx in range(0, len(l_lattices)))):
                    idx += shift
                # FIXME: dirty hack
                if abs(idx - idx_lattice) < 3:
                    comp_lattices_idx.append(idx)

                # Also add the lattice with the fault
                if idx_lattice not in comp_lattices_idx:
                    comp_lattices_idx.append(idx_lattice)

        comp_lattices_idx.sort()

        # List of compensating (+ broken) cavitites
        l_comp_cav = [cav
                      for idx in comp_lattices_idx
                      for cav in l_lattices[idx]
                      if cav.info['nature'] == 'FIELD_MAP'
                      ]
        return l_comp_cav

    def _set_broken_cavities(self):
        """Break the cavities to break."""
        # Break proper cavities
        for idx in self.fail['l_idx']:
            cav = self.brok_lin.elements['list'][idx]
            cav.update_status('failed')
            self.fail['l_cav'].append(cav)

    def prepare_cavities_for_compensation(self, strategy, l_comp_idx=None):
        """
        Prepare the compensating cavities for the upcoming optimisation.

        In particular, update the status of the compensating cavities to
        'compensate (in progress)', create list of compensating cavities,
        create list of all elements in the compensating zone.
        """
        new_status = "compensate (in progress)"

        # Create a list of cavities that will compensate
        if strategy == 'neighbors':
            l_comp_cav = self.select_neighboring_cavities()
        elif strategy == 'manual':
            assert len(l_comp_idx) > 0, "A list of compensating cavities" \
                    + "is required with WHAT_TO_FIT['strategy'] == 'manual'."
            l_comp_cav = [self.brok_lin.elements['list'][idx]
                          for idx in l_comp_idx]

        # Remove broke cavities, check if some compensating cavities already
        # compensate another fault, update status of comp cav
        for cav in l_comp_cav:
            current_status = cav.info['status']
            assert current_status != new_status, """Current cavity already has
            the status that you asked for. Maybe two faults want the same
            cavity for their compensation?"""

            # If the cavity is broken, we do not want to change it's status
            if current_status == 'failed':
                continue

            if current_status in ["compensate (ok)", "compensate (not ok)"]:
                print("""Warning! You want to update the status of a cavity
                      that is already used for compensation. Check
                      fault.set_compensating_cavities. Maybe two faults
                      want to use the same cavity for compensation?""")

            cav.update_status(new_status)
            self.comp['l_cav'].append(cav)

        self.comp['n_cav'] = len(self.comp['l_cav'])

        # Also create a list of all the elements in the compensating
        # lattices
        l_lattices = [lattice
                      for section in self.brok_lin.elements['l_sections']
                      for lattice in section
                      ]

        self.comp['l_all_elts'] = [elt
                                   for lattice in l_lattices
                                   for elt in lattice
                                   if any((cav in lattice
                                           for cav in self.comp['l_cav']))
                                   ]

    def update_status_and_cav_parameters(self, flag_success, l_rf_fields):
        """
        Update status of the compensating cavities, save new rf field param.
        """
        if flag_success:
            new_status = "compensate (ok)"
        else:
            new_status = "compensate (not ok)"

        # Remove broke cavities, check if some compensating cavities already
        # compensate another fault, update status of comp cav
        for (cav, rf_field) in zip(self.comp['l_cav'], l_rf_fields):
            # phi_0 = d_fits['l_phi'].pop(0)
            # rf_field = {'k_e': d_fits['l_k_e'].pop(0),
                        # 'phi_0_rel': phi_0,
                        # 'phi_0_abs': phi_0,
                       # }
            # FIXME I think that I can safely ignore the difference between
            # phi_0_rel and _abs, the good one will be used and the other one
            # erased.
            # I """think"""...
            cav.update_status(new_status)
            cav.acc_field.save_parameters_found_by_optimisation(**rf_field)

    def _set_fit_parameters(self):
        """
        Set initial conditions and boundaries for the fit.

        In the returned arrays, first half of components are initial phases
        phi_0, while second half of components are norms.

        Returns
        -------
        initial_guess : np.array
            Initial guess for the initial phase and norm of the compensating
            cavities.
        bounds : np.array of tuples
            Array of (min, max) bounds for the electric fields of the
            compensating cavities.
        phi_s_limits : np.array of tuples
            Contains upper and lower synchronous phase limits for each cavity.
            Used to define constraints in PSO.
        """
        # Useful dicts
        d_getter = {'k_e': lambda cav: cav.acc_field.k_e,
                    'phi_0_rel': lambda cav: cav.acc_field.phi_0['rel'],
                    'phi_0_abs': lambda cav: cav.acc_field.phi_0['abs'],
                    'phi_s': lambda cav: cav.acc_field.cav_params['phi_s_rad']}
        d_init_g = {'k_e': lambda ref_value: ref_value,
                    'phi_0_rel': lambda ref_value: 0.,
                    'phi_0_abs': lambda ref_value: 0.,
                    'phi_s': lambda ref_value: ref_value}
        d_tech_n = {'low beta': 1.3 * 3.03726,
                    'medium beta': 1.3 * 4.45899,
                    'high beta': 1.3 * 6.67386}
        d_bounds_abs = {'k_e': [1., np.NaN],
                        'phi_0_rel': [0., 4. * np.pi],
                        'phi_0_abs': [0., 4. * np.pi],
                        'phi_s': [-.5 * np.pi, 0.]}
        d_bounds_rel = {'k_e': [.5, np.NaN],
                        'phi_0_rel': [np.NaN, np.NaN],
                        'phi_0_abs': [np.NaN, np.NaN],
                        'phi_s': [np.NaN, 1. - .4]}   # phi_s+40%, w/ phi_s<0
        d_prop_label = {'k_e': r'$k_e$', 'phi_0_abs': r'$\phi_{0, abs}$',
                        'phi_0_rel': r'$\phi_{0, rel}$',
                        'phi_s': r'$\varphi_s$'}

        # Set a list of properties that will be fitted
        if FLAG_PHI_S_FIT:
            l_prop = ['phi_s']
        else:
            if FLAG_PHI_ABS:
                l_prop = ['phi_0_abs']
            else:
                l_prop = ['phi_0_rel']
        l_prop += ['k_e', 'phi_s']
        l_prop_label = []

        # Get initial guess and bounds for every property of l_prop and every
        # compensating cavity
        initial_guess, bounds = [], []
        for prop in l_prop:
            for cav in self.comp['l_cav']:
                equiv_cav = self.ref_lin.elements['list'][cav.idx['element']]
                ref_value = d_getter[prop](equiv_cav)
                b_down = np.nanmax((d_bounds_abs[prop][0],
                                    d_bounds_rel[prop][0] * ref_value))
                if prop == 'k_e':
                    b_up = d_tech_n[cav.info['zone']]
                else:
                    b_up = np.nanmin((d_bounds_abs[prop][1],
                                      d_bounds_rel[prop][1] * ref_value))
                bounds.append((b_down, b_up))
                initial_guess.append(d_init_g[prop](ref_value))
                l_prop_label.append(' '.join((cav.info['name'],
                                              d_prop_label[prop])))

        n_cav = len(self.comp['l_cav'])
        initial_guess = np.array(initial_guess[:2 * n_cav])
        phi_s_limits = np.array(bounds[2 * n_cav:])
        bounds = np.array(bounds[:2 * n_cav])

        print('initial_guess:\n', initial_guess, '\nbounds:\n', bounds)
        if OPTI_METHOD == 'PSO' and not FLAG_PHI_ABS:
            print('Additional constraint: phi_s_limits:\n', phi_s_limits)

        return initial_guess, bounds, phi_s_limits, l_prop_label

    def _select_zone_to_recompute(self, str_position):
        """
        Determine zone to recompute and indexes of where objective is checked.

        Parameters
        ----------
        str_position : string
            Indicates where the objective should be matched.

        Return
        ------
        l_elts : list of _Element
            List of elements that should be recomputed.
        d_idx : dict
            Dict holding the lists of indexes (ref and broken) to evaluate the
            objectives at the right spot.
        """
        d_idx = {'l_ref': [], 'l_brok': []}

        # Which lattices' data are necessary?
        d_lattices = {
            'end_mod': lambda l_cav: self.brok_lin.elements['l_lattices']
            [l_cav[0].idx['lattice'][0]:l_cav[-1].idx['lattice'][0] + 1],
            '1_mod_after': lambda l_cav: self.brok_lin.elements['l_lattices']
            [l_cav[0].idx['lattice'][0]:l_cav[-1].idx['lattice'][0] + 2],
            'both': lambda l_cav: self.brok_lin.elements['l_lattices']
            [l_cav[0].idx['lattice'][0]:l_cav[-1].idx['lattice'][0] + 2],
        }
        l_lattices = d_lattices[str_position](self.comp['l_cav'])
        l_elts = [elt
                  for lattice in l_lattices
                  for elt in lattice]
        # Where do you want to verify that the objective is matched?
        d_pos = {
            'end_mod': lambda lattices: [lattices[-1][-1].idx['s_out']],
            '1_mod_after': lambda lattices: [lattices[-1][-1].idx['s_out']],
            'both': lambda lattices: [lattices[-2][-1].idx['s_out'],
                                      lattices[-1][-1].idx['s_out']],
        }
        d_idx['l_ref'] = d_pos[str_position](l_lattices)
        shift_s_idx_brok = self.comp['l_all_elts'][0].idx['s_in']
        d_idx['l_brok'] = [idx - shift_s_idx_brok
                           for idx in d_idx['l_ref']]

        for idx in d_idx['l_ref']:
            elt = self.brok_lin.where_is_this_index(idx)
            print('\nWe try to match at synch index:', idx, 'which is',
                  elt.info, elt.idx, ".")

        return l_elts, d_idx


def _select_objective(l_str_objectives):
    """
    Select the objective to fit.

    Parameters
    ----------
    l_str_objectives : list of strings
        Indicates what should be fitted.

    Return
    ------
    fun_multi_objective : function
        Return the residuals for each objective at the proper position.
    """
    # Get data from reference linac
    d_obj_ref = {
        'energy': lambda ref_lin, idx:
            [ref_lin.synch.energy['kin_array_mev'][idx]],
        'phase': lambda ref_lin, idx:
            [ref_lin.synch.phi['abs_array'][idx]],
        'transf_mat': lambda ref_lin, idx:
            list(ref_lin.transf_mat['cumul'][idx].flatten()),
        'eps': lambda ref_lin, idx:
            [ref_lin.beam_param["eps"]["zdelta"][idx]],
        'twiss': lambda ref_lin, idx:
            list(ref_lin.beam_param["twiss"]["zdelta"][idx, 1:].flatten()),
    }

    # Get data from results dictionary
    d_obj_brok = {
        'energy': lambda calc, idx: [calc['w_kin'][idx]],
        'phase': lambda calc, idx: [calc['phi_abs'][idx]],
        'transf_mat': lambda calc, idx:
            list(calc['r_zz_cumul'][idx].flatten()),
        'eps': lambda calc, idx: [calc["d_zdelta"]["eps"][idx]],
        'twiss': lambda calc, idx:
            list(calc["d_zdelta"]["twiss"][idx, 1:].flatten()),
    }

    def fun_residual(ref_lin, d_results, d_idx):
        """Compute difference between ref_linac and current optimis. param."""
        l_fun_ref = [d_obj_ref[str_obj] for str_obj in l_str_objectives]
        l_fun_brok = [d_obj_brok[str_obj] for str_obj in l_str_objectives]

        ref, brok = [], []
        for fun_r, fun_b in zip(l_fun_ref, l_fun_brok):
            for i_r, i_b in zip(d_idx['l_ref'], d_idx['l_brok']):
                ref += fun_r(ref_lin, i_r)
                brok += fun_b(d_results, i_b)
        obj = np.abs(np.array(ref) - np.array(brok)).flatten()
        return obj

    d_obj_str = {'energy': [r'$W_{kin}$'],
                 'phase': [r'$\phi$'],
                 'transf_mat': [r'$M_{11}$', r'$M_{12}$',
                                r'$M_{21}$', r'$M_{22}$'],
                 'eps': [r'$\epsilon_{z\delta}$'],
                 'twiss': [r'$\beta_{z\delta}$', r'$\gamma_{z\delta}$']
                }
    l_obj_label = [d_obj_str[str_obj] for str_obj in l_str_objectives]

    return fun_residual, l_obj_label


def wrapper(arr_cav_prop, fault, fun_residual, d_idx):
    """
    Unpack arguments and compute proper residues at proper spot.

    Parameters
    ----------
    arr_cav_prop : np.array
        Holds the norms (first half) and phases (second half) of cavities
    fault : Fault object
        The Fault under study.
    fun_residual : function
        Function returning the residues of the objective function at the proper
        location.
    d_idx : dict
        Dict holding the lists of indexes (ref and broken) to evaluate the
        objectives at the right spot.

    Return
    ------
    arr_objective : np.array
        Array of residues on the objectives.
    """
    # Convert phases and norms into a dict for compute_transfer_matrices
    d_fits = {'l_phi': arr_cav_prop[:fault.comp['n_cav']].tolist(),
              'l_k_e': arr_cav_prop[fault.comp['n_cav']:].tolist()}

    # Update transfer matrices
    d_results = fault.brok_lin.compute_transfer_matrices(
        fault.comp['l_recompute'], d_fits=d_fits, flag_transfer_data=False)
    arr_objective = fun_residual(fault.ref_lin, d_results, d_idx)

    if debugs['fit_progression'] and fault.count % 20 == 0:
        debug.output_fit_progress(fault.count, arr_objective)
    fault.count += 1

    return arr_objective


def wrapper_pso(arr_cav_prop, fault, fun_residual, d_idx):
    """Unpack arguments and compute proper residues at proper spot."""
    d_fits = {'l_phi': arr_cav_prop[:fault.comp['n_cav']].tolist(),
              'l_k_e': arr_cav_prop[fault.comp['n_cav']:].tolist()}

    # Update transfer matrices
    d_results = fault.brok_lin.compute_transfer_matrices(
        fault.comp['l_recompute'], d_fits=d_fits, flag_transfer_data=False)
    arr_objective = fun_residual(fault.ref_lin, d_results, d_idx)

    if debugs['fit_progression'] and fault.count % 20 == 0:
        debug.output_fit_progress(fault.count, arr_objective)
    fault.count += 1

    return arr_objective, d_results
