"""Define a class to easily generate the |SO|."""

from abc import ABCMeta
from pathlib import Path

import numpy as np

from lightwin.beam_calculation.envelope_1d.beam_parameters_factory import (
    BeamParametersFactoryEnvelope1D,
)
from lightwin.beam_calculation.envelope_1d.transfer_matrix_factory import (
    TransferMatrixFactoryEnvelope1D,
)
from lightwin.beam_calculation.simulation_output.factory import (
    SimulationOutputFactory,
)
from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.core.particle import ParticleFullTrajectory
from lightwin.core.transfer_matrix.transfer_matrix import TransferMatrix
from lightwin.failures.set_of_cavity_settings import SetOfCavitySettings
from lightwin.util.typing import GETTABLE_CAVITY_SETTINGS_T, CavParams


class SimulationOutputFactoryEnvelope1D(SimulationOutputFactory):
    """A class for creating simulation outputs for :class:`.Envelope1D`."""

    _is_3d = False

    @property
    def _transfer_matrix_factory_class(self) -> ABCMeta:
        """Give the **class** of the transfer matrix factory."""
        return TransferMatrixFactoryEnvelope1D

    @property
    def _beam_parameters_factory_class(self) -> ABCMeta:
        """Give the **class** of the beam parameters factory."""
        return BeamParametersFactoryEnvelope1D

    def create(
        self,
        accelerator_id: str,
        elts: ListOfElements,
        single_elts_results: list[dict],
        set_of_cavity_settings: SetOfCavitySettings,
    ) -> SimulationOutput:
        """Transform the outputs of BeamCalculator to a SimulationOutput.

        .. todo::
            Patch in transfer matrix to get proper input transfer matrix. In
            future, input beam will not hold transf mat in anymore.

        """
        synch_trajectory = ParticleFullTrajectory(
            w_kin=self._format_w_kin(elts, single_elts_results),
            phi_abs=self._format_phi_abs(elts, single_elts_results),
            synchronous=True,
            beam=self._beam_kwargs,
        )

        element_to_index = elts.generate_element_to_index_func(
            self._beam_calculator_id
        )
        transfer_matrix: TransferMatrix = self.transfer_matrix_factory.run(
            elts.tm_cumul_in, single_elts_results, element_to_index
        )

        z_abs = elts.get("abs_mesh", remove_first=True)
        gamma_kin = synch_trajectory.gamma
        assert isinstance(gamma_kin, np.ndarray)

        beam_parameters = self.beam_parameters_factory.factory_method(
            elts.input_beam.sigma,
            z_abs,
            gamma_kin,
            transfer_matrix,
            element_to_index,
        )

        simulation_output = SimulationOutput(
            accelerator_id=accelerator_id,
            beam_calculator_id=self._beam_calculator_id,
            elts=elts,
            is_multiparticle=self._is_multipart,
            is_3d=self._is_3d,
            synch_trajectory=synch_trajectory,
            cav_params=self._get_cav_params(set_of_cavity_settings, elts),
            beam_parameters=beam_parameters,
            element_to_index=element_to_index,
            transfer_matrix=transfer_matrix,
            set_of_cavity_settings=set_of_cavity_settings,
        )
        return simulation_output

    def _format_w_kin(
        self, elts: ListOfElements, single_elts_results: list[dict]
    ) -> list[float]:
        w_kin = [
            energy
            for results in single_elts_results
            for energy in results["w_kin"]
        ]
        w_kin.insert(0, elts.w_kin_in)
        return w_kin

    def _format_phi_abs(
        self, elts: ListOfElements, single_elts_results: list[dict]
    ) -> list[float]:
        phi_abs_array = [elts.phi_abs_in]
        for elt_results in single_elts_results:
            phi_abs = [
                phi_rel + phi_abs_array[-1]
                for phi_rel in elt_results["phi_rel"]
            ]
            phi_abs_array.extend(phi_abs)
        return phi_abs_array

    def _get_cav_params(
        self, set_of_cavity_settings: SetOfCavitySettings, elts: ListOfElements
    ) -> CavParams:

        def get(attr: GETTABLE_CAVITY_SETTINGS_T) -> list[float | None]:
            return [
                (
                    getattr(set_of_cavity_settings[elt], attr)
                    if elt in set_of_cavity_settings
                    else None
                )
                for elt in elts
            ]

        return {
            "v_cav_mv": get("v_cav_mv"),
            "phi_s": get("phi_s"),
            "acceptance_phi": get("acceptance_phi"),
            "acceptance_energy": get("acceptance_energy"),
        }
