"""Define a class to hold solver parameters for :class:`.Envelope1D`.

This module holds :class:`ElementEnvelope1DParameters`, that inherits
from the Abstract Base Class :class:`.ElementBeamCalculatorParameters`.
It holds the transfer matrix function that is used, according to the solver
(Runge-Kutta or leapfrog) and their version (Python or Cython), as well as the
meshing in accelerating elements.

The :class:`.Element` objects with a transfer matrix are ``DRIFT``,
``SOLENOID``, ``QUAD``, ``FIELD_MAP``, ``BEND``.

"""

import math
from collections.abc import Collection
from typing import Any, Callable, Literal

import numpy as np

import lightwin.util.converters as convert
from lightwin.beam_calculation.envelope_1d import transfer_matrices
from lightwin.beam_calculation.envelope_1d.util import ENVELOPE1D_METHODS_T
from lightwin.beam_calculation.parameters.element_parameters import (
    ElementBeamCalculatorParameters,
)
from lightwin.core.elements.bend import Bend
from lightwin.core.elements.element import Element
from lightwin.core.elements.field_maps.cavity_settings import CavitySettings
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.elements.field_maps.superposed_field_map import (
    SuperposedFieldMap,
)
from lightwin.core.em_fields.types import (
    FieldFuncComplexTimedComponent,
    FieldFuncTimedComponent,
)
from lightwin.util.synchronous_phases import (
    PHI_S_MODELS,
    SYNCHRONOUS_PHASE_FUNCTIONS,
)


class ElementEnvelope1DParameters(ElementBeamCalculatorParameters):
    """Hold the parameters to compute beam propagation in an Element.

    ``has`` and ``get`` method inherited from
    :class:`.ElementBeamCalculatorParameters` parent class.

    """

    def __init__(
        self,
        length_m: float,
        n_steps: int,
        beam_kwargs: dict[str, Any],
        transf_mat_function: Callable | None = None,
        **kwargs: str | int,
    ) -> None:
        """Set the actually useful parameters."""
        if transf_mat_function is None:
            transf_mat_function = self._proper_transfer_matrix_func("Drift")
        self.transf_mat_function = transf_mat_function
        self.n_steps = n_steps
        self._beam_kwargs = beam_kwargs
        self.d_z = length_m / self.n_steps
        self.rel_mesh = np.linspace(0.0, length_m, self.n_steps + 1)

        self.s_in: int
        self.s_out: int
        self.abs_mesh: np.ndarray

    def set_absolute_meshes(
        self, pos_in: float, s_in: int
    ) -> tuple[float, int]:
        """Set the absolute indexes and arrays, depending on previous elem."""
        self.abs_mesh = self.rel_mesh + pos_in

        self.s_in = s_in
        self.s_out = self.s_in + self.n_steps

        return self.abs_mesh[-1], self.s_out

    def re_set_for_broken_cavity(self) -> None:
        """Change solver parameters for efficiency purposes."""
        raise NotImplementedError(
            "Calling this method for a non-field map is incorrect."
        )

    def transfer_matrix_kw(self, *args, **kwargs) -> dict[str, Any]:
        """Give the element parameters necessary to compute transfer matrix."""
        return self._beam_kwargs | {
            "delta_s": self.d_z,
            "n_steps": self.n_steps,
        }

    def transf_mat_function_wrapper(
        self,
        w_kin: float,
        phi_0_rel: float | None = None,
        cavity_settings: Any = None,
        **kwargs,
    ) -> dict:
        """Calculate beam propagation in the :class:`.Element`.

        kwargs can be cavity_settings rf_field

        """
        gamma_in = convert.energy(w_kin, "kin to gamma", **self._beam_kwargs)
        tm_kwargs = self.transfer_matrix_kw(
            w_kin=w_kin,
            phi_0_rel=phi_0_rel,
            cavity_settings=cavity_settings,
            **kwargs,
        )
        r_zz, gamma_phi, itg_field = self.transf_mat_function(
            gamma_in=gamma_in, **tm_kwargs
        )

        results = self._transfer_matrix_results_to_dict(
            r_zz, gamma_phi, itg_field
        )
        return results

    def _transfer_matrix_results_to_dict(
        self,
        r_zz: np.ndarray,
        gamma_phi: np.ndarray,
        integrated_field: float | None,
    ) -> dict:
        """Convert the results given by the transf_mat function to dict."""
        if integrated_field is not None:
            raise ValueError("Expected None integrated field.")
        w_kin = convert.energy(
            gamma_phi[:, 0], "gamma to kin", **self._beam_kwargs
        )
        results = {
            "r_zz": r_zz,
            "cav_params": None,
            "w_kin": w_kin,
            "phi_rel": gamma_phi[:, 1],
            "integrated_field": integrated_field,
        }
        return results

    def _proper_transfer_matrix_func(
        self,
        element_nature: str,
        method: ENVELOPE1D_METHODS_T | None = None,
    ) -> Callable:
        """Get the proper transfer matrix function."""
        match method, element_nature:
            case "RK4", "SuperposedFieldMap":
                return transfer_matrices.z_superposed_field_maps_rk4
            case "leapfrog", "SuperposedFieldMap":
                raise NotImplementedError(
                    "leapfrog not implemented for superposed field maps"
                )
            case "RK4", "FieldMap":
                return transfer_matrices.z_field_map_rk4
            case "leapfrog", "FieldMap":
                return transfer_matrices.z_field_map_leapfrog
            case _, "Bend":
                return transfer_matrices.z_bend
            case _:
                return transfer_matrices.z_drift


