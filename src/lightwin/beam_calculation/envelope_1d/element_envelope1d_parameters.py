"""Define a class to hold solver parameters for :class:`.Envelope1D`.

This module holds :class:`ElementEnvelope1DParameters`, that inherits
from the Abstract Base Class :class:`.ElementBeamCalculatorParameters`.
It holds the transfer matrix function that is used, according to the solver
(Runge-Kutta or leapfrog) and their version (Python or Cython), as well as the
meshing in accelerating elements.

The :class:`.Element` objects with a transfer matrix are listed in
:data:`.PARAMETERS_1D`.

"""

import math
from abc import abstractmethod
from types import ModuleType
from typing import Any, Callable, Literal

import numpy as np

import lightwin.util.converters as convert
from lightwin.beam_calculation.parameters.element_parameters import (
    ElementBeamCalculatorParameters,
)
from lightwin.constants import NEW
from lightwin.core.elements.bend import Bend
from lightwin.core.elements.element import Element
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.elements.field_maps.superposed_field_map import (
    SuperposedFieldMap,
)
from lightwin.util.synchronous_phases import SYNCHRONOUS_PHASE_FUNCTIONS

FIELD_MAP_INTEGRATION_METHOD_TO_FUNC = {
    "RK4": lambda module: (
        module.z_field_map_rk4_new if NEW else module.z_field_map_rk4
    ),
    "leapfrog": lambda module: module.z_field_map_leapfrog,
}


SUPERPOSED_FIELD_MAP_INTEGRATION_METHOD_TO_FUNC = {
    "RK4": lambda module: module.z_superposed_field_maps_rk4,
}


