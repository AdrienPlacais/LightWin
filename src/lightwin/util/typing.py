"""Define types for better code-completion and linting."""

from typing import Literal, TypedDict

from numpy.typing import NDArray

#: List of different phase spaces.
PHASE_SPACES = ("phiw", "phiw99", "t", "x", "x99", "y", "y99", "z", "zdelta")
PHASE_SPACE_T = Literal[
    "phiw", "phiw99", "t", "x", "x99", "y", "y99", "z", "zdelta"
]

#: Attributes that are stored in :class:`.InitialPhaseSpaceBeamParameters` and
#: :class:`.PhaseSpaceBeamParameters`.
GETTABLE_BEAM_PARAMETERS_PHASE_SPACE = (
    "alpha",
    "beta",
    "beta_kin",
    "envelope_energy",
    "envelope_pos",
    "eps",
    "eps_no_normalization",
    "eps_normalized",
    "gamma",
    "gamma_kin",
    "sigma",
    "twiss",
    "z_abs",
) + PHASE_SPACES
GETTABLE_BEAM_PARAMETERS_PHASE_SPACE_T = (
    Literal[
        "alpha",
        "beta",
        "beta_kin",
        "envelope_energy",
        "envelope_pos",
        "eps",
        "eps_no_normalization",
        "eps_normalized",
        "gamma",
        "gamma_kin",
        "sigma",
        "twiss",
        "z_abs",
    ]
    | PHASE_SPACE_T
)

#: Attributes that are stored in :class:`.InitialBeamParameters` and
#: :class:`.BeamParameters`.
GETTABLE_BEAM_PARAMETERS = (
    # fmt: off
    (
        "alpha_phiw", "beta_phiw", "envelope_energy_phiw", "envelope_pos_phiw", "eps_phiw", "eps_no_normalization_phiw", "eps_normalized_phiw", "gamma_phiw", "sigma_phiw", "twiss_phiw",
        "alpha_phiw99", "beta_phiw99", "envelope_energy_phiw99", "envelope_pos_phiw99", "eps_phiw99", "eps_no_normalization_phiw99", "eps_normalized_phiw99", "gamma_phiw99", "sigma_phiw99", "twiss_phiw99",
        "alpha_t", "beta_t", "envelope_energy_t", "envelope_pos_t", "eps_t", "eps_no_normalization_t", "eps_normalized_t", "gamma_t", "sigma_t", "twiss_t",
        "alpha_x", "beta_x", "envelope_energy_x", "envelope_pos_x", "eps_x", "eps_no_normalization_x", "eps_normalized_x", "gamma_x", "sigma_x", "twiss_x",
        "alpha_x99", "beta_x99", "envelope_energy_x99", "envelope_pos_x99", "eps_x99", "eps_no_normalization_x99", "eps_normalized_x99", "gamma_x99", "sigma_x99", "twiss_x99",
        "alpha_y", "beta_y", "envelope_energy_y", "envelope_pos_y", "eps_y", "eps_no_normalization_y", "eps_normalized_y", "gamma_y", "sigma_y", "twiss_y",
        "alpha_y99", "beta_y99", "envelope_energy_y99", "envelope_pos_y99", "eps_y99", "eps_no_normalization_y99", "eps_normalized_y99", "gamma_y99", "sigma_y99", "twiss_y99",
        "alpha_z", "beta_z", "envelope_energy_z", "envelope_pos_z", "eps_z", "eps_no_normalization_z", "eps_normalized_z", "gamma_z", "sigma_z", "twiss_z",
        "alpha_zdelta", "beta_zdelta", "envelope_energy_zdelta", "envelope_pos_zdelta", "eps_zdelta", "eps_no_normalization_zdelta", "eps_normalized_zdelta", "gamma_zdelta", "sigma_zdelta", "twiss_zdelta",
    ) + GETTABLE_BEAM_PARAMETERS_PHASE_SPACE
    # fmt: on
)
GETTABLE_BEAM_PARAMETERS_T = (
    # fmt: off
    Literal[
        "alpha_phiw", "beta_phiw", "envelope_energy_phiw", "envelope_pos_phiw", "eps_phiw", "eps_no_normalization_phiw", "eps_normalized_phiw", "gamma_phiw", "sigma_phiw", "twiss_phiw",
        "alpha_phiw99", "beta_phiw99", "envelope_energy_phiw99", "envelope_pos_phiw99", "eps_phiw99", "eps_no_normalization_phiw99", "eps_normalized_phiw99", "gamma_phiw99", "sigma_phiw99", "twiss_phiw99",
        "alpha_t", "beta_t", "envelope_energy_t", "envelope_pos_t", "eps_t", "eps_no_normalization_t", "eps_normalized_t", "gamma_t", "sigma_t", "twiss_t",
        "alpha_x", "beta_x", "envelope_energy_x", "envelope_pos_x", "eps_x", "eps_no_normalization_x", "eps_normalized_x", "gamma_x", "sigma_x", "twiss_x",
        "alpha_x99", "beta_x99", "envelope_energy_x99", "envelope_pos_x99", "eps_x99", "eps_no_normalization_x99", "eps_normalized_x99", "gamma_x99", "sigma_x99", "twiss_x99",
        "alpha_y", "beta_y", "envelope_energy_y", "envelope_pos_y", "eps_y", "eps_no_normalization_y", "eps_normalized_y", "gamma_y", "sigma_y", "twiss_y",
        "alpha_y99", "beta_y99", "envelope_energy_y99", "envelope_pos_y99", "eps_y99", "eps_no_normalization_y99", "eps_normalized_y99", "gamma_y99", "sigma_y99", "twiss_y99",
        "alpha_z", "beta_z", "envelope_energy_z", "envelope_pos_z", "eps_z", "eps_no_normalization_z", "eps_normalized_z", "gamma_z", "sigma_z", "twiss_z",
        "alpha_zdelta", "beta_zdelta", "envelope_energy_zdelta", "envelope_pos_zdelta", "eps_zdelta", "eps_no_normalization_zdelta", "eps_normalized_zdelta", "gamma_zdelta", "sigma_zdelta", "twiss_zdelta",
    ] | GETTABLE_BEAM_PARAMETERS_PHASE_SPACE_T
    # fmt: on
)

