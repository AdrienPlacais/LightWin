"""Define a class to easily generate the :class:`.SimulationOutput`."""

from abc import ABCMeta

from lightwin.beam_calculation.envelope_1d.simulation_output_factory import (
    SimulationOutputFactoryEnvelope1D,
)
from lightwin.beam_calculation.envelope_3d.beam_parameters_factory import (
    BeamParametersFactoryEnvelope3D,
)
from lightwin.beam_calculation.envelope_3d.transfer_matrix_factory import (
    TransferMatrixFactoryEnvelope3D,
)


class SimulationOutputFactoryEnvelope3D(SimulationOutputFactoryEnvelope1D):
    """A class for creating simulation outputs for :class:`.Envelope3D`."""

    _is_3d = True

    @property
    def _transfer_matrix_factory_class(self) -> ABCMeta:
        """Give the **class** of the transfer matrix factory."""
        return TransferMatrixFactoryEnvelope3D

    @property
    def _beam_parameters_factory_class(self) -> ABCMeta:
        """Give the **class** of the beam parameters factory."""
        return BeamParametersFactoryEnvelope3D
