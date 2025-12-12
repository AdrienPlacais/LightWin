"""Define a class to easily generate the :class:`.SimulationOutput`."""

from abc import ABCMeta
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from lightwin.beam_calculation.envelope_1d.simulation_output_factory import (
    SimulationOutputFactoryEnvelope1D,
)
from lightwin.beam_calculation.envelope_3d.beam_parameters_factory import (
    BeamParametersFactoryEnvelope3D,
)
from lightwin.beam_calculation.envelope_3d.transfer_matrix_factory import (
    TransferMatrixFactoryEnvelope3D,
)
from lightwin.beam_calculation.simulation_output.factory import (
    SimulationOutputFactory,
)
from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.core.particle import ParticleFullTrajectory
from lightwin.failures.set_of_cavity_settings import SetOfCavitySettings


@dataclass
class SimulationOutputFactoryEnvelope3D(SimulationOutputFactoryEnvelope1D):
    """A class for creating simulation outputs for :class:`.Envelope3D`."""

    out_folder: Path

    def __post_init__(self) -> None:
        """Create the factories.

        The created factories are :class:`.TransferMatrixFactory` and
        :class:`.BeamParametersFactory`. The sub-class that is used is declared
        in :meth:`._transfer_matrix_factory_class` and
        :meth:`._beam_parameters_factory_class`.

        """
        # Factories created in ABC's __post_init__
        return super().__post_init__()

    @property
    def _transfer_matrix_factory_class(self) -> ABCMeta:
        """Give the **class** of the transfer matrix factory."""
        return TransferMatrixFactoryEnvelope3D

    @property
    def _beam_parameters_factory_class(self) -> ABCMeta:
        """Give the **class** of the beam parameters factory."""
        return BeamParametersFactoryEnvelope3D

    def run(
        self,
        elts: ListOfElements,
        single_elts_results: list[dict],
        set_of_cavity_settings: SetOfCavitySettings,
        is_3d: bool = True,
    ) -> SimulationOutput:
        return super().run(
            elts, single_elts_results, set_of_cavity_settings, is_3d=is_3d
        )