#: Attributes stored in the :attr:`.ParticleFullTrajectory.beam` dictionary.
BEAM_KEYS = (
    "e_mev",
    "e_rest_mev",
    "f_bunch_mhz",
    "i_milli_a",
    "q_adim",
    "sigma",
    "inv_e_rest_mev",
    "gamma_init",
    "omega_0_bunch",
    "lambda_bunch",
    "q_over_m",
    "m_over_q",
)
BEAM_KEYS_T = Literal[
    "e_mev",
    "e_rest_mev",
    "f_bunch_mhz",
    "i_milli_a",
    "q_adim",
    "sigma",
    "inv_e_rest_mev",
    "gamma_init",
    "omega_0_bunch",
    "lambda_bunch",
    "q_over_m",
    "m_over_q",
]

#: Attributes that can be extracted with :meth:`.ParticleFullTrajectory.get`
#: method.
GETTABLE_PARTICLE = (
    "beta",
    "gamma",
    "phi_abs",
    "synchronous",
    "w_kin",
    "z_in",
) + BEAM_KEYS
GETTABLE_PARTICLE_T = (
    Literal["beta", "gamma", "phi_abs", "synchronous", "w_kin", "z_in"]
    | BEAM_KEYS_T
)

#: Attributes that can be extracted with
#: :meth:`.ElementBeamCalculatorParameters.get` method.
GETTABLE_BEAM_CALC_PARAMETERS = (
    "abs_mesh",
    "d_z",
    "n_steps",
    "rel_mesh",
    "s_in",
    "s_out",
    "transf_mat_function",
)
GETTABLE_BEAM_CALC_PARAMETERS_T = Literal[
    "abs_mesh",
    "d_z",
    "n_steps",
    "rel_mesh",
    "s_in",
    "s_out",
    "transf_mat_function",
]

#: The three types of reference phase
REFERENCE_PHASES = ("phi_0_abs", "phi_0_rel", "phi_s")
REFERENCE_PHASES_T = Literal["phi_0_abs", "phi_0_rel", "phi_s"]

#: How phases can be saved in the output ``DAT`` file.
EXPORT_PHASES = (
    "as_in_original_dat",
    "as_in_settings",
    "phi_0_abs",
    "phi_0_rel",
    "phi_s",
)
EXPORT_PHASES_T = (
    REFERENCE_PHASES_T | Literal["as_in_settings", "as_in_original_dat"]
)