class DriftEnvelope1DParameters(ElementEnvelope1DParameters):
    """Hold the properties to compute transfer matrix of a :class:`.Drift`.

    As this is 1D, it is also used for :class:`.Solenoid`, :class:`.Quad`,
    broken :class:`.FieldMap`.

    """

    def __init__(
        self,
        elt: Element,
        beam_kwargs: dict[str, Any],
        n_steps: int = 1,
        **kwargs: str | int,
    ) -> None:
        """Create the specific parameters for a drift."""
        return super().__init__(
            length_m=elt.length_m,
            n_steps=n_steps,
            beam_kwargs=beam_kwargs,
            transf_mat_function=None,
            **kwargs,
        )


class FieldMapEnvelope1DParameters(ElementEnvelope1DParameters):
    """Hold the properties to compute transfer matrix of a :class:`.FieldMap`.

    Non-accelerating cavities will use :class:`.DriftEnvelope1DParameters`
    instead.

    """

    def __init__(
        self,
        elt: FieldMap,
        method: ENVELOPE1D_METHODS_T,
        n_steps_per_cell: int,
        solver_id: str,
        beam_kwargs: dict[str, Any],
        phi_s_model: PHI_S_MODELS = "historical",
        **kwargs: str | int,
    ) -> None:
        """Create the specific parameters for a field map."""
        transf_mat_function = self._proper_transfer_matrix_func(
            "FieldMap", method
        )
        self.compute_cavity_parameters = SYNCHRONOUS_PHASE_FUNCTIONS[
            phi_s_model
        ]

        self.solver_id = solver_id
        n_cell = elt.cavity_settings.field.n_cell
        self._rf_to_bunch = elt.cavity_settings.rf_phase_to_bunch_phase
        n_steps = n_cell * n_steps_per_cell
        super().__init__(
            elt.length_m,
            n_steps,
            beam_kwargs=beam_kwargs,
            transf_mat_function=transf_mat_function,
            **kwargs,
        )
        self.field_map_file_name = str(elt.filename)
        elt.cavity_settings.set_cavity_parameters_methods(
            self.solver_id,
            self.transf_mat_function_wrapper,
            self.compute_cavity_parameters,
        )

    def transfer_matrix_kw(
        self,
        w_kin: float,
        cavity_settings: CavitySettings,
        *args,
        phi_0_rel: float | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        r"""Give the element parameters necessary to compute transfer matrix.

        Parameters
        ----------
        w_kin : float
            Kinetic energy at the entrance of cavity in :unit:`MeV`.
        cavity_settings : CavitySettings
            Object holding the cavity parameters that can be changed.
        phi_0_rel : float | None
            Relative entry phase of the cavity. When provided, it means that we
            are trying to find the :math:`\phi_{0,\,\mathrm{rel}}` matching a
            given :math:`\phi_s`. The default is None.

        Returns
        -------
        dict[str, Any]
            Keyword arguments that will be passed to the 1D transfer matrix
            function defined in :mod:`.envelope_1d.transfer_matrices`.

        """
        geometry_kwargs = {
            "d_z": self.d_z,
            "n_steps": self.n_steps,
        }

        field = cavity_settings.field
        rf_kwargs: dict[str, float | FieldFuncComplexTimedComponent]
        match cavity_settings.reference, phi_0_rel:
            # Prepare the phi_s fit
            case "phi_s", None:
                rf_kwargs = {
                    "omega0_rf": cavity_settings.omega0_rf,
                }
                cavity_settings.set_cavity_parameters_arguments(
                    self.solver_id,
                    w_kin,
                    **rf_kwargs,  # Note that phi_0_rel is not set
                )
                # phi_0_rel will be set when trying to access
                # CavitySettings.phi_0_rel (this is the case #2)
                phi_0_rel = _get_phi_0_rel(cavity_settings)
                funcs = field.partial_e_z(cavity_settings.k_e, phi_0_rel)
                rf_kwargs["complex_e_func"], rf_kwargs["real_e_func"] = funcs

            # Currently looking for the phi_0_rel matching phi_s
            case "phi_s", _:
                funcs = field.partial_e_z(cavity_settings.k_e, phi_0_rel)
                rf_kwargs = {
                    "omega0_rf": cavity_settings.omega0_rf,
                    "complex_e_func": funcs[0],
                    "real_e_func": funcs[1],
                }

            # Normal run
            case _, None:
                phi_0_rel = _get_phi_0_rel(cavity_settings)
                funcs = field.partial_e_z(cavity_settings.k_e, phi_0_rel)
                rf_kwargs = {
                    "omega0_rf": cavity_settings.omega0_rf,
                    "complex_e_func": funcs[0],
                    "real_e_func": funcs[1],
                }
                cavity_settings.set_cavity_parameters_arguments(
                    self.solver_id, w_kin, **rf_kwargs
                )
            case _, _:
                raise ValueError
        return self._beam_kwargs | rf_kwargs | geometry_kwargs

    def _transfer_matrix_results_to_dict(
        self,
        r_zz: np.ndarray,
        gamma_phi: np.ndarray,
        integrated_field: float | None,
    ) -> dict:
        """Convert the results given by the transf_mat function to a dict.

        Overrides the default method defined in the ABC.

        """
        if integrated_field is None:
            raise ValueError("Expected non-None integrated field.")
        w_kin = convert.energy(
            gamma_phi[:, 0], "gamma to kin", **self._beam_kwargs
        )
        gamma_phi[:, 1] = self._rf_to_bunch(gamma_phi[:, 1])
        cav_params = self.compute_cavity_parameters(integrated_field)
        results = {
            "r_zz": r_zz,
            "cav_params": cav_params,
            "w_kin": w_kin,
            "phi_rel": gamma_phi[:, 1],
            "integrated_field": integrated_field,
        }
        return results

    def re_set_for_broken_cavity(self) -> Callable:
        """Make beam calculator call Drift func instead of FieldMap."""
        self.transf_mat_function = self._proper_transfer_matrix_func("Drift")
        self._transfer_matrix_results_to_dict = (
            self._broken_transfer_matrix_results_to_dict
        )
        self.transfer_matrix_kw = self._broken_transfer_matrix_kw
        return self.transf_mat_function

    def _broken_transfer_matrix_results_to_dict(
        self,
        r_zz: np.ndarray,
        gamma_phi: np.ndarray,
        integrated_field: float | None,
    ) -> dict:
        """Convert the results given by the transf_mat function to a dict."""
        assert integrated_field is None
        w_kin = convert.energy(
            gamma_phi[:, 0], "gamma to kin", **self._beam_kwargs
        )
        cav_params = self.compute_cavity_parameters(np.nan)
        results = {
            "r_zz": r_zz,
            "cav_params": cav_params,
            "w_kin": w_kin,
            "phi_rel": gamma_phi[:, 1],
            "integrated_field": integrated_field,
        }
        return results

    def _broken_transfer_matrix_kw(self, *args, **kwargs) -> dict[str, Any]:
        """Give the element parameters necessary to compute transfer matrix."""
        return self._beam_kwargs | {
            "delta_s": self.d_z,
            "n_steps": self.n_steps,
        }


def _get_phi_0_rel(cavity_settings: CavitySettings) -> float:
    """Get the phase from the object."""
    phi_0_rel = cavity_settings.phi_0_rel
    assert phi_0_rel is not None
    return phi_0_rel


class SuperposedFieldMapEnvelope1DParameters(ElementEnvelope1DParameters):
    """
    Hold properties to compute transfer matrix of :class:`.SuperposedFieldMap`.

    """

    def __init__(
        self,
        elt: SuperposedFieldMap,
        method: Literal["RK4"],
        n_steps_per_cell: int,
        solver_id: str,
        beam_kwargs: dict[str, Any],
        phi_s_model: PHI_S_MODELS = "historical",
        **kwargs: str | int,
    ) -> None:
        """Create the specific parameters for a field map."""
        transf_mat_function = self._proper_transfer_matrix_func(
            "SuperposedFieldMap", method
        )
        self.compute_cavity_parameters = SYNCHRONOUS_PHASE_FUNCTIONS[
            phi_s_model
        ]

        self.solver_id = solver_id
        field_maps = elt.field_maps

        self._rf_to_bunch = field_maps[
            0
        ].cavity_settings.rf_phase_to_bunch_phase
        n_cell = sum((fm.cavity_settings.field.n_cell for fm in field_maps))
        n_steps = n_cell * n_steps_per_cell

        self.field_maps = field_maps
        self.cavity_settings = [fm.cavity_settings for fm in field_maps]
        self.fields = [setting.field for setting in self.cavity_settings]
        self.field = elt.field

        super().__init__(
            elt.length_m,
            n_steps,
            beam_kwargs=beam_kwargs,
            transf_mat_function=transf_mat_function,
            **kwargs,
        )

        for fm in field_maps:
            fm.cavity_settings.set_cavity_parameters_methods(
                self.solver_id,
                self.transf_mat_function_wrapper,
                self.compute_cavity_parameters,
            )

    def transfer_matrix_kw(
        self, w_kin: float, *args, **kwargs
    ) -> dict[str, Any]:
        """Give the element parameters necessary to compute transfer matrix."""
        geometry_kwargs = {
            "d_z": self.d_z,
            "n_steps": self.n_steps,
        }
        complex_e_func, real_e_func = self._set_field_functions()
        rf_kwargs = {
            "omega0_rf": self.cavity_settings[0].omega0_rf,
            "complex_e_func": complex_e_func,
            "real_e_func": real_e_func,
        }

        # What will happen when 1st cavity accelerates the beam, hence the
        # given w_kin is bad? Problem for synchronous phases only
        for cav in self.cavity_settings:
            cav.set_cavity_parameters_arguments(
                self.solver_id, w_kin, **rf_kwargs
            )
        return self._beam_kwargs | rf_kwargs | geometry_kwargs

    def _set_field_functions(
        self,
    ) -> tuple[FieldFuncComplexTimedComponent, FieldFuncTimedComponent]:
        """Set the functions to compute electric fields."""
        k_es = [setting.k_e for setting in self.cavity_settings]
        phi_0_rels = [setting.phi_0_rel for setting in self.cavity_settings]
        if None in phi_0_rels:
            raise RuntimeError(
                "A phi_0_rel was not set in the sublist of field maps"
            )
        return self.field.partial_e_z(k_es, phi_0_rels)

    def _transfer_matrix_results_to_dict(
        self,
        r_zz: np.ndarray,
        gamma_phi: np.ndarray,
        integrated_field: float | None,
    ) -> dict:
        """Convert the results given by the transf_mat function to a dict.

        Overrides the default method defined in the ABC.

        """
        assert integrated_field is not None
        w_kin = convert.energy(
            gamma_phi[:, 0], "gamma to kin", **self._beam_kwargs
        )
        gamma_phi[:, 1] = self._rf_to_bunch(gamma_phi[:, 1])
        cav_params = self.compute_cavity_parameters(integrated_field)
        results = {
            "r_zz": r_zz,
            "cav_params": cav_params,
            "w_kin": w_kin,
            "phi_rel": gamma_phi[:, 1],
            "integrated_field": integrated_field,
        }
        return results

    def re_set_for_broken_cavity(self) -> None:
        """Make beam calculator call Drift func instead of FieldMap."""
        raise NotImplementedError(
            "superposed field maps should not be modified during execution for"
            " now"
        )


class BendEnvelope1DParameters(ElementEnvelope1DParameters):
    """Hold the specific parameters to compute :class:`.Bend` transfer matrix.

    In particular, we define ``factor_1``, ``factor_2`` and ``factor_3`` to
    speed-up calculations.

    """

    def __init__(
        self,
        elt: Bend,
        beam_kwargs: dict[str, Any],
        n_steps: int = 1,
        **kwargs: str | int,
    ) -> None:
        """Instantiate object and pre-compute some parameters for speed.

        Parameters
        ----------
        transf_mat_module : types.ModuleType
            Module where the transfer matrix function is defined.
        elt : Bend
            ``BEND`` element.
        beam_kwargs : dict[str, Any]
            Configuration dict holding all initial beam properties.
        n_steps : int, optional
            Number of integration steps. The default is 1.

        """
        transf_mat_function = self._proper_transfer_matrix_func("Bend")

        super().__init__(
            elt.length_m,
            n_steps=n_steps,
            beam_kwargs=beam_kwargs,
            transf_mat_function=transf_mat_function,
            **kwargs,
        )

        factors = self._pre_compute_factors_for_transfer_matrix(
            elt.length_m,
            elt.h_squared,
            elt.k_x,
            elt.field_grad_index <= 1.0,
        )
        self.factor_1, self.factor_2, self.factor_3 = factors

    def _pre_compute_factors_for_transfer_matrix(
        self,
        length_m: float,
        h_squared: float,
        k_x: float,
        index_is_lower_than_unity: bool,
    ) -> tuple[float, float, float]:
        r"""
        Compute factors to speed up the transfer matrix calculation.

        ``factor_1`` is:

        .. math::
            \frac{-h^2\Delta s}{k_x^2}

        ``factor_2`` is:

        .. math::
            \frac{h^2 \sin{(k_x\Delta s)}}{k_x^3}

        if :math:`n \leq 1`. Else:

        .. math::
            \frac{h^2 \sinh{(k_x\Delta s)}}{k_x^3}

        ``factor_3`` is:

        .. math::
            \Delta s \left(1 - \frac{h^2}{k_x^2}\right)

        """
        factor_1 = -h_squared * length_m / k_x**2
        if index_is_lower_than_unity:
            factor_2 = h_squared * math.sin(k_x * length_m) / k_x**3
        else:
            factor_2 = h_squared * math.sinh(k_x * length_m) / k_x**3
        factor_3 = length_m * (1.0 - h_squared / k_x**2)
        assert isinstance(factor_1, float)
        assert isinstance(factor_2, float)
        assert isinstance(factor_3, float)
        return factor_1, factor_2, factor_3

    def transfer_matrix_kw(self, *args, **kwargs) -> dict[str, Any]:
        """Give the element parameters necessary to compute transfer matrix."""
        return self._beam_kwargs | {
            "delta_s": self.d_z,
            "factor_1": self.factor_1,
            "factor_2": self.factor_2,
            "factor_3": self.factor_3,
        }


class DummyEnvelope1DParameters(ElementEnvelope1DParameters):
    """Create dummy arguments for dummy element."""

    def __init__(
        self,
        elt: Element,
        beam_kwargs: dict[str, Any],
        n_steps: int = 1,
        **kwargs: str | int,
    ) -> None:
        """Create no specific parameters."""
        return super().__init__(
            length_m=elt.length_m,
            n_steps=n_steps,
            beam_kwargs=beam_kwargs,
            transf_mat_function=transfer_matrices.z_dummy,
            **kwargs,
        )


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
