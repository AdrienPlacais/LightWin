"""Define class to compute beam propagation in envelope, 1D, no space-charge.

This solver is fast, but should not be used at low energies.

Almost everything is inherited from the Python version of the solver,
:class:`.Envelope1D`.

"""

from pathlib import Path

from lightwin.beam_calculation.cy_envelope_1d.element_parameters_factory import (
    ElementCyEnvelope1DParametersFactory,
)
from lightwin.beam_calculation.cy_envelope_1d.simulation_output_factory import (
    SimulationOutputFactoryCyEnvelope1D,
)
from lightwin.beam_calculation.cy_envelope_1d.util import (
    CY_ENVELOPE1D_METHODS_T,
)
from lightwin.beam_calculation.envelope_1d.envelope_1d import Envelope1D
from lightwin.core.list_of_elements.factory import ListOfElementsFactory
from lightwin.util.synchronous_phases import PHI_S_MODELS


class CyEnvelope1D(Envelope1D):
    """The fastest beam calculator, adapted to high energies."""

    flag_cython = True

    def __init__(
        self,
        *,
        flag_phi_abs: bool,
        n_steps_per_cell: int,
        method: CY_ENVELOPE1D_METHODS_T,
        out_folder: Path | str,
        default_field_map_folder: Path | str,
        phi_s_definition: PHI_S_MODELS = "historical",
        **kwargs,
    ) -> None:
        """Set the proper motion integration function, according to inputs."""
        return super().__init__(
            flag_phi_abs=flag_phi_abs,
            n_steps_per_cell=n_steps_per_cell,
            method=method,
            out_folder=out_folder,
            default_field_map_folder=default_field_map_folder,
            phi_s_definition=phi_s_definition,
            **kwargs,
        )

    def _set_up_specific_factories(self) -> None:
        """Set up the factories specific to the :class:`.BeamCalculator`.

        This method is called in the :meth:`.BeamCalculator.__init__`, hence it
        appears only in the base :class:`.BeamCalculator`.

        """
        self.simulation_output_factory = SimulationOutputFactoryCyEnvelope1D(
            _is_3d=self.is_a_3d_simulation,
            _is_multipart=self.is_a_multiparticle_simulation,
            _solver_id=self.id,
            _beam_kwargs=self._beam_kwargs,
            out_folder=self.out_folder,
        )
        self.beam_calc_parameters_factory = (
            ElementCyEnvelope1DParametersFactory(
                method=self.method,
                n_steps_per_cell=self.n_steps_per_cell,
                solver_id=self.id,
                beam_kwargs=self._beam_kwargs,
            )
        )
        self.list_of_elements_factory = ListOfElementsFactory(
            self.is_a_3d_simulation,
            self.is_a_multiparticle_simulation,
            beam_kwargs=self._beam_kwargs,
            default_field_map_folder=self.default_field_map_folder,
            load_rf_field=True,
            load_field=True,
            load_cython_field_maps=True,
            field_maps_in_3d=False,  # not implemented anyway
            elements_to_dump=(),
        )
