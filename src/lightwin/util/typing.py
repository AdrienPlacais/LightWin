"""Define types for better code-completion and linting."""

from typing import Literal

#: Type for the different phase spaces.
PHASE_SPACE_T = Literal[
    "phiw", "phiw99", "t", "x", "x99", "y", "y99", "z", "zdelta"
]
#: List of different phase spaces.
PHASE_SPACES = ("phiw", "phiw99", "t", "x", "x99", "y", "y99", "z", "zdelta")

#: Attributes that are stored in :class:`.InitialPhaseSpaceBeamParameters` and
#: :class:`.PhaseSpaceBeamParameters`.
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
