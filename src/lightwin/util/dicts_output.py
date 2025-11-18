"""Here we define functions to make proper outputs of various quantities.

.. note::
    By default, all phases are stored in radians (more computer friendly).
    In outputs, they are always converted to degrees (more human friendly),
    which is why units are degrees in following markdown dictionaries.

.. todo::
   ``markdown`` holds complete names, not markdown related!
   Fill up full_name for that.

"""

full_name = {
    "acceptance_energy": "Energy acceptance [MeV]",
    "acceptance_phi": "Phase acceptance [deg]",
    "phi_s": "Synch. phase [deg]",
    "v_cav_mv": "Acc. field [MV]",
    "w_kin": "Beam energy [MeV]",
}

markdown = {
    "acceptance_energy": "$A_E$ [MeV]",
    "acceptance_phi": r"$A_\phi$ [deg]",
    "alpha_phiw": r"$\alpha_{\phi W}$ [1]",
    "alpha_z": r"$\alpha_{zz'}$ [1]",
    "alpha_zdelta": r"$\alpha_{z\delta}$ [1]",
    "beta": r"Synch. $\beta$ [1]",
    "beta_kin": r"Lorentz $\beta$ [1]",
    "beta_phiw": r"$\beta_{\phi W}$ [deg/$\pi$.MeV]",
    "beta_z": r"$\beta_{zz'}$ [mm/$\pi$.mrad]",
    "beta_zdelta": r"$\beta_{z\delta}$ [mm/$\pi$.%]",
    "elt number": "Element number",
    "elt_idx": "Element index",
    "envelope_energy_phiw": r"Norm. $\sigma_\phi$ @ $1\sigma$ [MeV]",
    "envelope_energy_z": r"$\sigma_{z'}$ @ $1\sigma$ [mrad]",
    "envelope_energy_zdelta": r"$\sigma_\delta$ @ $1\sigma$ [%]",
    "envelope_pos_phiw": r"Norm. $\sigma_\phi$ @ $1\sigma$ [deg]",
    "envelope_pos_z": r"$\sigma_z$ @ $1\sigma$ [mm]",
    "envelope_pos_zdelta": r"$\sigma_z$ @ $1\sigma$ [mm]",
    "eps_phiw": r"Norm. $\epsilon_{\phi W}$ [$\pi$.deg.MeV]",
    "eps_phiw99": r"Norm. 99% $\epsilon_{zz'}$ [$\pi$mm mrad]",
    "eps_t": r"Norm. RMS $\epsilon_t$ [$\pi$mm mrad]",
    "eps_x": r"Norm. RMS $\epsilon_{xx'}$ [$\pi$mm mrad]",
    "eps_x99": r"Norm. 99% $\epsilon_{xx'}$ [$\pi$mm mrad]",
    "eps_y": r"Norm. RMS $\epsilon_{yy'}$ [$\pi$mm mrad]",
    "eps_y99": r"Norm. 99% $\epsilon_{yy'}$ [$\pi$mm mrad]",
    "eps_z": r"Norm. RMS $\epsilon_{zz'}$ [$\pi$.mm.mrad]",
    "eps_zdelta": r"Norm. $\epsilon_{z\delta}$ [$\pi$.mm.%]",
    "err_abs": "Abs. error",
    "err_log": "log of rel. error",
    "err_rel": "Rel. error",
    "err_simple": "Error",
    "gamma_kin": r"Lorentz $\gamma$ [1]",
    "gamma_phiw": r"$\gamma_{\phi W}$ [MeV/$\pi$.deg]",
    "gamma_z": r"$\gamma_{zz'}$ [mrad/$\pi$.mm]",
    "gamma_zdelta": r"$\gamma_{z\delta}$ [%/$\pi$.mm]",
    "k_e": r"$k_e$ [1]",
    "mismatch_factor": r"$M$",
    "mismatch_factor_t": r"$M_t$",
    "mismatch_factor_x": r"$M_{xx'}$",
    "mismatch_factor_y": r"$M_{yy'}$",
    "mismatch_factor_zdelta": r"$M_{z\delta}$",
    "non_norm_eps_phiw": r"$\epsilon_{\phi W}$ [$\pi$.deg.MeV]",
    "non_norm_eps_z": r"RMS $\epsilon_{zz'}$ [$\pi$.mm.mrad]",
    "non_norm_eps_zdelta": r"$\epsilon_{z\delta}$ [$\pi$.mm.%]",
    "optimisation_time": "Optimisation time",
    "phi_0_abs": r"$\phi_{0, abs}$ [deg]",
    "phi_0_rel": r"$\phi_{0, rel}$ [deg]",
    "phi_abs": "Beam phase [deg]",
    "phi_s": r"$\phi_s$ [deg]",
    "pow_lost": "Lost power [W]",
    "r_zdelta_11": r"$(M_{z\delta})_{1,\,1}$",
    "r_zdelta_12": r"$(M_{z\delta})_{1,\,2}$",
    "r_zdelta_21": r"$(M_{z\delta})_{2,\,1}$",
    "r_zdelta_22": r"$(M_{z\delta})_{2,\,2}$",
    "struct": "Structure",
    "v_cav_mv": r"$V_{cav}$ [MV]",
    "w_kin": "$W_{kin}$ [MeV]",
    "z_abs": "Synch. position [m]",
}

plot_kwargs = {
    # Accelerator
    "eps_zdelta": {"marker": None},
    "eps_z": {"marker": None},
    "eps_phiw": {"marker": None},
    "alpha_zdelta": {"marker": None},
    "alpha_z": {"marker": None},
    "alpha_phiw": {"marker": None},
    "beta_zdelta": {"marker": None},
    "beta_z": {"marker": None},
    "beta_phiw": {"marker": None},
    "gamma_zdelta": {"marker": None},
    "gamma_z": {"marker": None},
    "gamma_phiw": {"marker": None},
    "envelope_pos_zdelta": {"marker": None},
    "envelope_pos_z": {"marker": None},
    "envelope_pos_phiw": {"marker": None},
    "envelope_energy_zdelta": {"marker": None},
    "envelope_energy_z": {"marker": None},
    "envelope_energy_phiw": {"marker": None},
    "mismatch_factor_zdelta": {"marker": None},
    "acceptance_energy": {"marker": "s"},
    "acceptance_phi": {"marker": "s"},
    # Element
    "elt_idx": {"marker": None},
    # RfField
    "v_cav_mv": {"marker": "o"},
    "phi_s": {"marker": "o"},
    "k_e": {"marker": "o"},
    # Particle
    "z_abs": {"marker": None},
    "w_kin": {"marker": None},
    "phi_abs": {"marker": None},
    "beta": {"marker": None},
    # Misc
    "struct": {"marker": None},
    "err_abs": {"marker": None},
    "err_rel": {"marker": None},
    "err_log": {"marker": None},
    # ListOfElements
    #
    "r_zdelta_11": {"marker": None},
    "r_zdelta_12": {"marker": None},
    "r_zdelta_21": {"marker": None},
    "r_zdelta_22": {"marker": None},
}
