"""Define class generating :class:`.BeamParameters` for :class:`.Envelope1D`."""

import numpy as np

from lightwin.core.beam_parameters.beam_parameters import BeamParameters
from lightwin.core.beam_parameters.factory import BeamParametersFactory
from lightwin.core.elements.element import ELEMENT_TO_INDEX_T
from lightwin.core.transfer_matrix.transfer_matrix import TransferMatrix


class BeamParametersFactoryEnvelope1D(BeamParametersFactory):
    """A class holding method to generate :class:`.BeamParameters`."""

    def factory_method(
        self,
        sigma_in: np.ndarray,
        z_abs: np.ndarray,
        gamma_kin: np.ndarray,
        transfer_matrix: TransferMatrix,
        element_to_index: ELEMENT_TO_INDEX_T,
    ) -> BeamParameters:
        """Create the :class:`.BeamParameters` object."""
        z_abs, gamma_kin, beta_kin = self._check_and_set_arrays(
            z_abs, gamma_kin
        )
        sigma_in = self._check_sigma_in(sigma_in)

        beam_parameters = BeamParameters(
            z_abs,
            gamma_kin,
            beta_kin,
            sigma_in=sigma_in,
            element_to_index=element_to_index,
        )

        phase_space_names = ("zdelta",)
        sub_transf_mat_names = ("r_zdelta",)
        transfer_matrices = (transfer_matrix.get(*sub_transf_mat_names),)
        self._set_from_transfer_matrix(
            beam_parameters,
            phase_space_names,
            transfer_matrices,
            gamma_kin,
            beta_kin,
        )

        other_phase_space_name = "zdelta"
        phase_space_names = ("z", "phiw")
        self._set_from_other_phase_space(
            beam_parameters,
            other_phase_space_name,
            phase_space_names,
            gamma_kin,
            beta_kin,
        )
        return beam_parameters
