"""Define types for better code-completion and linting."""

from collections.abc import Collection
from pathlib import Path
from typing import Any, Literal, NotRequired, TypedDict

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
        "alpha_phiw", "alpha_phiw99", "alpha_t", "alpha_x", "alpha_x99", "alpha_y", "alpha_y99", "alpha_z", "alpha_zdelta",
        "beta_phiw", "beta_phiw99", "beta_t", "beta_x", "beta_x99", "beta_y", "beta_y99", "beta_z", "beta_zdelta",
        "envelope_energy_phiw", "envelope_energy_phiw99", "envelope_energy_t", "envelope_energy_x", "envelope_energy_x99", "envelope_energy_y", "envelope_energy_y99", "envelope_energy_z", "envelope_energy_zdelta",
        "envelope_pos_phiw", "envelope_pos_phiw99", "envelope_pos_t", "envelope_pos_x", "envelope_pos_x99", "envelope_pos_y", "envelope_pos_y99", "envelope_pos_z", "envelope_pos_zdelta",
        "eps_no_normalization_phiw", "eps_no_normalization_phiw99", "eps_no_normalization_t", "eps_no_normalization_x", "eps_no_normalization_x99", "eps_no_normalization_y", "eps_no_normalization_y99", "eps_no_normalization_z", "eps_no_normalization_zdelta",
        "eps_normalized_phiw", "eps_normalized_phiw99", "eps_normalized_t", "eps_normalized_x", "eps_normalized_x99", "eps_normalized_y", "eps_normalized_y99", "eps_normalized_z", "eps_normalized_zdelta",
        "eps_phiw", "eps_phiw99", "eps_t", "eps_x", "eps_x99", "eps_y", "eps_y99", "eps_z", "eps_zdelta",
        "gamma_phiw", "gamma_phiw99", "gamma_t", "gamma_x", "gamma_x99", "gamma_y", "gamma_y99", "gamma_z", "gamma_zdelta",
        "sigma_phiw", "sigma_phiw99", "sigma_t", "sigma_x", "sigma_x99", "sigma_y", "sigma_y99", "sigma_z", "sigma_zdelta",
        "twiss_phiw", "twiss_phiw99", "twiss_t", "twiss_x", "twiss_x99", "twiss_y", "twiss_y99", "twiss_z", "twiss_zdelta",
    )
    + GETTABLE_BEAM_PARAMETERS_PHASE_SPACE
    # fmt: on
)
GETTABLE_BEAM_PARAMETERS_T = (
    # fmt: off
    Literal[
        "alpha_phiw", "alpha_phiw99", "alpha_t", "alpha_x", "alpha_x99", "alpha_y", "alpha_y99", "alpha_z", "alpha_zdelta",
        "beta_phiw", "beta_phiw99", "beta_t", "beta_x", "beta_x99", "beta_y", "beta_y99", "beta_z", "beta_zdelta",
        "envelope_energy_phiw", "envelope_energy_phiw99", "envelope_energy_t", "envelope_energy_x", "envelope_energy_x99", "envelope_energy_y", "envelope_energy_y99", "envelope_energy_z", "envelope_energy_zdelta",
        "envelope_pos_phiw", "envelope_pos_phiw99", "envelope_pos_t", "envelope_pos_x", "envelope_pos_x99", "envelope_pos_y", "envelope_pos_y99", "envelope_pos_z", "envelope_pos_zdelta",
        "eps_no_normalization_phiw", "eps_no_normalization_phiw99", "eps_no_normalization_t", "eps_no_normalization_x", "eps_no_normalization_x99", "eps_no_normalization_y", "eps_no_normalization_y99", "eps_no_normalization_z", "eps_no_normalization_zdelta",
        "eps_normalized_phiw", "eps_normalized_phiw99", "eps_normalized_t", "eps_normalized_x", "eps_normalized_x99", "eps_normalized_y", "eps_normalized_y99", "eps_normalized_z", "eps_normalized_zdelta",
        "eps_phiw", "eps_phiw99", "eps_t", "eps_x", "eps_x99", "eps_y", "eps_y99", "eps_z", "eps_zdelta",
        "gamma_phiw", "gamma_phiw99", "gamma_t", "gamma_x", "gamma_x99", "gamma_y", "gamma_y99", "gamma_z", "gamma_zdelta",
        "sigma_phiw", "sigma_phiw99", "sigma_t", "sigma_x", "sigma_x99", "sigma_y", "sigma_y99", "sigma_z", "sigma_zdelta",
        "twiss_phiw", "twiss_phiw99", "twiss_t", "twiss_x", "twiss_x99", "twiss_y", "twiss_y99", "twiss_z", "twiss_zdelta",
    ]
    | GETTABLE_BEAM_PARAMETERS_PHASE_SPACE_T
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

#: Reference phase policy at |BC| creation. Note that some
#: cavities can see their reference phase change during execution of the code,
#: according to the compensations strategy.
REFERENCE_PHASE_POLICY = REFERENCE_PHASES + ("as_in_original_dat",)
REFERENCE_PHASE_POLICY_T = REFERENCE_PHASES_T | Literal["as_in_original_dat"]

#: How phases shall be saved in the output ``DAT`` file.
EXPORT_PHASES = REFERENCE_PHASE_POLICY + ("as_in_settings",)
EXPORT_PHASES_T = REFERENCE_PHASE_POLICY_T | Literal["as_in_settings"]

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
#: Different status for cavities
STATUS_T = Literal[
    "compensate (in progress)",  # Trying to fit
    "compensate (not ok)",  # Compensating, proper setting found
    "compensate (ok)",  # Compensating, proper setting not found
    "failed",  # Cavity norm is 0
    "nominal",  # Cavity settings not changed from .dat
    "rephased (in progress)",  # Cavity ABSOLUTE phase changed; relative phase unchanged
    "rephased (ok)",
]

#: Attributes that can be extracted with :meth:`.CavitySettings.get` method.
GETTABLE_CAVITY_SETTINGS = (
    "acceptance_energy",
    "acceptance_phi",
    "field",
    "freq_cavity_mhz",
    "k_e",
    "omega_0_rf",
    "phi_ref",
    "phi_rf",
    "phi_s",
    "reference",
    "status",
    "v_cav_mv",
) + REFERENCE_PHASES
GETTABLE_CAVITY_SETTINGS_T = (
    Literal[
        "acceptance_energy",
        "acceptance_phi",
        "field",
        "freq_cavity_mhz",
        "k_e",
        "omega_0_rf",
        "phi_ref",
        "phi_rf",
        "phi_s",
        "reference",
        "rf_field",
        "status",
        "v_cav_mv",
    ]
    | REFERENCE_PHASES_T
)

#: Attributes from |CS| to concatenate into
#: a list when called from :meth:`.ListOfElements.get` (or
#: :meth:`.SimulationOutput.get`)
CONCATENABLE_CAVITY_SETTINGS = (
    "acceptance_energy",
    "acceptance_phi",
    "phi_0_abs",
    "phi_0_rel",
    "phi_bunch",
    "phi_ref",
    "phi_rf",
    "phi_s",
    "v_cav_mv",
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
    + GETTABLE_ELT
    + GETTABLE_CAVITY_SETTINGS
)
GETTABLE_FIELD_MAP_T = (
    Literal[
        "aperture_flag", "field_map_filename", "field_map_folder", "geometry"
    ]
    | GETTABLE_ELT_T
    | GETTABLE_CAVITY_SETTINGS_T
)

_UNCONCATENABLE = (
    # Confusion between energy along linac, and energy at entrance of field
    # maps used to compute phi_s and v_cav
    "w_kin",
)
#: Attributes from |E| or |FM| to concatenate into
#: a list when called from :meth:`.ListOfElements.get` (or
#: :meth:`.SimulationOutput.get`, :meth:`.Accelerator.get`)
CONCATENABLE_ELTS = tuple(
    [key for key in GETTABLE_FIELD_MAP if key not in _UNCONCATENABLE]
)
CONCATENABLE_ELTS_T = (
    Literal[
        "aperture_flag", "field_map_filename", "field_map_folder", "geometry"
    ]
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
        "cav_number",
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
        "cav_number",
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
GETTABLE_STRUCTURE_DEPENDENT = GETTABLE_ELT + (
    "aperture_flag",
    "cav_number",
    "field_map_filename",
    "field_map_folder",
    "geometry",
    "field",
    "freq_cavity_mhz",
    "omega_0_rf",
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

#: Attributes that you can get from 3D |SO|.
NEEDS_3D = (
    # fmt: off
    "alpha_t", "alpha_x", "alpha_y",
    "beta_t", "beta_x", "beta_y",
    "envelope_energy_t", "envelope_energy_x", "envelope_energy_y",
    "envelope_pos_t", "envelope_pos_x", "envelope_pos_y",
    "eps_no_normalization_t", "eps_no_normalization_x", "eps_no_normalization_y",
    "eps_normalized_t", "eps_normalized_x", "eps_normalized_y",
    "eps_t", "eps_x", "eps_y",
    "gamma_t", "gamma_x", "gamma_y",
    "mismatch_factor_t", "mismatch_factor_x", "mismatch_factor_y",
    "sigma_t", "sigma_x", "sigma_y",
    "twiss_t", "twiss_x", "twiss_y",
    # fmt: on
)
NEEDS_3D_T = Literal[
    # fmt: off
    "alpha_t", "alpha_x", "alpha_y",
    "beta_t", "beta_x", "beta_y",
    "envelope_energy_t", "envelope_energy_x", "envelope_energy_y",
    "envelope_pos_t", "envelope_pos_x", "envelope_pos_y",
    "eps_no_normalization_t", "eps_no_normalization_x", "eps_no_normalization_y",
    "eps_normalized_t", "eps_normalized_x", "eps_normalized_y",
    "eps_t", "eps_x", "eps_y",
    "gamma_t", "gamma_x", "gamma_y",
    "mismatch_factor_t", "mismatch_factor_x", "mismatch_factor_y",
    "sigma_t", "sigma_x", "sigma_y",
    "twiss_t", "twiss_x", "twiss_y",
    # fmt: on
]
#: Attributes that you can get from multipart |SO|.
NEEDS_MULTIPART = ("eps_phiw99", "eps_x99", "eps_y99", "pow_lost")
NEEDS_MULTIPART_T = Literal["eps_phiw99", "eps_x99", "eps_y99", "pow_lost"]
#: Attributes that can be extracted with :meth:`.SimulationOutput.get` method.
GETTABLE_SIMULATION_OUTPUT = (
    (
        "acceptance_energy",
        "acceptance_phi",
        "beam_parameters",
        "cav_number",
        "element_to_index",
        "elt_idx",
        "mismatch_factor_zdelta",
        "phi_s",
        "set_of_cavity_settings",
        "synch_trajectory",
        "v_cav_mv",
        "z_abs",
    )
    + GETTABLE_BEAM_PARAMETERS
    + GETTABLE_PARTICLE
    + GETTABLE_TRANSFER_MATRIX
    + NEEDS_3D
    + NEEDS_MULTIPART
)
GETTABLE_SIMULATION_OUTPUT_T = (
    Literal[
        "acceptance_energy",
        "acceptance_phi",
        "beam_parameters",
        "cav_number",
        "element_to_index",
        "elt_idx",
        "mismatch_factor_zdelta",
        "phi_s",
        "set_of_cavity_settings",
        "synch_trajectory",
        "v_cav_mv",
        "z_abs",
    ]
    | GETTABLE_BEAM_PARAMETERS_T
    | GETTABLE_PARTICLE_T
    | GETTABLE_TRANSFER_MATRIX_T
    | NEEDS_3D_T
    | NEEDS_MULTIPART_T
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

#: Allowed values for the ``pos`` keyword argument in ``get`` methods.
POS_T = Literal["in", "out"]

#: Magic values for the ``elt`` keyword argument in ``get`` methods.
GET_ELT_ARG = ("first", "last")
GET_ELT_ARG_T = Literal["first", "last"]

#: Implemented optimization variables
VARIABLES = ("k_e",) + REFERENCE_PHASES
VARIABLES_T = Literal["k_e"] | REFERENCE_PHASES_T
#: Implemented optimization constraints
CONSTRAINTS = ("phi_s",)
CONSTRAINTS_T = Literal["phi_s"]
#: optimization status
OPTIMIZATION_STATUS = Literal["not started", "in progress", "finished"]

#: Implemented :class:`.DesignSpaceFactory` presets.
DESIGN_SPACES = (
    "AbsPhaseAmplitude",
    "AbsPhaseAmplitudeWithConstrainedSyncPhase",
    "Everything",
    "RelPhaseAmplitude",
    "RelPhaseAmplitudeWithConstrainedSyncPhase",
    "SyncPhaseAmplitude",
    "UserDefined",
    "abs_phase_amplitude",
    "abs_phase_amplitude_with_constrained_sync_phase",
    "everything",
    "rel_phase_amplitude",
    "rel_phase_amplitude_with_constrained_sync_phase",
    "sync_phase_amplitude",
    "user_defined",
    # Deprecated
    "unconstrained",
    "unconstrained_rel",
    "constrained_sync_phase",
    "sync_phase_as_variable",
)
DESIGN_SPACES_T = Literal[
    "AbsPhaseAmplitude",
    "AbsPhaseAmplitudeWithConstrainedSyncPhase",
    "Everything",
    "RelPhaseAmplitude",
    "RelPhaseAmplitudeWithConstrainedSyncPhase",
    "SyncPhaseAmplitude",
    "UserDefined",
    "abs_phase_amplitude",
    "abs_phase_amplitude_with_constrained_sync_phase",
    "everything",
    "rel_phase_amplitude",
    "rel_phase_amplitude_with_constrained_sync_phase",
    "sync_phase_amplitude",
    "user_defined",
    # Deprecated
    "unconstrained",
    "unconstrained_rel",
    "constrained_sync_phase",
    "sync_phase_as_variable",
]


class DesignSpaceKw(TypedDict):
    """Holds all ``TOML`` configuration entries for design space."""

    design_space_preset: DESIGN_SPACES_T

    from_file: bool
    variables_filepaths: NotRequired[Path]
    constraints_filepaths: NotRequired[Path]

    variable_names: NotRequired[Collection[VARIABLES_T]]
    constraints_names: NotRequired[Collection[CONSTRAINTS_T]]

    max_increase_sync_phase_in_percent: NotRequired[float]
    max_absolute_sync_phase_in_deg: NotRequired[float]
    min_absolute_sync_phase_in_deg: NotRequired[float]
    max_decrease_k_e_in_percent: NotRequired[float]
    max_increase_k_e_in_percent: NotRequired[float]
    maximum_k_e_is_calculated_wrt_maximum_k_e_of_section: NotRequired[bool]


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


class CavParams(TypedDict):
    """Holds cavity parameters in a |SO|.

    All lists have the length of the associated |LOE|. They contain ``None``
    where |E| is not a |FM|.

    """

    v_cav_mv: list[float | None]
    phi_s: list[float | None]
    acceptance_phi: NotRequired[list[float | None]]
    acceptance_energy: NotRequired[list[float | None]]
    phi_0: NotRequired[list[float | None]]


#: Allowed values for the ``id_nature`` key of ``wtf`` configuration table.
ID_NATURE = ("cavity", "element", "lattice", "name", "section")
ID_NATURE_T = Literal["cavity", "element", "lattice", "name", "section"]


class ConfigKw(TypedDict):
    """Holds all configuration dicts."""

    files: dict[str, Any]
    beam: BeamKwargs
    beam_calculator: dict[str, Any]
    beam_calculator_post: NotRequired[dict[str, Any]]
    plots: dict[str, Any]
    wtf: NotRequired[dict[str, Any]]
    design_space: NotRequired[DesignSpaceKw]
    evaluators: NotRequired[dict[str, Any]]
