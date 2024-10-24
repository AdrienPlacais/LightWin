"""Define class to compute beam propagation in envelope, 1D, no space-charge.

This solver is fast, but should not be used at low energies.

"""

import logging
from collections.abc import Callable, Collection, Sequence
from pathlib import Path
from typing import Any, Literal

from lightwin.beam_calculation.beam_calculator import BeamCalculator
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
from lightwin.core.elements.element import Element
from lightwin.core.elements.field_maps.cavity_settings import CavitySettings
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.elements.field_maps.superposed_field_map import (
    SuperposedFieldMap,
)
from lightwin.core.em_fields.rf_field import RfField
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.failures.set_of_cavity_settings import SetOfCavitySettings
from lightwin.util.synchronous_phases import SYNCHRONOUS_PHASE_FUNCTIONS


class Envelope1D(BeamCalculator):
    """The fastest beam calculator, adapted to high energies."""

    def __init__(
        self,
        *,
        flag_phi_abs: bool,
        flag_cython: bool,
        n_steps_per_cell: int,
        method: ENVELOPE1D_METHODS_T,
        out_folder: Path | str,
        default_field_map_folder: Path | str,
        phi_s_definition: Literal["historical"] = "historical",
        **kwargs,
    ) -> None:
        """Set the proper motion integration function, according to inputs."""
        self.n_steps_per_cell = n_steps_per_cell
        self.method: ENVELOPE1D_METHODS_T = method
        super().__init__(
            flag_phi_abs=flag_phi_abs,
            out_folder=out_folder,
            default_field_map_folder=default_field_map_folder,
            flag_cython=flag_cython,
            **kwargs,
        )

        self._phi_s_definition = phi_s_definition
        self._phi_s_func = SYNCHRONOUS_PHASE_FUNCTIONS[self._phi_s_definition]

    def _set_up_specific_factories(self) -> None:
        """Set up the factories specific to the :class:`.BeamCalculator`.

        This method is called in the :meth:`.BeamCalculator.__init__`, hence it
        appears only in the base :class:`.BeamCalculator`.

        """
        self.simulation_output_factory = SimulationOutputFactoryEnvelope1D(
            _is_3d=self.is_a_3d_simulation,
            _is_multipart=self.is_a_multiparticle_simulation,
            _solver_id=self.id,
            _beam_kwargs=self._beam_kwargs,
            out_folder=self.out_folder,
        )
        self.beam_calc_parameters_factory: (  # type: ignore
            ElementEnvelope1DParametersFactory
        ) = ElementEnvelope1DParametersFactory(
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
        """Compute beam propagation in 1D, envelope calculation.

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
        """Use solver on ``elts``, including the ``set_of_cavity_settings``.

        Parameters
        ----------
        set_of_cavity_settings : SetOfCavitySettings | None
            The new cavity settings to try. If it is None, then the cavity
            settings are taken from the :class:`.FieldMap` objects.
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
            rf_field_kwargs, cavity_settings = self._transfer_matrix_kwargs(
                elt, set_of_cavity_settings, phi_abs, w_kin
            )
            # Technically: if we made a phi_s fit, following lines are useless
            # elt_results already calculated
            # v_cav, phi_s already calculated

            func = elt.beam_calc_param[self.id].transf_mat_function_wrapper
            elt_results = func(w_kin, **rf_field_kwargs)

            if cavity_settings is not None:
                v_cav_mv, phi_s = self._compute_cavity_parameters(elt_results)
                cavity_settings.v_cav_mv = v_cav_mv
                # not useful if sync phase is already set (reference phi_s)
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
        """Run :class:`Envelope1D` with optimized cavity settings.

        With this solver, we have nothing to do, nothing to update. Just call
        the regular :meth:`run_with_this` method.

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

        The solver parameters are stored in the ``beam_calc_param`` attribute
        of :class:`.Element`.

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
        """Return False."""
        return False

    def _post_treat_cavity_settings(
        self, cavity_settings: CavitySettings, results: dict
    ) -> None:
        """Compute synchronous phase and accelerating field."""
        v_cav_mv, phi_s = self._compute_cavity_parameters(results)
        cavity_settings.v_cav_mv = v_cav_mv
        cavity_settings.phi_s = phi_s

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

    def _transfer_matrix_kwargs(
        self,
        element: Element,
        set_of_cavity_settings: SetOfCavitySettings,
        phi_bunch_abs: float,
        w_kin_in: float,
    ) -> tuple[dict[str, Any], CavitySettings | None]:
        """Set the keyword arguments of the transfer matrix function."""
        if element not in set_of_cavity_settings:
            return {}, None
        assert isinstance(element, FieldMap)

        cavity_settings = set_of_cavity_settings[element]
        rf_field = element.rf_field
        _set_entry_phase(phi_bunch_abs, cavity_settings)

        if isinstance(element, SuperposedFieldMap):
            assert isinstance(cavities_settings := cavity_settings, list)
            assert isinstance(rf_fields := rf_field, list)
            kwargs = _superposed_field_map_kwargs(
                cavities_settings=cavities_settings, rf_fields=rf_fields
            )
            if not kwargs:
                return {}, None
            _add_cavities_phases(self.id, w_kin_in, cavities_settings, kwargs)
            return kwargs, None

        if isinstance(element, FieldMap):
            kwargs = _field_map_kwargs(cavity_settings, rf_field)
            if not kwargs:
                return {}, cavity_settings
            _add_cavity_phase(self.id, w_kin_in, cavity_settings, kwargs)
            return kwargs, cavity_settings


def _field_map_kwargs(
    cavity_settings: CavitySettings, rf_field: RfField
) -> dict[str, Callable | int | float]:
    """Format the cavity settings for the current solver transfer matrix func.

    .. todo::
        Seems a bit lengthy for what it does, no?

    """
    # alt implementation?
    # if cavity_settings is None:
    #     cavity_settings = field_map.cavity_settings

    if cavity_settings.status == "failed":
        return {}

    rf_parameters_as_dict = {
        "bunch_to_rf": cavity_settings.bunch_phase_to_rf_phase,
        "e_spat": rf_field.e_spat,
        "k_e": cavity_settings.k_e,
        "n_cell": rf_field.n_cell,
        "omega0_rf": cavity_settings.omega0_rf,
        "section_idx": rf_field.section_idx,
    }
    return rf_parameters_as_dict


def _add_cavity_phase(
    solver_id: str,
    w_kin_in: float,
    cavity_settings: CavitySettings,
    rf_parameters_as_dict: dict[str, Callable | int | float],
) -> None:
    r"""Set reference phase and function to compute :math:`\phi_s`."""
    if cavity_settings.reference == "phi_s":
        cavity_settings.set_cavity_parameters_arguments(
            solver_id, w_kin_in, **rf_parameters_as_dict
        )
        phi_0_rel = cavity_settings.phi_0_rel
        assert phi_0_rel is not None
        rf_parameters_as_dict["phi_0_rel"] = phi_0_rel
        return

    phi_0_rel = cavity_settings.phi_0_rel
    assert phi_0_rel is not None
    rf_parameters_as_dict["phi_0_rel"] = phi_0_rel
    cavity_settings.set_cavity_parameters_arguments(
        solver_id, w_kin_in, **rf_parameters_as_dict
    )


def _superposed_field_map_kwargs(
    cavities_settings: Sequence[CavitySettings], rf_fields: Sequence[RfField]
) -> dict[str, list[Callable] | int | float | list[float]]:
    """Format cavity settings for superposed field map object."""
    rf_parameters_as_dict = {
        "bunch_to_rf": cavities_settings[0].bunch_phase_to_rf_phase,
        "e_spats": [rf_field.e_spat for rf_field in rf_fields],
        "k_es": [setting.k_e for setting in cavities_settings],
        "n_cell": max([rf_field.n_cell for rf_field in rf_fields]),
        "omega0_rf": cavities_settings[0].omega0_rf,
        "phi_0_rels": [],
        "section_idx": None,  # Cython only (not implemented)
    }
    return rf_parameters_as_dict


def _add_cavities_phases(
    solver_id: str,
    w_kin_in: float,
    cavities_settings: Collection[CavitySettings],
    rf_parameters_as_dict: dict[
        str, list[Callable] | int | float | list[float]
    ],
) -> None:
    r"""Set reference phase and function to compute :math:`\phi_s`."""
    assert isinstance(rf_parameters_as_dict["phi_0_rels"], list)
    for cavity_settings in cavities_settings:
        if cavity_settings.reference == "phi_s":
            cavity_settings.set_cavity_parameters_arguments(
                solver_id, w_kin_in, **rf_parameters_as_dict
            )
            phi_0_rel = cavity_settings.phi_0_rel
            assert phi_0_rel is not None
            rf_parameters_as_dict["phi_0_rels"].append(phi_0_rel)
            return

        phi_0_rel = cavity_settings.phi_0_rel
        assert phi_0_rel is not None
        rf_parameters_as_dict["phi_0_rels"].append(phi_0_rel)
        cavity_settings.set_cavity_parameters_arguments(
            solver_id, w_kin_in, **rf_parameters_as_dict
        )


def _set_entry_phase(
    phi_bunch_abs: float,
    cavity_settings: CavitySettings | Collection[CavitySettings],
) -> None:
    """Set entry phase."""
    if isinstance(cavity_settings, CavitySettings):
        cavity_settings.phi_bunch = phi_bunch_abs
        return

    for settings in cavity_settings:
        _set_entry_phase(phi_bunch_abs, settings)
    return
