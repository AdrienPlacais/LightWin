"""Provide an easy way to generate :class:`.TransferMatrix`."""

from lightwin.beam_calculation.envelope_1d.transfer_matrix_factory import (
    TransferMatrixFactoryEnvelope1D,
)


class TransferMatrixFactoryCyEnvelope1D(TransferMatrixFactoryEnvelope1D):
    """Provide a method for easy creation of :class:`.TransferMatrix`."""