#: Different status for cavities
ALLOWED_STATUS = (
    "nominal",
    "rephased (in progress)",
    "rephased (ok)",
    "failed",
    "compensate (in progress)",
    "compensate (ok)",
    "compensate (not ok)",
)
STATUS_T = Literal[
    "compensate (in progress)",  # Trying to fit
    "compensate (not ok)",  # Compensating, proper setting found
    "compensate (ok)",  # Compensating, proper setting not found
    "failed",  # Cavity norm is 0
    "nominal",  # Cavity settings not changed from .dat
    "rephased (in progress)",  # Cavity ABSOLUTE phase changed; relative phase unchanged
    "rephased (ok)",
]

#: Attributes that can be extracted with :meth:`.RfField.get` method.
GETTABLE_RF_FIELD = (
    "e_spat",
    "n_cell",
    "n_z",
    "starting_position",
    "section_idx",
)
GETTABLE_RF_FIELD_T = Literal[
    "e_spat",
    "n_cell",
    "n_z",
    "starting_position",
    "section_idx",
]

#: Attributes that can be extracted with :meth:`.CavitySettings.get` method.
GETTABLE_CAVITY_SETTINGS = (
    (
        "acceptance_energy",
        "field",
        "freq_cavity_mhz",
        "k_e",
        "omega_0_rf",
        "acceptance_phi",
        "phi_ref",
        "phi_rf",
        "phi_s",
        "phi_s_func",
        "reference",
        "rf_field",
        "status",
        "v_cav_mv",
        "w_kin",
    )
    + REFERENCE_PHASES
    + GETTABLE_RF_FIELD
)
GETTABLE_CAVITY_SETTINGS_T = (
    Literal[
        "acceptance_energy",
        "field",
        "freq_cavity_mhz",
        "k_e",
        "omega_0_rf",
        "acceptance_phi",
        "phi_ref",
        "phi_rf",
        "phi_s",
        "phi_s_func",
        "reference",
        "rf_field",
        "status",
        "v_cav_mv",
        "w_kin",
    ]
    | REFERENCE_PHASES_T
    | GETTABLE_RF_FIELD_T
)

#: Attributes from :class:`.CavitySettings` to concatenate into
#: a list when called from :meth:`.SetOfCavitySettings.get` (or
#: :meth:`.SimulationOutput.get`)
CONCATENABLE_CAVITY_SETTINGS = (
    "v_cav_mv",
    "phi_0_abs",
    "phi_0_rel",
    "phi_bunch",
    "phi_ref",
    "phi_rf",
    "phi_s",
    "acceptance_phi",
    "acceptance_energy",
)

#: Attributes that can be extracted with :meth:`.Element.get` method.
GETTABLE_ELT = (
    "dat_idx",
    "elt_idx",
    "idx",
    "idx_in_lattice",
    "lattice",
    "length_m",
    "name",
    "nature",
    "section",
) + GETTABLE_BEAM_CALC_PARAMETERS
GETTABLE_ELT_T = (
    Literal[
        "dat_idx",
        "elt_idx",
        "idx",
        "idx_in_lattice",
        "lattice",
        "length_m",
        "name",
        "nature",
        "section",
    ]
    | GETTABLE_BEAM_CALC_PARAMETERS_T
)

#: Attributes that can be extracted with :meth:`.FieldMap.get` method.
GETTABLE_FIELD_MAP = (
    ("aperture_flag", "field_map_filename", "field_map_folder", "geometry")
    + GETTABLE_RF_FIELD
    + GETTABLE_ELT
    + GETTABLE_CAVITY_SETTINGS
)
GETTABLE_FIELD_MAP_T = (
    Literal[
        "aperture_flag", "field_map_filename", "field_map_folder", "geometry"
    ]
    | GETTABLE_RF_FIELD_T
    | GETTABLE_ELT_T
    | GETTABLE_CAVITY_SETTINGS_T
)

