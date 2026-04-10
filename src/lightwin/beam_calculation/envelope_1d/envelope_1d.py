"""Define class to compute beam propagation in envelope, 1D, no space-charge.

This solver is fast, but should not be used at low energies.

"""

import logging
from collections.abc import Collection
from pathlib import Path

from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.beam_calculation.envelope_1d.element_envelope1d_parameters import (
    ElementEnvelope1DParameters,
)
from lightwin.beam_calculation.envelope_1d.element_envelope1d_parameters_factory import (
    ElementEnvelope1DParametersFactory,
)
from lightwin.beam_calculation.envelope_1d.simulation_output_factory import (
    SimulationOutputFactoryEnvelope1D,
)
from lightwin.beam_calculation.envelope_1d.util import ENVELOPE1D_METHODS_T
from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.core.elements.field_maps.cavity_settings import CavitySettings
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.elements.field_maps.superposed_field_map import (
    SuperposedFieldMap,
)
from lightwin.core.list_of_elements.factory import ListOfElementsFactory
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.failures.set_of_cavity_settings import SetOfCavitySettings
from lightwin.physics.acceptance import compute_acceptances
from lightwin.physics.synchronous_phases import (
    PHI_S_MODELS,
    SYNCHRONOUS_PHASE_FUNCTIONS,
)
from lightwin.util.typing import (
    EXPORT_PHASES_T,
    REFERENCE_PHASE_POLICY_T,
    BeamKwargs,
)


