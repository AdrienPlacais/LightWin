"""Define a class to easily generate the :class:`.SimulationOutput`.

This class should be subclassed by every :class:`.BeamCalculator` to match its
own specific outputs.

"""

from abc import ABC, ABCMeta, abstractmethod
from dataclasses import dataclass

from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.util.typing import BeamKwargs


@dataclass
class SimulationOutputFactory(ABC):
    """A base class for creation of :class:`.SimulationOutput`."""

    _is_3d: bool
    _is_multipart: bool
    _solver_id: str
    _beam_kwargs: BeamKwargs

    def __post_init__(self) -> None:
        """Create the factories.

        The created factories are :class:`.TransferMatrixFactory` and
        :class:`.BeamParametersFactory`. The sub-class that is used is declared
        in :meth:`._transfer_matrix_factory_class` and
        :meth:`._beam_parameters_factory_class`.

        """
        self.transfer_matrix_factory = self._transfer_matrix_factory_class(
            self._is_3d
        )
        self.beam_parameters_factory = self._beam_parameters_factory_class(
            self._is_3d,
            self._is_multipart,
            beam_kwargs=self._beam_kwargs,
        )

    @property
    @abstractmethod
    def _transfer_matrix_factory_class(self) -> ABCMeta:
        """Declare the **class** of the transfer matrix factory."""

    @property
    @abstractmethod
    def _beam_parameters_factory_class(self) -> ABCMeta:
        """Declare the **class** of the beam parameters factory."""

    @abstractmethod
    def run(self, elts: ListOfElements, *args, **kwargs) -> SimulationOutput:
        """Create the :class:`.SimulationOutput`."""
        pass
