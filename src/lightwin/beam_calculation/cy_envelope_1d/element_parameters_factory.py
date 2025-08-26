"""Create the solver parameters for :class:`.CyEnvelope1D`."""

from lightwin.beam_calculation.cy_envelope_1d.element_parameters import (
    BendCyEnvelope1DParameters,
    DriftCyEnvelope1DParameters,
    ElementCyEnvelope1DParameters,
    FieldMapCyEnvelope1DParameters,
    SuperposedFieldMapCyEnvelope1DParameters,
)
from lightwin.beam_calculation.envelope_1d.element_envelope1d_parameters_factory import (
    ElementEnvelope1DParametersFactory,
)
from lightwin.core.elements.aperture import Aperture
from lightwin.core.elements.bend import Bend
from lightwin.core.elements.diagnostic import Diagnostic
from lightwin.core.elements.drift import Drift
from lightwin.core.elements.edge import Edge
from lightwin.core.elements.element import Element
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.elements.field_maps.superposed_field_map import (
    SuperposedFieldMap,
)
from lightwin.core.elements.quad import Quad
from lightwin.core.elements.solenoid import Solenoid

#: Implemented elements; a non-implemented element will be replaced by a Drift.
#: A warning will be raised.
CY_PARAMETERS_1D = {
    Aperture: DriftCyEnvelope1DParameters,
    Bend: BendCyEnvelope1DParameters,
    Diagnostic: DriftCyEnvelope1DParameters,
    Drift: DriftCyEnvelope1DParameters,
    Edge: DriftCyEnvelope1DParameters,
    FieldMap: FieldMapCyEnvelope1DParameters,
    Quad: DriftCyEnvelope1DParameters,
    Solenoid: DriftCyEnvelope1DParameters,
    SuperposedFieldMap: SuperposedFieldMapCyEnvelope1DParameters,
}


class ElementCyEnvelope1DParametersFactory(ElementEnvelope1DParametersFactory):
    """Define a method to easily create the solver parameters."""

    _parameters = CY_PARAMETERS_1D

    def run(self, elt: Element) -> ElementCyEnvelope1DParameters:
        """Create the proper subclass of solver parameters, instantiate it.

        .. note::
            If an Element type is not found in ``self.parameters``, we take its
            mother type.

        Parameters
        ----------
        elt :
            Element under study.

        Returns
        -------
            Proper instantiated subclass of
            :class:`.ElementCyEnvelope1DParameters`.

        """
        single_element_cy_envelope_1d_parameters = super().run(elt)
        return single_element_cy_envelope_1d_parameters
