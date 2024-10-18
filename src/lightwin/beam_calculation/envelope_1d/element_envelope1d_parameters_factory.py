"""Create the solver parameters for :class:`.Envelope1D`."""

import logging
from typing import Any, Literal

from lightwin.beam_calculation.envelope_1d.element_envelope1d_parameters import (
    BendEnvelope1DParameters,
    DriftEnvelope1DParameters,
    ElementEnvelope1DParameters,
    FieldMapEnvelope1DParameters,
)
from lightwin.beam_calculation.envelope_1d.util import (
    ENVELOPE1D_METHODS,
    ENVELOPE1D_METHODS_T,
)
from lightwin.beam_calculation.parameters.factory import (
    ElementBeamCalculatorParametersFactory,
)
from lightwin.core.elements.aperture import Aperture
from lightwin.core.elements.bend import Bend
from lightwin.core.elements.diagnostic import Diagnostic
from lightwin.core.elements.drift import Drift
from lightwin.core.elements.edge import Edge
from lightwin.core.elements.element import Element
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.elements.quad import Quad
from lightwin.core.elements.solenoid import Solenoid

PARAMETERS_1D = {
    Aperture: DriftEnvelope1DParameters,
    Bend: BendEnvelope1DParameters,
    Edge: DriftEnvelope1DParameters,
    Diagnostic: DriftEnvelope1DParameters,
    Drift: DriftEnvelope1DParameters,
    FieldMap: FieldMapEnvelope1DParameters,
    Quad: DriftEnvelope1DParameters,
    Solenoid: DriftEnvelope1DParameters,
}  #:


class ElementEnvelope1DParametersFactory(
    ElementBeamCalculatorParametersFactory
):
    """Define a method to easily create the solver parameters."""

    def __init__(
        self,
        method: ENVELOPE1D_METHODS_T,
        n_steps_per_cell: int,
        solver_id: str,
        beam_kwargs: dict[str, Any],
        flag_cython: bool = False,
        phi_s_definition: Literal["historical"] = "historical",
    ) -> None:
        """Prepare import of proper functions."""
        assert method in ENVELOPE1D_METHODS
        self.method = method
        self.n_steps_per_cell = n_steps_per_cell
        self.solver_id = solver_id
        self.phi_s_definition = phi_s_definition
        self.beam_kwargs = beam_kwargs

        if flag_cython:
            try:
                import lightwin.beam_calculation.envelope_1d.transfer_matrices_c as transf_mat_module
            except ModuleNotFoundError:
                logging.error(
                    "Cython not found. Maybe it was not compilated. Check "
                    "util/setup.py for information."
                )
                raise ModuleNotFoundError
        else:
            import lightwin.beam_calculation.envelope_1d.transfer_matrices_p as transf_mat_module
        self.transf_mat_module = transf_mat_module

    def run(self, elt: Element) -> ElementEnvelope1DParameters:
        """Create the proper subclass of solver parameters, instantiate it.

        .. note::
            If an Element type is not found in ``PARAMETERS_1D``, we take
            its mother type.

        Parameters
        ----------
        elt : Element
            Element under study.

        Returns
        -------
        ElementEnvelope1DParameters
            Proper instantiated subclass of
            :class:`.ElementEnvelope1DParameters`.

        See also
        --------
        _parameters_constructor

        """
        subclass = self._parameters_constructor(elt)
        kwargs = {
            "method": self.method,
            "n_steps_per_cell": self.n_steps_per_cell,
            "solver_id": self.solver_id,
            "phi_s_definition": self.phi_s_definition,
        }
        single_element_envelope_1d_parameters = subclass(
            self.transf_mat_module,
            elt=elt,
            beam_kwargs=self.beam_kwargs,
            **kwargs,
        )

        return single_element_envelope_1d_parameters

    def _parameters_constructor(
        self, elt: Element, default: type = PARAMETERS_1D[Drift]
    ) -> type:
        """Get the proper object constructor.

        Examples
        --------
        >>> self._parameters_constructor(Drift())
        DriftEnvelope1DParameters

        In 1D, a quadrupole is basically a drift.

        >>> self._parameters_constructor(Quad())
        DriftEnvelope1DParameters

        As DiagPosition is not in PARAMETERS_1D, we look for the mother
        class Diagnostic.

        >>> self._parameters_constructor(DiagPosition())
        DriftEnvelope1DParameters

        To avoid wasting computation time, non-accelerating field maps are
        treated as drifts.

        >>> self._parameters_constructor(FieldMap100(is_accelerating=False))
        DriftEnvelope1DParameters

        """
        if isinstance(elt, FieldMap) and not elt.is_accelerating:
            return default

        element_class = type(elt)
        constructor = PARAMETERS_1D.get(element_class, None)
        if constructor is not None:
            return constructor

        super_class = element_class.__base__
        constructor = PARAMETERS_1D.get(super_class, None)
        if constructor is not None:
            return constructor

        logging.error(
            f"Element {elt} of {element_class = } not added to the Envelope1D "
            "dict linking every Element class to its specific parameters"
            "(transfer matrix in particular). Neither was found its "
            f"{super_class = }. "
            "Note that you can use the elements_to_dump key in the "
            "Envelope1D.ListOfElementFactory class."
        )
        return default
