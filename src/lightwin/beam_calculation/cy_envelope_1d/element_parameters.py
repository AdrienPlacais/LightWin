"""Define a class to hold solver parameters for :class:`.CyEnvelope1D`.

Almost everything is inherited from the python version of the module. The main
difference is that with the Cython version, we give the transfer matrix
function the name of the field map.

"""

import logging
from typing import Callable

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
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.physics.synchronous_phases import PHI_S_MODELS
from lightwin.util.typing import BeamKwargs

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
        beam_kwargs: BeamKwargs,
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

    def __init__(
        self,
        elt: FieldMap,
        method: CY_ENVELOPE1D_METHODS_T,
        n_steps_per_cell: int,
        solver_id: str,
        beam_kwargs: BeamKwargs,
        phi_s_model: PHI_S_MODELS = "historical",
        **kwargs: str | int,
    ) -> None:
        """Set the name of the field map and init base class."""
        return super().__init__(
            elt=elt,
            method=method,
            n_steps_per_cell=n_steps_per_cell,
            solver_id=solver_id,
            beam_kwargs=beam_kwargs,
            phi_s_model=phi_s_model,
            **kwargs,
        )


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
