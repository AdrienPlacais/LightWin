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
import tracewin.interface
from beam_calculation.tracewin import TraceWinBeamCalculator
from beam_calculation.factory import init_calc_with
from util import helper, output, evaluate
from util.log_manager import set_up_logging
from visualization import plot


if __name__ == '__main__':
    FILEPATH = "../data/MYRRHA/MYRRHA_Transi-100MeV.dat"
    CONFIG_PATH = 'myrrha.ini'
    KEY_BEAM_CALCULATOR = 'beam_calculator.lightwin.envelope_longitudinal'
    KEY_BEAM = 'beam.myrrha'
    KEY_WTF = 'wtf.k_out_of_n'
    KEY_TW = 'post_tracewin.quick_debug'

    # =========================================================================
    # Fault compensation
    # =========================================================================
    FLAG_BREAK = True
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
        # "cav",
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
    # Startjkj
    # =========================================================================
    FILEPATH = os.path.abspath(FILEPATH)
    PROJECT_FOLDER = os.path.join(
        os.path.dirname(FILEPATH),
        datetime.datetime.now().strftime('%Y.%m.%d_%Hh%M_%Ss_%fms'))
    os.makedirs(PROJECT_FOLDER)

    set_up_logging(logfile_file=os.path.join(PROJECT_FOLDER, 'lightwin.log'))

    beam_calculator_parameters, beam, wtf, post_tw = conf_man.process_config(
        CONFIG_PATH, PROJECT_FOLDER, KEY_BEAM_CALCULATOR, KEY_BEAM, KEY_WTF,
        KEY_TW)

    ref_linac = acc.Accelerator(FILEPATH, PROJECT_FOLDER, "Working")
    beam_calculator = init_calc_with(beam_calculator_parameters)

    simulation_output = beam_calculator.run(ref_linac.elts)
    ref_linac.keep_this(simulation_output=simulation_output)

    data_tab_from_tw = tracewin.interface.output_data_in_tw_fashion(ref_linac)
    linacs = [ref_linac]

    lw_fit_evals = []

# =============================================================================
# Run all simulations of the Project
# =============================================================================
    l_failed = wtf.pop('failed')
    l_manual = None
    manual = None
    if 'manual list' in wtf:
        l_manual = wtf.pop('manual list')

    if FLAG_BREAK:
        for i, failed in enumerate(l_failed):
            start_time = time.monotonic()
            lin = acc.Accelerator(FILEPATH, PROJECT_FOLDER, "Broken")

            if l_manual is not None:
                manual = l_manual[i]
            fault_scenario = FaultScenario(ref_acc=ref_linac,
                                           fix_acc=lin,
                                           beam_calculator=beam_calculator,
                                           wtf=wtf,
                                           fault_idx=failed,
                                           comp_idx=manual)
            linacs.append(deepcopy(lin))

            if FLAG_FIX:
                fault_scenario.fix_all()

            linacs.append(lin)

            end_time = time.monotonic()
            delta_t = datetime.timedelta(seconds=end_time - start_time)
            logging.info(f"Elapsed time: {delta_t}")

            tracewin.interface.update_dat_with_fixed_cavities(
                lin.get('dat_filecontent', to_numpy=False), lin.elts,
                lin.get('field_map_folder'))
            data_tab_from_tw = \
                tracewin.interface.output_data_in_tw_fashion(lin)
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
            # TODO transfer ini path elsewhere
            tw_simu = TraceWinBeamCalculator(post_tw['executable'],
                                             ini_path,
                                             lin.get('out_tw'),
                                             lin.get('dat_filepath'),
                                             post_tw)
            tw_simu.run(store_all_outputs=True)
            lin.tracewin_simulation = tw_simu

            if 'Fixed' in lin.name:
                tracewin.interface.resample_tracewin_results(
                    ref=linacs[0].tracewin_simulation,
                    fix=lin.tracewin_simulation)

            if FLAG_EVALUATE and 'Fixed' in lin.name:
                d_fred = evaluate.fred_tests(linacs[0], lin)
                l_fred.append(d_fred)

                d_bruce = evaluate.bruce_tests(linacs[0], lin)
                l_bruce.append(d_bruce)

        if FLAG_FIX and FLAG_EVALUATE:
            for _list, name in zip([l_fred, l_bruce],
                                   ['fred_tests.csv', 'bruce_tests.csv']):
                out = pd.DataFrame(_list)
                filepath = os.path.join(PROJECT_FOLDER, name)
                out.to_csv(filepath)

# =============================================================================
# Plot
# =============================================================================
    kwargs = {'plot_tw': FLAG_TW, 'save_fig': False, 'clean_fig': True}
    for i in range(len(l_failed)):
        for str_plot in PLOTS:
            # Plot the reference linac, i-th broken linac and corresponding
            # fixed linac
            if not FLAG_BREAK:
                args = (linacs[0], )
            else:
                if not FLAG_FIX:
                    args = (linacs[0], linacs[i + 1])
                else:
                    args = (linacs[0], linacs[2 * i + 1], linacs[2 * i + 2])
            plot.plot_preset(str_plot, *args, **kwargs)