_UNCONCATENABLE = (
    # Confusion between energy along linac, and energy at entrance of field
    # maps used to compute phi_s and v_cav
    "w_kin",
)
#: Attributes from :class:`.Element` or :class:`.FieldMap` to concatenate into
#: a list when called from :meth:`.ListOfElements.get` (or
#: :meth:`.SimulationOutput.get`, :meth:`.Accelerator.get`)
CONCATENABLE_ELTS = tuple(
    [key for key in GETTABLE_FIELD_MAP if key not in _UNCONCATENABLE]
)
CONCATENABLE_ELTS_T = (
    Literal[
        "aperture_flag", "field_map_filename", "field_map_folder", "geometry"
    ]
    | GETTABLE_RF_FIELD_T
    | GETTABLE_ELT_T
    # GETTABLE_CAVITY_SETTINGS_T without w_kin
    | Literal[
        "acceptance_energy",
        "field",
        "freq_cavity_mhz",
        "k_e",
        "omega_0_rf",
        "acceptance_phi",
        "phi_ref",
        "phi_rf",
        "phi_s_func",
        "reference",
        "rf_field",
        "status",
        "v_cav_mv",
    ]
    | REFERENCE_PHASES_T
)

#: Attributes that can be extracted with :meth:`.ListOfElements.get` method.
GETTABLE_ELTS = (
    (
        "accelerator_path",
        "dat_file",
        "dat_filecontent",
        "elts_n_cmds",
        "files",
        "input_beam",
        "input_particle",
        "tm_cumul_in",
    )
    + GETTABLE_FIELD_MAP
    + GETTABLE_PARTICLE
    + GETTABLE_BEAM_PARAMETERS
)
GETTABLE_ELTS_T = (
    Literal[
        "accelerator_path",
        "dat_file",
        "dat_filecontent",
        "elts_n_cmds",
        "files",
        "input_beam",
        "input_particle",
        "tm_cumul_in",
    ]
    | GETTABLE_FIELD_MAP_T
    | GETTABLE_PARTICLE_T
    | GETTABLE_BEAM_PARAMETERS_T
)

#: Attributes that are structure-dependent and should not vary from simulation
#: to simulation
GETTABLE_STRUCTURE_DEPENDENT = (
    GETTABLE_ELT
    + GETTABLE_RF_FIELD
    + (
        "aperture_flag",
        "field_map_filename",
        "field_map_folder",
        "geometry",
        "field",
        "freq_cavity_mhz",
        "omega_0_rf",
    )
)

#: Attributes that can be extracted with :meth:`.TransferMatrix.get` method.
GETTABLE_TRANSFER_MATRIX = (
    "cumulated",
    "individual",
    "n_points",
    "r_xx",
    "r_yy",
    "r_zdelta",
    "r_zdelta_11",
    "r_zdelta_12",
    "r_zdelta_21",
    "r_zdelta_22",
    "r_zz",
)
GETTABLE_TRANSFER_MATRIX_T = Literal[
    "cumulated",
    "individual",
    "n_points",
    "r_xx",
    "r_yy",
    "r_zdelta",
    "r_zz",
    "r_zdelta_11",
    "r_zdelta_12",
    "r_zdelta_21",
    "r_zdelta_22",
]

#: Attributes that can be extracted with :meth:`.SimulationOutput.get` method.
GETTABLE_SIMULATION_OUTPUT = (
    (
        "beam_parameters",
        "element_to_index",
        "elt_idx",
        "phi_s",
        "set_of_cavity_settings",
        "synch_trajectory",
        "v_cav_mv",
        "z_abs",
    )
    + GETTABLE_BEAM_PARAMETERS
    + GETTABLE_PARTICLE
    + GETTABLE_TRANSFER_MATRIX
)
GETTABLE_SIMULATION_OUTPUT_T = (
    Literal[
        "beam_parameters",
        "element_to_index",
        "elt_idx",
        "phi_s",
        "set_of_cavity_settings",
        "synch_trajectory",
        "v_cav_mv",
        "z_abs",
    ]
    | GETTABLE_BEAM_PARAMETERS_T
    | GETTABLE_PARTICLE_T
    | GETTABLE_TRANSFER_MATRIX_T
)

#: Attributes that can be extracted with :meth:`.Accelerator.get` method.
GETTABLE_ACCELERATOR = (
    "accelerator_path",
    "elts",
    "name",
    "simulation_outputs",
) + GETTABLE_ELTS
GETTABLE_ACCELERATOR_T = (
    Literal["accelerator_path", "elts", "name", "simulation_outputs"]
    | GETTABLE_ELTS_T
)


class BeamKwargs(TypedDict):
    """Holds all beam properties."""

    e_mev: float
    e_rest_mev: float
    f_bunch_mhz: float
    i_milli_a: float
    q_adim: float
    sigma: NDArray
    inv_e_rest_mev: float
    gamma_init: float
    omega_0_bunch: float
    lambda_bunch: float
    q_over_m: float
    m_over_q: float
