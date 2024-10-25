"""Define :class:`Envelope3D`, an envelope solver."""

import logging
from collections.abc import Collection
from pathlib import Path
from typing import Literal

from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.beam_calculation.envelope_3d.beam_parameters_factory import (
    BeamParametersFactoryEnvelope3D,
)
from lightwin.beam_calculation.envelope_3d.element_envelope3d_parameters_factory import (
    ElementEnvelope3DParametersFactory,
)
from lightwin.beam_calculation.envelope_3d.simulation_output_factory import (
    SimulationOutputFactoryEnvelope3D,
)
from lightwin.beam_calculation.envelope_3d.transfer_matrix_factory import (
    TransferMatrixFactoryEnvelope3D,
)
from lightwin.beam_calculation.envelope_3d.util import ENVELOPE3D_METHODS_T
from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.core.elements.field_maps.cavity_settings import CavitySettings
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.failures.set_of_cavity_settings import SetOfCavitySettings
from lightwin.util.synchronous_phases import (
    PHI_S_MODELS,
    SYNCHRONOUS_PHASE_FUNCTIONS,
)


class Envelope3D(BeamCalculator):
    """A 3D envelope solver."""

    def __init__(
        self,
        *,
        flag_phi_abs: bool,
        n_steps_per_cell: int,
        out_folder: Path | str,
        default_field_map_folder: Path | str,
        flag_cython: bool = False,
        method: ENVELOPE3D_METHODS_T = "RK4",
        phi_s_definition: PHI_S_MODELS = "historical",
        **kwargs,
    ) -> None:
        """Set the proper motion integration function, according to inputs."""
        self.n_steps_per_cell = n_steps_per_cell
        self.method = method
        super().__init__(
            flag_phi_abs=flag_phi_abs,
            out_folder=out_folder,
            default_field_map_folder=default_field_map_folder,
            flag_cython=flag_cython,
            **kwargs,
        )

        self._phi_s_definition = phi_s_definition
        self._phi_s_func = SYNCHRONOUS_PHASE_FUNCTIONS[self._phi_s_definition]

        self.beam_parameters_factory = BeamParametersFactoryEnvelope3D(
            self.is_a_3d_simulation,
            self.is_a_multiparticle_simulation,
            beam_kwargs=self._beam_kwargs,
        )
        self.transfer_matrix_factory = TransferMatrixFactoryEnvelope3D(
            self.is_a_3d_simulation
        )

        import lightwin.beam_calculation.envelope_3d.transfer_matrices_p as transf_mat

        self.transf_mat_module = transf_mat

    def _set_up_specific_factories(self) -> None:
        """Set up the factories specific to the :class:`.BeamCalculator`.

        This method is called in the :meth:`.BeamCalculator.__init__`, hence it
        appears only in the base :class:`.BeamCalculator`.

        """
        self.simulation_output_factory = SimulationOutputFactoryEnvelope3D(
            _is_3d=self.is_a_3d_simulation,
            _is_multipart=self.is_a_multiparticle_simulation,
            _solver_id=self.id,
            _beam_kwargs=self._beam_kwargs,
            out_folder=self.out_folder,
        )
        self.beam_calc_parameters_factory = ElementEnvelope3DParametersFactory(
            method=self.method,
            n_steps_per_cell=self.n_steps_per_cell,
            solver_id=self.id,
            beam_kwargs=self._beam_kwargs,
            flag_cython=self.flag_cython,
        )

    def run(
        self,
        elts: ListOfElements,
        update_reference_phase: bool = False,
        **kwargs,
    ) -> SimulationOutput:
        """Compute beam propagation in 3D, envelope calculation.

        Parameters
        ----------
        elts : ListOfElements
            List of elements in which the beam must be propagated.
        update_reference_phase : bool, optional
            To change the reference phase of cavities when it is different from
            the one asked in the ``.toml``. To use after the first calculation,
            if ``BeamCalculator.flag_phi_abs`` does not correspond to
            ``CavitySettings.reference``. The default is False.

        Returns
        -------
        simulation_output : SimulationOutput
            Holds energy, phase, transfer matrices (among others) packed into a
            single object.

        """
        return super().run(elts, update_reference_phase, **kwargs)

    def run_with_this(
        self,
        set_of_cavity_settings: SetOfCavitySettings | None,
        elts: ListOfElements,
        use_a_copy_for_nominal_settings: bool = True,
    ) -> SimulationOutput:
        """Compute beam propagation with non-nominal settings.

        Parameters
        ----------
        set_of_cavity_settings : SetOfCavitySettings | None
            The new cavity settings to try. If it is None, then the cavity
            settings are taken from the FieldMap objects.
        elts : ListOfElements
            List of elements in which the beam must be propagated.
        use_a_copy_for_nominal_settings : bool, optional
            To copy the nominal :class:`.CavitySettings` and avoid altering
            their nominal counterpart. Set it to True during optimisation, to
            False when you want to keep the current settings. The default is
            True.

        Returns
        -------
        simulation_output : SimulationOutput
            Holds energy, phase, transfer matrices (among others) packed into a
            single object.

        """
        single_elts_results = []
        w_kin = elts.w_kin_in
        phi_abs = elts.phi_abs_in

        set_of_cavity_settings = SetOfCavitySettings.from_incomplete_set(
            set_of_cavity_settings,
            elts.l_cav,
            use_a_copy_for_nominal_settings=use_a_copy_for_nominal_settings,
        )

        for elt in elts:
            cavity_settings = set_of_cavity_settings.get(elt, None)
            _store_entry_phase_in_settings(phi_abs, cavity_settings)

            func = elt.beam_calc_param[self.id].transf_mat_function_wrapper
            elt_results = func(w_kin=w_kin, cavity_settings=cavity_settings)

            if cavity_settings is not None:
                v_cav_mv, phi_s = self._compute_cavity_parameters(elt_results)
                cavity_settings.v_cav_mv = v_cav_mv
                cavity_settings.phi_s = phi_s

            single_elts_results.append(elt_results)

            phi_abs += elt_results["phi_rel"][-1]
            w_kin = elt_results["w_kin"][-1]

        simulation_output = self._generate_simulation_output(
            elts, single_elts_results, set_of_cavity_settings
        )
        return simulation_output

    def post_optimisation_run_with_this(
        self,
        optimized_cavity_settings: SetOfCavitySettings,
        full_elts: ListOfElements,
        **specific_kwargs,
    ) -> SimulationOutput:
        """
        Run Envelope3D with optimized cavity settings.

        With this solver, we have nothing to do, nothing to update. Just call
        the regular `run_with_this` method.

        """
        simulation_output = self.run_with_this(
            optimized_cavity_settings,
            full_elts,
            use_a_copy_for_nominal_settings=False,
            **specific_kwargs,
        )
        return simulation_output

    def init_solver_parameters(self, accelerator: Accelerator) -> None:
        """Create the number of steps, meshing, transfer functions for elts.

        The solver parameters are stored in the :class:`.Element`'s
        ``beam_calc_param``.

        Parameters
        ----------
        accelerator : Accelerator
            Object which :class:`.ListOfElements` must be initialized.

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
            position, index = solver_param.set_absolute_meshes(position, index)
        logging.debug(f"Initialized solver param for {elts[0]} to {elts[-1]}")
        return

    @property
    def is_a_multiparticle_simulation(self) -> bool:
        """Return False."""
        return False

    @property
    def is_a_3d_simulation(self) -> bool:
        """Return True."""
        return True

    def _compute_cavity_parameters(self, results: dict) -> tuple[float, float]:
        """Compute the cavity parameters by calling ``_phi_s_func``.

        Parameters
        ----------
        results
            The dictionary of results as returned by the transfer matrix
            function wrapper.

        Returns
        -------
        tuple[float, float]
            Accelerating voltage in MV and synchronous phase in radians. If the
            cavity is failed, two ``np.nan`` are returned.

        """
        v_cav_mv, phi_s = self._phi_s_func(**results)
        return v_cav_mv, phi_s


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