class ElementEnvelope1DParameters(ElementBeamCalculatorParameters):
    """Hold the parameters to compute beam propagation in an Element.

    ``has`` and ``get`` method inherited from
    :class:`.ElementBeamCalculatorParameters` parent class.

    """

    def __init__(
        self,
        transf_mat_function: Callable,
        length_m: float,
        n_steps: int,
        beam_kwargs: dict[str, Any],
        **kwargs: str | int,
    ) -> None:
        """Set the actually useful parameters."""
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
        raise IOError("Calling this method for a non-field map is incorrect.")

    @abstractmethod
    def transfer_matrix_kw(self) -> dict[str, Any]:
        """Give all the arguments for the transfer matrix function."""
        return {}

    def transf_mat_function_wrapper(
        self, w_kin_in: float, **rf_field_kwargs
    ) -> dict:
        """Calculate beam propagation in the :class:`.Element`."""
        gamma_in = convert.energy(
            w_kin_in, "kin to gamma", **self._beam_kwargs
        )
        r_zz, gamma_phi, itg_field = self.transf_mat_function(
            gamma_in=gamma_in,
            **self.transfer_matrix_kw(),
            **rf_field_kwargs,
            **self._beam_kwargs,
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
        assert integrated_field is None
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

    def _transfer_matrix_results_to_dict_broken_field_map(
        self,
        r_zz: np.ndarray,
        gamma_phi: np.ndarray,
        itg_field: float | None,
    ) -> dict:
        """Convert the results given by the transf_mat function to dict.

        This method should override the default
        ``_transfer_matrix_results_to_dict`` when the element under study is a
        broken field map.

        """
        assert itg_field is None
        w_kin = convert.energy(
            gamma_phi[:, 0], "gamma to kin", **self._beam_kwargs
        )
        results = {
            "r_zz": r_zz,
            "cav_params": {"v_cav_mv": np.nan, "phi_s": np.nan},
            "w_kin": w_kin,
            "phi_rel": gamma_phi[:, 1],
        }
        return results


class DriftEnvelope1DParameters(ElementEnvelope1DParameters):
    """Hold the properties to compute transfer matrix of a :class:`.Drift`.

    As this is 1D, it is also used for :class:`.Solenoid`, :class:`.Quad`,
    broken :class:`.FieldMap`.

    """

    def __init__(
        self,
        transf_mat_module: ModuleType,
        elt: Element,
        beam_kwargs: dict[str, Any],
        n_steps: int = 1,
        **kwargs: str | int,
    ) -> None:
        """Create the specific parameters for a drift."""
        transf_mat_function = transf_mat_module.z_drift
        return super().__init__(
            transf_mat_function,
            length_m=elt.length_m,
            n_steps=n_steps,
            beam_kwargs=beam_kwargs,
            **kwargs,
        )

    def transfer_matrix_kw(self) -> dict[str, Any]:
        """Give the fixed args to compute transfer matrix."""
        return {"delta_s": self.d_z, "n_steps": self.n_steps}


class FieldMapEnvelope1DParameters(ElementEnvelope1DParameters):
    """Hold the properties to compute transfer matrix of a :class:`.FieldMap`.

    Non-accelerating cavities will use :class:`.DriftEnvelope1DParameters`
    instead.

    """

    def __init__(
        self,
        transf_mat_module: ModuleType,
        elt: FieldMap,
        method: Literal["leapfrog", "RK4"],
        n_steps_per_cell: int,
        solver_id: str,
        beam_kwargs: dict[str, Any],
        phi_s_model: str = "historical",
        **kwargs: str | int,
    ) -> None:
        """Create the specific parameters for a field map."""
        transf_mat_function = FIELD_MAP_INTEGRATION_METHOD_TO_FUNC[method](
            transf_mat_module
        )
        self.compute_cavity_parameters = SYNCHRONOUS_PHASE_FUNCTIONS[
            phi_s_model
        ]

        self.solver_id = solver_id
        self.n_cell = elt.rf_field.n_cell
        self._rf_to_bunch = elt.cavity_settings.rf_phase_to_bunch_phase
        n_steps = self.n_cell * n_steps_per_cell
        super().__init__(
            transf_mat_function,
            elt.length_m,
            n_steps,
            beam_kwargs=beam_kwargs,
            **kwargs,
        )
        self._transf_mat_module = transf_mat_module
        self.field_map_file_name = str(elt.field_map_file_name)
        elt.cavity_settings.set_cavity_parameters_methods(
            self.solver_id,
            self.transf_mat_function_wrapper,
            self.compute_cavity_parameters,
        )

    def transfer_matrix_kw(self) -> dict[str, Any]:
        """Give the fixed args to compute transfer matrix."""
        return {
            "d_z": self.d_z,
            "n_steps": self.n_steps,
            "filename": self.field_map_file_name,
        }

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

    def re_set_for_broken_cavity(self) -> Callable:
        """Make beam calculator call Drift func instead of FieldMap."""
        self.transf_mat_function = self._transf_mat_module.z_drift
        self.transfer_matrix_kw = lambda: {
            "delta_s": self.d_z,
            "n_steps": self.n_steps,
        }

        def _new_transfer_matrix_results_to_dict(
            r_zz: np.ndarray,
            gamma_phi: np.ndarray,
            integrated_field: float | None,
        ) -> dict:
            """Convert the results given by the transf_mat function to dict.

            Overrides the default method defined in the ABC.

            """
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

        self._transfer_matrix_results_to_dict = (
            _new_transfer_matrix_results_to_dict
        )
        return self.transf_mat_function


class SuperposedFieldMapEnvelope1DParameters(ElementEnvelope1DParameters):
    """
    Hold properties to compute transfer matrix of :class:`.SuperposedFieldMap`.

    """

    def __init__(
        self,
        transf_mat_module: ModuleType,
        superposed: SuperposedFieldMap,
        method: Literal["RK4"],
        n_steps_per_cell: int,
        solver_id: str,
        phi_s_model: str = "historical",
        **kwargs: str | int,
    ) -> None:
        """Create the specific parameters for a field map."""
        if method == "leapfrog":
            raise NotImplementedError(
                "SUPERPOSE_MAP not implemented in leapfrog for now."
            )
        try:
            transf_mat_function = (
                SUPERPOSED_FIELD_MAP_INTEGRATION_METHOD_TO_FUNC[method](
                    transf_mat_module
                )
            )
        except ImportError:
            raise NotImplementedError(
                "SUPERPOSE_MAP not implemented in Cython for now."
            )
        self.compute_cavity_parameters = SYNCHRONOUS_PHASE_FUNCTIONS[
            phi_s_model
        ]

        self.solver_id = solver_id
        self.n_cell = superposed.rf_field.n_cell
        self._rf_to_bunch = (
            superposed.cavities_settings.rf_phase_to_bunch_phase
        )
        n_steps = self.n_cell * n_steps_per_cell
        super().__init__(
            transf_mat_function, superposed.length_m, n_steps, **kwargs
        )
        self._transf_mat_module = transf_mat_module

        self.field_map_file_names = [
            str(name) for name in superposed.field_map_file_names
        ]
        for settings in superposed.field_maps_settings:
            settings.set_cavity_parameters_methods(
                self.solver_id,
                self.transf_mat_function_wrapper,
                self.compute_cavity_parameters,
            )

    def transfer_matrix_kw(self) -> dict[str, Any]:
        """Give the fixed args to compute transfer matrix."""
        return {"d_z": self.d_z, "n_steps": self.n_steps}

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

    def re_set_for_broken_cavity(self) -> Callable:
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
        transf_mat_module: ModuleType,
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
        transf_mat_function = transf_mat_module.z_bend

        super().__init__(
            transf_mat_function,
            elt.length_m,
            n_steps=n_steps,
            beam_kwargs=beam_kwargs,
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

    def transfer_matrix_kw(self) -> dict[str, Any]:
        """Give the fixed args to compute transfer matrix."""
        return {
            "delta_s": self.d_z,
            "factor_1": self.factor_1,
            "factor_2": self.factor_2,
            "factor_3": self.factor_3,
        }
