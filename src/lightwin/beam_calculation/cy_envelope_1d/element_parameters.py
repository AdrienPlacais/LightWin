"""Define a class to hold solver parameters for :class:`.CyEnvelope1D`.

Almost everything is inherited from the python version of the module. The main
difference is that with the Cython version, we give the transfer matrix
function the name of the field map.

"""

import logging
from typing import Any, Callable

from lightwin.beam_calculation.cy_envelope_1d.util import (
    CY_ENVELOPE1D_METHODS_T,
)
from lightwin.beam_calculation.envelope_1d.element_envelope1d_parameters import (
    BendEnvelope1DParameters,
    DriftEnvelope1DParameters,
    ElementEnvelope1DParameters,
    FieldMapEnvelope1DParameters,
    SuperposedFieldMapEnvelope1DParameters,
)
from lightwin.core.elements.field_maps.cavity_settings import CavitySettings

try:
    from lightwin.beam_calculation.cy_envelope_1d import (
        transfer_matrices,  # type: ignore
    )
except ModuleNotFoundError as e:
    logging.error("Is CyEnvelope1D compiled? Check setup.py.")
    raise ModuleNotFoundError(e)


class ElementCyEnvelope1DParameters(ElementEnvelope1DParameters):
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
        return super().__init__(
            length_m=length_m,
            n_steps=n_steps,
            beam_kwargs=beam_kwargs,
            transf_mat_function=transf_mat_function,
            **kwargs,
        )

    def _proper_transfer_matrix_func(
        self,
        element_nature: str,
        method: CY_ENVELOPE1D_METHODS_T | None = None,
    ) -> Callable:
        """Get the proper transfer matrix function."""
        match method, element_nature:
            case _, "SuperposedFieldMap":
                raise NotImplementedError(
                    "No Cython function for SuperposedFieldMap."
                )
            case "RK4", "FieldMap":
                return transfer_matrices.z_field_map_rk4
            case "leapfrog", "FieldMap":
                return transfer_matrices.z_field_map_leapfrog
            case _, "Bend":
                return transfer_matrices.z_bend
            case _:
                return transfer_matrices.z_drift


class DriftCyEnvelope1DParameters(
    DriftEnvelope1DParameters, ElementCyEnvelope1DParameters
):
    """Hold the properties to compute transfer matrix of a :class:`.Drift`.

    As this is 1D, it is also used for :class:`.Solenoid`, :class:`.Quad`,
    broken :class:`.FieldMap`.

    """


class FieldMapCyEnvelope1DParameters(
    FieldMapEnvelope1DParameters, ElementCyEnvelope1DParameters
):
    """Hold the properties to compute transfer matrix of a :class:`.FieldMap`.

    Non-accelerating cavities will use :class:`.DriftEnvelope1DParameters`
    instead.

    """

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
            function defined in :mod:`.cy_envelope_1d.transfer_matrices`.

        """
        geometry_kwargs = {
            "d_z": self.d_z,
            "n_steps": self.n_steps,
            "filename": self.field_map_file_name,
        }
        rf_field = cavity_settings.rf_field
        rf_kwargs = {
            "bunch_to_rf": cavity_settings.bunch_phase_to_rf_phase,
            "k_e": cavity_settings.k_e,
            "n_cell": rf_field.n_cell,
            "omega0_rf": cavity_settings.omega0_rf,
            "section_idx": rf_field.section_idx,
        }
        match cavity_settings.reference, phi_0_rel:
            case "phi_s", None:  # Prepare fit
                cavity_settings.set_cavity_parameters_arguments(
                    self.solver_id,
                    w_kin,
                    **rf_kwargs,  # no phi_0_rel in kwargs
                )
                # calls phi_0_rel and triggers phi_0_rel calculation (case just below)
                phi_0_rel = _get_phi_0_rel(cavity_settings)
                rf_kwargs["phi_0_rel"] = phi_0_rel
            case "phi_s", _:  # Fitting phi_s
                rf_kwargs["phi_0_rel"] = phi_0_rel
            case _, None:  # Normal run
                phi_0_rel = _get_phi_0_rel(cavity_settings)
                rf_kwargs["phi_0_rel"] = phi_0_rel
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


class SuperposedFieldMapCyEnvelope1DParameters(
    SuperposedFieldMapEnvelope1DParameters, ElementCyEnvelope1DParameters
):
    """
    Hold properties to compute transfer matrix of :class:`.SuperposedFieldMap`.

    """

    def __init__(self, *args, **kwargs) -> None:
        """Create the specific parameters for a superposed field map."""
        raise NotImplementedError


class BendCyEnvelope1DParameters(
    BendEnvelope1DParameters, ElementCyEnvelope1DParameters
):
    """Hold the specific parameters to compute :class:`.Bend` transfer matrix.

    In particular, we define ``factor_1``, ``factor_2`` and ``factor_3`` to
    speed-up calculations.

    """
