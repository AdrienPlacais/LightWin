#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 13:52:26 2023.

@author: placais

Routines to evaluate the quality of the new settings for the linac.
"""
import numpy as np
import matplotlib.pyplot as plt

from palettable.colorbrewer.qualitative import Dark2_8
from cycler import cycler

from util import helper
from core.emittance import mismatch_factor
import visualization.plot

font = {'family': 'serif',
        'size': 20}
plt.rc('font', **font)
plt.rc('axes', prop_cycle=(cycler('color', Dark2_8.mpl_colors)))
plt.rc('mathtext', fontset='cm')


def fred_tests(lin_ref, lin_fix, multipart=True, plot=True):
    """
    Check if the new settings are ok.

    The tests are:
        - lost power shall be null;
        - the RMS emittances shall not grow of more than 20% along the linac;
        - the maximum of 99% emittances (fixed) shall not exceed the nominal
          maximum of 99% emittances by more than 30%.

    This routine simply returns a dict containing a boolean telling if these
    tests´ were successfully passed or not.
    """
    source = "multipart"
    if not multipart:
        source = "envelope"
    d_ref = lin_ref.tw_results[source]
    d_fix = lin_fix.tw_results[source]

    l_d_lim = []

    d_tests = {'Powlost': True, 'ex': True, 'ey': True, 'ep': True,
               'ex99': True, 'ey99': True, 'ep99': True}

    # Power loss test
    pow_lost = d_fix['Powlost']
    if pow_lost[-1] > 1e-10:
        d_tests['Powlost'] = False
    l_d_lim.append({'Powlost': {'max': None, 'min': None}})

    # RMS emittances test
    eps_rms = np.column_stack((d_fix['ex'], d_fix['ey'], d_fix['ep']))
    var_rms = 100. * (eps_rms - eps_rms[0, :]) / eps_rms[0, :]
    tmp_lim = {}
    for i, key in enumerate(['ex', 'ey', 'ep']):
        tmp_lim[key] = {'max': 1.2 * d_ref[key], 'min': None}
        if np.any(var_rms[:, i] > 20.):
            d_tests[key] = False
    l_d_lim.append(tmp_lim)

    # 99% emittances test
    eps99_ref = np.max(
        np.column_stack((d_ref['ex99'], d_ref['ey99'], d_ref['ep99'])), axis=0)
    eps99_fix = np.max(
        np.column_stack((d_fix['ex99'], d_fix['ey99'], d_fix['ep99'])), axis=0)

    tmp_lim = {}
    for i, key in enumerate(['ex99', 'ey99', 'ep99']):
        tmp_lim[key] = {'max': 1.3 * np.max(d_ref[key]), 'min': None}
        if eps99_fix[i] > 1.3 * eps99_ref[i]:
            d_tests[key] = False
    l_d_lim.append(tmp_lim)

    if plot:
        l_d_ref, l_d_fix = [], []
        for l_keys in [['Powlost'],
                       ['ex', 'ey', 'ep'],
                       ['ex99', 'ey99', 'ep99']]:
            tmp_ref, tmp_fix = {}, {}
            for key in l_keys:
                tmp_ref[key] = d_ref[key]
                tmp_fix[key] = d_fix[key]
            l_d_ref.append(tmp_ref)
            l_d_fix.append(tmp_fix)

        z_m = d_fix['z(m)']
        visualization.plot.plot_evaluate(z_m, l_d_ref, l_d_fix, l_d_lim,
                                         lin_fix, 'fred', save_fig=True,
                                         num=60)

    return d_tests


def bruce_tests(lin_ref, lin_fix, multipart=True, plot=True):
    """Test the fixed linac using Bruce's paper."""
    source = "multipart"
    if not multipart:
        source = "envelope"

    d_ref = lin_ref.tw_results[source]
    d_fix = lin_fix.tw_results[source]
    l_d_fix = []

    d_tests = {'relative_var_et': None,
               'relative_var_ep': None,
               'mismatch_t': None,
               'mismatch_zdp': None,
               'max_retuned_power': None}

    base = 'relative_var_'
    tmp = {}
    for key in ['et', 'ep']:
        delta = 100. * (d_fix[key] - d_ref[key]) / d_ref[key]
        d_fix[base + key] = delta
        d_tests[base + key] = delta[-1]
        tmp[base + key] = delta
    l_d_fix.append(tmp)

    # Mismatch test
    mismatch = {'x': None, 'y': None, 'zdp': None}
    for key in mismatch.keys():
        twiss_ref = d_ref['twiss_' + key]
        twiss_fix = d_fix['twiss_' + key]
        mismatch[key] = mismatch_factor(twiss_ref, twiss_fix, transp=True)


    d_fix['mismatch_t'] = .5 * (mismatch['x'] + mismatch['y'])
    d_fix['mismatch_zdp'] = mismatch['zdp']
    tmp = {}
    for key in ['mismatch_t', 'mismatch_zdp']:
        d_tests[key] = d_fix[key][-1]
        tmp[key] = d_fix[key]
    l_d_fix.append(tmp)

    if plot:
        z_m = d_fix['z(m)']

        l_d_ref = []
        l_d_lim = []
        for dic in l_d_fix:
            tmp1, tmp2 = {}, {}
            for key, val in dic.items():
                tmp1[key] = val * np.NaN
                tmp2[key] = {'max': None, 'min': None}
            l_d_ref.append(tmp1)
            l_d_lim.append(tmp2)
        visualization.plot.plot_evaluate(z_m, l_d_ref, l_d_fix, l_d_lim,
                                         lin_fix, 'bruce', save_fig=True,
                                         num=70)

    return d_tests