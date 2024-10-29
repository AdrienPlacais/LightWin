"""Define a class to hold solver parameters for :class:`.Envelope3D`.

This module holds :class:`ElementEnvelope3DParameters`, that inherits
from the Abstract Base Class :class:`.ElementBeamCalculatorParameters`.
It holds the transfer matrix function that is used, as well as the meshing in
accelerating elements.

In a first time, only Runge-Kutta (no leapfrog) and only Python (no Cython).

The list of implemented transfer matrices is :data:`.PARAMETERS_3D`.

"""

import logging
from collections.abc import Callable
from typing import Any

import numpy as np

import lightwin.util.converters as convert
from lightwin.beam_calculation.envelope_1d.element_envelope1d_parameters import (
    ElementEnvelope1DParameters,
)
from lightwin.beam_calculation.envelope_3d import (
    transfer_matrices_p as transfer_matrices,
)
from lightwin.core.elements.bend import Bend
from lightwin.core.elements.drift import Drift
from lightwin.core.elements.field_maps.cavity_settings import CavitySettings
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.elements.quad import Quad
from lightwin.core.elements.solenoid import Solenoid
from lightwin.core.em_fields.rf_field import compute_param_cav
from lightwin.core.em_fields.types import FieldFuncComplexTimedComponent
from lightwin.util.synchronous_phases import (
    PHI_S_MODELS,
    SYNCHRONOUS_PHASE_FUNCTIONS,
)


class ElementEnvelope3DParameters(ElementEnvelope1DParameters):
    """Hold the parameters to compute beam propagation in an :class:`.Element`.

    has and get method inherited from ElementCalculatorParameters parent
    class.

    """

    def __init__(
        self,
        length_m: float,
        n_steps: int,
        beam_kwargs: dict[str, Any],
        transf_mat_function: Callable | None = None,
        **kwargs,
    ) -> None:
        """Save useful parameters as attribute.

        Parameters
        ----------
        length_m : float
            length_m
        n_steps : int
            n_steps
        beam_kwargs : dict[str, Any]
            Configuration dict holding initial beam parameters.
        transf_mat_function : Callable | None, optional
            Function to compute transfer matrix of element. The default is
            None, in which case we fall back on Drift transfer matrix.

        """
        if transf_mat_function is None:
            transf_mat_function = self._proper_transfer_matrix_func("Drift")
        super().__init__(
            length_m=length_m,
            n_steps=n_steps,
            beam_kwargs=beam_kwargs,
            transf_mat_function=transf_mat_function,
        )

    def _transfer_matrix_results_to_dict(
        self,
        transfer_matrix: np.ndarray,
        gamma_phi: np.ndarray,
        integrated_field: float | None,
    ) -> dict:
        """Convert the results given by the transf_mat function to dict."""
        assert integrated_field is None
        w_kin = convert.energy(
            gamma_phi[:, 0], "gamma to kin", **self._beam_kwargs
        )
        results = {
            "transfer_matrix": transfer_matrix,
            "r_zz": transfer_matrix[:, 4:, 4:],
            "cav_params": None,
            "w_kin": w_kin,
            "phi_rel": gamma_phi[:, 1],
            "integrated_field": integrated_field,
        }
        return results

    def _proper_transfer_matrix_func(
        self, element_nature: str, method: str | None = None
    ) -> Callable:
        """Get the proper transfer matrix function."""
        if method is not None and method != "RK4":
            logging.warning(
                "Only RK4 integration method is implemented for Envelope3D."
            )
        match element_nature:
            case "Drift":
                return transfer_matrices.drift
            case "Quad":
                return transfer_matrices.quad
            case "Solenoid":
                raise NotImplementedError(
                    "Solenoid transf mat not implemented in 3D."
                )
                return transfer_matrices.solenoid
            case "FieldMap":
                return transfer_matrices.field_map_rk4
            case "Bend":
                raise NotImplementedError(
                    "Bend transf mat not implemented in 3D."
                )
                return transfer_matrices.bend
            case _:
                raise NotImplementedError(
                    f"No parameters defined for {element_nature = }"
                )


class DriftEnvelope3DParameters(ElementEnvelope3DParameters):
    """Hold the properties to compute transfer matrix of a :class:`.Drift`."""

    def __init__(
        self,
        elt: Drift | FieldMap,
        beam_kwargs: dict[str, Any],
        n_steps: int = 1,
        **kwargs: str,
    ) -> None:
        """Create the specific parameters for a drift."""
        super().__init__(
            elt.length_m,
            n_steps=n_steps,
            beam_kwargs=beam_kwargs,
            transf_mat_function=self._proper_transfer_matrix_func("Drift"),
            **kwargs,
        )


class QuadEnvelope3DParameters(ElementEnvelope3DParameters):
    """Hold the properties to compute transfer matrix of a :class:`.Quad`."""

    def __init__(
        self,
        elt: Quad,
        beam_kwargs: dict[str, Any],
        n_steps: int = 1,
        **kwargs: str,
    ) -> None:
        """Create the specific parameters for a drift."""
        super().__init__(
            length_m=elt.length_m,
            beam_kwargs=beam_kwargs,
            n_steps=n_steps,
            transf_mat_function=self._proper_transfer_matrix_func("Quad"),
            **kwargs,
        )
        self.gradient = elt.grad

    def transfer_matrix_kw(self, *args, **kwargs) -> dict[str, Any]:
        """Give the element parameters necessary to compute transfer matrix."""
        return self._beam_kwargs | {
            "delta_s": self.d_z,
            "gradient": self.gradient,
        }


