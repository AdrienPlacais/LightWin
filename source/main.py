#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  6 14:33:39 2022.

@author: placais
"""

import os
import logging
from copy import deepcopy
import time
import datetime
import pandas as pd

import config_manager as conf_man
import core.accelerator as acc
from optimisation.fault_scenario import FaultScenario
from util import helper, output, evaluate
import util.tracewin_interface as tw
from util.log_manager import set_up_logging
from visualization import plot


if __name__ == '__main__':
    FILEPATH = "../data/JAEA/JAEA_ADS_026.dat"
    CONFIG_PATH = 'jaea.ini'
    KEY_SOLVER = 'solver.envelope_longitudinal'
    KEY_BEAM = 'beam.jaea'
    KEY_WTF = 'wtf.global'
    KEY_TW = 'tracewin.quick_debug'

    # =========================================================================
    # Fault compensation
    # =========================================================================
    FLAG_FIX = True
    SAVE_FIX = True
    FLAG_TW = False
    RECOMPUTE_REFERENCE = False
    FLAG_EVALUATE = False

    # =========================================================================
    # Outputs
    # =========================================================================
    PLOTS = [
        "energy",
        "phase",
        "cav",
        "emittance",
        # "twiss",  # TODO
        # "envelopes", # FIXME
        # "transfer matrices", # TODO
    ]

    SAVES = [
        "energy phase and mt",
        "Vcav and phis",
    ]

    DICT_SAVES = {
        "energy phase and mt": helper.save_energy_phase_tm,
        "Vcav and phis": helper.save_vcav_and_phis,
    }

    # =========================================================================
    # Start
    # =========================================================================
    FILEPATH = os.path.abspath(FILEPATH)
    PROJECT_FOLDER = os.path.join(
        os.path.dirname(FILEPATH),
        datetime.datetime.now().strftime('%Y.%m.%d_%Hh%M_%Ss_%fms'))
    os.makedirs(PROJECT_FOLDER)

    set_up_logging(logfile_file=os.path.join(PROJECT_FOLDER, 'lightwin.log'))

    d_solver, d_beam, d_wtf, d_tw = conf_man.process_config(
        CONFIG_PATH, PROJECT_FOLDER, KEY_SOLVER, KEY_BEAM, KEY_WTF, KEY_TW)

    # Reference linac
    ref_linac = acc.Accelerator(FILEPATH, PROJECT_FOLDER, "Working")
    results = ref_linac.elts.compute_transfer_matrices()
    ref_linac.store_results(results, ref_linac.elts)

    linacs = [ref_linac]

    lw_fit_evals = []

# =============================================================================
# Run all simulations of the Project
# =============================================================================
    l_failed = d_wtf.pop('failed')
    l_manual = None
    manual = None
    if 'manual list' in d_wtf:
        l_manual = d_wtf.pop('manual list')

    for i, failed in enumerate(l_failed):
        start_time = time.monotonic()
        lin = acc.Accelerator(FILEPATH, PROJECT_FOLDER, "Broken")

        if l_manual is not None:
            manual = l_manual[i]
        fault_scenario = FaultScenario(ref_acc=ref_linac,
                                       fix_acc=lin,
                                       wtf=d_wtf,
                                       fault_idx=failed,
                                       comp_idx=manual)
        linacs.append(deepcopy(lin))

        if FLAG_FIX:
            fault_scenario.fix_all()
            results = lin.elts.compute_transfer_matrices()  # useful?
            lin.store_results(results, lin.elts)  # useful?

        linacs.append(lin)

        # Output some info on the quality of the fit
        end_time = time.monotonic()
        delta_t = datetime.timedelta(seconds=end_time - start_time)
        logging.info(f"Elapsed time: {delta_t}")

        tw.update_dat_with_fixed_cavities(
            lin.get('dat_filecontent', to_numpy=False), lin.elts,
            lin.get('field_map_folder'))
        data_tab_from_tw = tw.output_data_in_tw_fashion(lin)
        lw_fit_eval = fault_scenario.evaluate_fit_quality(delta_t)

        if SAVE_FIX:
            lin.files['dat_filepath'] = os.path.join(
                lin.get('out_lw'), os.path.basename(FILEPATH))
            output.save_files(lin, data=data_tab_from_tw,
                              lw_fit_eval=lw_fit_eval)

        lw_fit_evals.append(lw_fit_eval)

# =============================================================================
# TraceWin
# =============================================================================
    l_fred = []
    l_bruce = []
    if FLAG_TW:
        for lin in linacs:
            # It would be a loss of time to do these simulation
            if 'Broken' in lin.name:
                continue

            if 'Working' in lin.name and not RECOMPUTE_REFERENCE:
                lin.files["out_tw"] = os.path.join(os.path.dirname(FILEPATH),
                                                   'ref')
                logging.info(
                    "we do not TW recompute reference linac. "
                    + f"We take TW results from {lin.files['out_tw']}.")
                continue

            ini_path = FILEPATH.replace('.dat', '.ini')
            lin.simulate_in_tracewin(ini_path, **d_tw)
            # TODO transfer ini path elsewhere
            lin.store_tracewin_results()

            if 'Fixed' in lin.name:
                lin.resample_tw_results(linacs[0])

            lin.precompute_some_tracewin_results()

            if FLAG_EVALUATE and 'Fixed' in lin.name:
                d_fred = evaluate.fred_tests(linacs[0], lin)
                l_fred.append(d_fred)

                d_bruce = evaluate.bruce_tests(linacs[0], lin)
                l_bruce.append(d_bruce)

        if FLAG_EVALUATE:
            for _list, name in zip([l_fred, l_bruce],
                                   ['fred_tests.csv', 'bruce_tests.csv']):
                out = pd.DataFrame(_list)
                filepath = os.path.join(PROJECT_FOLDER, name)
                out.to_csv(filepath)

# =============================================================================
# Plot
# =============================================================================
    kwargs = {'plot_tw': FLAG_TW, 'save_fig': SAVE_FIX, 'clean_fig': True}
    for i in range(len(l_failed)):
        for str_plot in PLOTS:
            # Plot the reference linac, i-th broken linac and corresponding
            # fixed linac
            args = (linacs[0], linacs[2 * i + 1], linacs[2 * i + 2])
            plot.plot_preset(str_plot, *args, **kwargs)