class Envelope1D(BeamCalculator):
    """The fastest beam calculator, adapted to high energies.

    The following elements are explicitly supported. Note that, by default, an
    element that is implemented but not explicitly supported is replaced by a
    ``DRIFT``. In 1D, this is perfectly acceptable for most non-implemented
    elements that act on the transverse dynamics, such as ``THIN_LENS``.

    .. configkeys:: lightwin.beam_calculation.envelope_1d.element_envelope1d_parameters_factory.PARAMETERS_1D
       :n_cols: 3

    """

    flag_cython = False

    def __init__(
        self,
        *,
        reference_phase_policy: REFERENCE_PHASE_POLICY_T,
        default_field_map_folder: Path | str,
        beam_kwargs: BeamKwargs,
        export_phase: EXPORT_PHASES_T,
        phi_s_definition: PHI_S_MODELS = "historical",
        n_steps_per_cell: int,
        method: ENVELOPE1D_METHODS_T,
        **kwargs,
    ) -> None:
        """Set the proper motion integration function, according to inputs."""
        self.n_steps_per_cell = n_steps_per_cell
        self.method: ENVELOPE1D_METHODS_T = method
        super().__init__(
            reference_phase_policy=reference_phase_policy,
            default_field_map_folder=default_field_map_folder,
            beam_kwargs=beam_kwargs,
            export_phase=export_phase,
            **kwargs,
        )
        self._phi_s_definition = phi_s_definition
        self._phi_s_func = SYNCHRONOUS_PHASE_FUNCTIONS[self._phi_s_definition]

    def _set_up_specific_factories(self) -> None:
        """Set up the factories specific to the |BC|.

        This method is called in the :meth:`.BeamCalculator.__init__`, hence it
        appears only in the base |BC|.

        .. todo::
            ``default_field_map_folder`` has a wrong default value. Should take
            path to the ``.dat`` file, that is not known at this point. Maybe
            handle this directly in the :class:`.InstructionsFactory` or
            whatever.

        """
        self.simulation_output_factory = SimulationOutputFactoryEnvelope1D(
            is_multipart=self.is_a_multiparticle_simulation,
            beam_calculator_id=self.id,
            beam_kwargs=self._beam_kwargs,
        )
        self.beam_calc_parameters_factory = ElementEnvelope1DParametersFactory(
            method=self.method,
            n_steps_per_cell=self.n_steps_per_cell,
            solver_id=self.id,
            beam_kwargs=self._beam_kwargs,
        )
        self.list_of_elements_factory = ListOfElementsFactory(
            self.is_a_3d_simulation,
            self.is_a_multiparticle_simulation,
            default_field_map_folder=self.default_field_map_folder,
            load_fields=True,
            beam_kwargs=self._beam_kwargs,
            field_maps_in_3d=False,  # not implemented anyway
            load_cython_field_maps=False,
            elements_to_dump=(),
        )

    def run_with_this(
        self,
        accelerator_id: str,
        set_of_cavity_settings: SetOfCavitySettings,
        elts: ListOfElements,
        **kwargs,
    ) -> SimulationOutput:
        """Use solver on ``elts``, including the ``set_of_cavity_settings``.

        Parameters
        ----------
        accelerator_id :
            Associated :attr:`.Accelerator.id`. Looks like:
            ``0000001_Solution``.
        set_of_cavity_settings :
            The cavity settings to use for every cavity in ``elts``. They can
            be given by an optimization algorithm, or taken from cavity
            objects.
        elts :
            List of elements in which the beam must be propagated.

        Returns
        -------
            Holds energy, phase, transfer matrices (among others) packed into a
            single object.

        """
        single_elts_results = []
        w_kin = elts.w_kin_in
        phi_abs = elts.phi_abs_in

        for elt in elts:
            cavity_settings = set_of_cavity_settings.get(elt)
            _store_entry_phase_in_settings(phi_abs, cavity_settings)
            # Patch
            if isinstance(elt, SuperposedFieldMap):
                _store_entry_phase_in_settings(phi_abs, elt.cavities_settings)

            func = elt.beam_calc_param[self.id].transf_mat_function_wrapper
            elt_results = func(w_kin=w_kin, cavity_settings=cavity_settings)

            if cavity_settings is not None:
                self._post_treat_cavity_settings(
                    cavity_settings, elt_results, elt.length_m
                )

            single_elts_results.append(elt_results)

            phi_abs += elt_results["phi_rel"][-1]
            w_kin = elt_results["w_kin"][-1]

        simulation_output = self.simulation_output_factory.create(
            accelerator_id=accelerator_id,
            elts=elts,
            single_elts_results=single_elts_results,
            set_of_cavity_settings=set_of_cavity_settings,
        )
        return simulation_output

    def init_solver_parameters(self, accelerator: Accelerator) -> None:
        """Create the number of steps, meshing, transfer functions for elts.

        The solver parameters are stored in the ``beam_calc_param`` attribute
        of |E|.

        Parameters
        ----------
        accelerator :
            Object which |LOE| must be initialized.

        """
        elts = accelerator.elts
        position = 0.0
        index = 0
        for elt in elts:
            if self.id in elt.beam_calc_param:
                logging.debug(
                    f"Solver already initialized for {elt = }. I will skip "
                    f"solver param initialisation {elts[0]} to {elts[-1]}"
                )
                return
            solver_param = self.beam_calc_parameters_factory.run(elt)
            elt.beam_calc_param[self.id] = solver_param
            assert isinstance(solver_param, ElementEnvelope1DParameters)
            position, index = solver_param.set_absolute_meshes(position, index)
        logging.debug(f"Initialized solver param for {elts[0]} to {elts[-1]}")
        return

    @property
    def is_a_multiparticle_simulation(self) -> bool:
        """Return False."""
        return False

    @property
    def is_a_3d_simulation(self) -> bool:
        """Return False."""
        return False

    def _post_treat_cavity_settings(
        self, cavity_settings: CavitySettings, results: dict, length_m: float
    ) -> None:
        """Compute synchronous phase, accelerating field and acceptances.

        Also store these quantities in ``cavity_settings``.

        .. todo::
           Integrate this to |CS|.

        """
        v_cav_mv, phi_s = self._phi_s_func(**results)
        cavity_settings.v_cav_mv = v_cav_mv
        cavity_settings.phi_s = phi_s

        acceptance_phi, acceptance_energy = compute_acceptances(
            phi_s,
            cavity_settings.freq_cavity_mhz,
            getattr(cavity_settings, "w_kin", None),
            v_cav_mv,
            length_m,
            self._beam_kwargs,
        )
        cavity_settings.acceptance_phi = acceptance_phi
        cavity_settings.acceptance_energy = acceptance_energy


def _store_entry_phase_in_settings(
    phi_bunch_abs: float,
    cavity_settings: CavitySettings | Collection[CavitySettings] | None,
) -> None:
    """Set entry phase."""
    if cavity_settings is None:
        return
    if isinstance(cavity_settings, CavitySettings):
        cavity_settings = (cavity_settings,)

    for settings in cavity_settings:
        settings.phi_bunch = phi_bunch_abs
    return