class SolenoidEnvelope3DParameters(ElementEnvelope3DParameters):
    """Hold properties to compute transfer matrix of a :class:`.Solenoid`."""

    def __init__(
        self,
        elt: Solenoid,
        beam_kwargs: dict[str, Any],
        n_steps: int = 1,
        **kwargs: str,
    ) -> None:
        """Create the specific parameters for a drift."""
        raise NotImplementedError


class FieldMapEnvelope3DParameters(ElementEnvelope3DParameters):
    """Hold the properties to compute transfer matrix of a :class:`.FieldMap`.

    Non-accelerating cavities will use :class:`.DriftEnvelope3DParameters`
    instead.

    """

    def __init__(
        self,
        elt: FieldMap,
        method: str,
        n_steps_per_cell: int,
        solver_id: str,
        beam_kwargs: dict[str, Any],
        phi_s_model: PHI_S_MODELS = "historical",
        **kwargs: str,
    ) -> None:
        """Create the specific parameters for a drift."""
        transf_mat_function = self._proper_transfer_matrix_func(
            "FieldMap", method
        )
        self.compute_cavity_parameters = SYNCHRONOUS_PHASE_FUNCTIONS[
            phi_s_model
        ]

        self.solver_id = solver_id
        self.n_cell = elt.rf_field.n_cell
        self._rf_to_bunch = elt.cavity_settings.rf_phase_to_bunch_phase
        n_steps = self.n_cell * n_steps_per_cell
        super().__init__(
            elt.length_m,
            n_steps,
            beam_kwargs=beam_kwargs,
            transf_mat_function=transf_mat_function,
            **kwargs,
        )
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
            Keyword arguments that will be passed to the 3D transfer matrix
            function defined in :mod:`.envelope_3d.transfer_matrices_p`.

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


def _get_phi_0_rel(cavity_settings: CavitySettings) -> float:
    """Get the phase from the object."""
    phi_0_rel = cavity_settings.phi_0_rel
    assert phi_0_rel is not None
    return phi_0_rel

    def _transfer_matrix_results_to_dict(
        self,
        transfer_matrix: np.ndarray,
        gamma_phi: np.ndarray,
        integrated_field: float | None,
    ) -> dict:
        """Convert the results given by the transf_mat function to dict.

        Overrides the default method defined in the ABC.

        """
        assert integrated_field is not None
        w_kin = convert.energy(
            gamma_phi[:, 0], "gamma to kin", **self._beam_kwargs
        )
        gamma_phi[:, 1] = self._rf_to_bunch(gamma_phi[:, 1])
        cav_params = compute_param_cav(integrated_field)
        results = {
            "transfer_matrix": transfer_matrix,
            "r_zz": transfer_matrix[:, 4:, 4:],
            "cav_params": cav_params,
            "w_kin": w_kin,
            "phi_rel": gamma_phi[:, 1],
            "integrated_field": integrated_field,
        }
        return results

    def re_set_for_broken_cavity(self) -> Callable:
        """Make beam calculator call Drift func instead of FieldMap."""
        self.transf_mat_function = self._proper_transfer_matrix_func("Drift")
        self.transfer_matrix_kw = self._broken_transfer_matrix_kw
        self._transfer_matrix_results_to_dict = (
            self._broken_transfer_matrix_results_to_dict
        )
        return self.transf_mat_function

    def _broken_transfer_matrix_results_to_dict(
        self,
        transfer_matrix: np.ndarray,
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
            "transfer_matrix": transfer_matrix,
            "r_zz": transfer_matrix[4:, 4:],
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


class BendEnvelope3DParameters(ElementEnvelope3DParameters):
    """Hold specific parameters to compute :class:`.Bend` transfer matrix."""

    def __init__(
        self,
        elt: Bend,
        beam_kwargs: dict[str, Any],
        n_steps: int = 1,
        **kwargs: str,
    ):
        """Instantiate object and pre-compute some parameters for speed.

        Parameters
        ----------
        transf_mat_module : types.ModuleType
            Module where the transfer matrix function is defined.
        elt : Bend
            ``BEND`` element.
        kwargs :
            kwargs

        """
        raise NotImplementedError


def _add_cavity_phase(
    solver_id: str,
    w_kin_in: float,
    cavity_settings: CavitySettings,
    rf_kwargs: dict[str, Callable | int | float],
) -> None:
    r"""Set reference phase and function to compute :math:`\phi_s`."""
    if cavity_settings.reference == "phi_s":
        cavity_settings.set_cavity_parameters_arguments(
            solver_id, w_kin_in, **rf_kwargs
        )
        phi_0_rel = cavity_settings.phi_0_rel
        assert phi_0_rel is not None
        rf_kwargs["phi_0_rel"] = phi_0_rel
        return

    phi_0_rel = cavity_settings.phi_0_rel
    assert phi_0_rel is not None
    rf_kwargs["phi_0_rel"] = phi_0_rel
    cavity_settings.set_cavity_parameters_arguments(
        solver_id, w_kin_in, **rf_kwargs
    )
