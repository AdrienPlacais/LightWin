#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 29 12:01:01 2022.

@author: placais
"""
# NB: all phi are in radians. The reason why they all have unit [deg] is that
# they are always converted to degrees when outputed.
d_markdown = {
    # Accelerator
    'M_11': r"$M_{11}$",
    'M_12': r"$M_{12}$",
    'M_21': r"$M_{21}$",
    'M_22': r"$M_{22}$",
    'eps_zdelta': r"$\epsilon_{z\delta}$ [$\pi$.m.rad]",
    'eps_z': r"$\epsilon_{zz'}$ [mm/$\pi$.mrad]",
    'eps_w': r"$\epsilon_{\phi W}$ [deg/$\pi$.MeV]",
    'alpha_zdelta': r"$\alpha_{z\delta}$ [1]",
    'alpha_z': r"$\alpha_{zz'}$ [1]",
    'alpha_w': r"$\alpha_{\phi W}$ [1]",
    'beta_zdelta': r"$\beta_{z\delta}$ [mm/$\pi$.%]",
    'beta_z': r"$\beta_{zz'}$ [mm/$\pi$.mrad]",
    'beta_w': r"$\beta_{\phi W}$ [deg/$\pi$.MeV]",
    'gamma_zdelta': r"$\gamma_{z\delta}$ [$\pi$/mm.rad]",
    'gamma_z': r"$\gamma_{zz'}$ [$\pi$/mm.mrad]",
    'gamma_w': r"$\gamma_{\phi W}$ [$\pi$/deg.MeV]",
    'envelope_pos_zdelta': r"$\sigma_z$ [m]",
    'envelope_pos_z': r"$\sigma_z$ [mm]",
    'envelope_pos_w': r"$\sigma_\phi$ [deg]",
    'envelope_energy_zdelta': r"$\sigma_\delta$ [rad]",
    'envelope_energy_z': r"$\sigma_{z'}$ [mrad]",
    'envelope_energy_w': r"$\sigma_\phi$ [MeV]",
    'mismatch factor': r"$M$",
    # Element
    'elt_idx': "Element index",
    'elt number': "Element number",
    # RfField
    'v_cav_mv': "Acc. field [MV]",
    'phi_s': "Synch. phase [deg]",
    'k_e': r"$k_e$ [1]",
    'phi_0_abs': r"$\phi_{0, abs}$ [deg]",
    'phi_0_rel': r"$\phi_{0, rel}$ [deg]",
    # Particle
    'z_abs': "Synch. position [m]",
    'w_kin': "Beam energy [MeV]",
    'phi_abs_array': "Beam phase [deg]",
    'beta': r"Synch. $\beta$ [1]",
    # Misc
    'struct': "Structure",
    'err_simple': "Error",
    'err_abs': "Abs. error",
    'err_rel': "Rel. error",
    'err_log': "log of rel. error",
    # ListOfElements
    # TraceWin
    'Powlost': "Lost power [W]",
    'ex': r"Norm. RMS $\epsilon_{xx'}$ [$\pi$mm mrad]",
    'ey': r"Norm. RMS $\epsilon_{yy'}$ [$\pi$mm mrad]",
    'ezdp': r"Norm. RMS $\epsilon_{zz'}$ [$\pi$mm mrad]",   # NOT epsilon z dp/p !!
    'ep': r"Norm. RMS $\epsilon_{\phi W}$ [$\pi$deg MeV]",
    'ex99': r"Norm. 99% $\epsilon_{xx'}$ [$\pi$mm mrad]",
    'ey99': r"Norm. 99% $\epsilon_{yy'}$ [$\pi$mm mrad]",
    'ep99': r"Norm. 99% $\epsilon_{zz'}$ [$\pi$mm mrad]",  # NOT epsilon z dp/p
    # util.evaluate
    'relative_var_et': r'$\Delta\epsilon_t / \epsilon_{t, 0}$ [%]',
    'relative_var_ep': r'$\Delta\epsilon_{\phi W} / \epsilon_{\phi W, 0}$ [%]',
    'mismatch_t': r'$M_t$',
    'mismatch_zdp': r'$M_l$',
}

d_plot_kwargs = {
    # Accelerator
    'eps_zdelta': {'marker': None},
    'eps_z': {'marker': None},
    'eps_w': {'marker': None},
    'alpha_zdelta': {'marker': None},
    'alpha_z': {'marker': None},
    'alpha_w': {'marker': None},
    'beta_zdelta': {'marker': None},
    'beta_z': {'marker': None},
    'beta_w': {'marker': None},
    'gamma_zdelta': {'marker': None},
    'gamma_z': {'marker': None},
    'gamma_w': {'marker': None},
    'envelope_pos_zdelta': {'marker': None},
    'envelope_pos_z': {'marker': None},
    'envelope_pos_w': {'marker': None},
    'envelope_energy_zdelta': {'marker': None},
    'envelope_energy_z': {'marker': None},
    'envelope_energy_w': {'marker': None},
    'mismatch factor': {'marker': None},
    # Element
    'elt_idx': {'marker': None},
    # RfField
    'v_cav_mv': {'marker': 'o'},
    'phi_s': {'marker': 'o'},
    'k_e': {'marker': 'o'},
    # Particle
    'z_abs': {'marker': None},
    'w_kin': {'marker': None},
    'phi_abs_array': {'marker': None},
    'beta': {'marker': None},
    # Misc
    'struct': {'marker': None},
    'err_abs': {'marker': None},
    'err_rel': {'marker': None},
    'err_log': {'marker': None},
    # ListOfElements
    # TraceWin
}

d_lw_to_tw = {
    # Accelerator
    'eps_zdelta': 'ezdp',
    'envelope_pos_z': 'SizeZ',
    'envelope_pos_zdelta': 'SizeZ',
    'envelope_pos_w': 'SizeP',
    'envelope_energy_w': 'spW',
    'envelope_energy_zdelta': 'szdp',
    # Element
    'elt_idx': 'Cav#',
    'elt number': '##',
    # RfField
    'v_cav_mv': 'Voltage[MV]',
    'phi_s': 'SyncPhase[°]',
    # 'k_e':
    # Particle
    'z_abs': 'z(m)',
    # 'w_kin': Computed in Accelerator.precompute_some_tracewin_results,
    # 'phi_abs_array': Computed in Accelerator.precompute_some_tracewin_results,
    # Misc
    # List OfElements
    # TraceWin
    'lost power': 'Powlost',
    }

d_lw_to_tw_func = {
    'eps_zdelta': lambda x: x * 1e-6,
    'envelope_pos_zdelta': lambda x: x * 1e-3,
    'envelope_energy_zdelta': lambda x: x * 1e-3,
    'elt_idx': lambda x: x - 1,
    }
