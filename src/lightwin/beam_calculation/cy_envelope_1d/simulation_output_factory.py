"""Define a class to easily generate the :class:`.SimulationOutput`."""

from abc import ABCMeta
from dataclasses import dataclass

from lightwin.beam_calculation.cy_envelope_1d.beam_parameters_factory import (
    BeamParametersFactoryCyEnvelope1D,
)
from lightwin.beam_calculation.cy_envelope_1d.transfer_matrix_factory import (
    TransferMatrixFactoryCyEnvelope1D,
)
from lightwin.beam_calculation.envelope_1d.simulation_output_factory import (
    SimulationOutputFactoryEnvelope1D,
)


@dataclass
class SimulationOutputFactoryCyEnvelope1D(SimulationOutputFactoryEnvelope1D):
    """A class for creating simulation outputs for :class:`.CyEnvelope1D`."""

    @property
    def _transfer_matrix_factory_class(self) -> ABCMeta:
        """Give the **class** of the transfer matrix factory."""
        return TransferMatrixFactoryCyEnvelope1D

    @property
    def _beam_parameters_factory_class(self) -> ABCMeta:
        """Give the **class** of the beam parameters factory."""
        return BeamParametersFactoryCyEnvelope1D
