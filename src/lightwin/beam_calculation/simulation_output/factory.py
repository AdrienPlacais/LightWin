"""Define a class to easily generate the :class:`.SimulationOutput`.

This class should be subclassed by every :class:`.BeamCalculator` to match its
own specific outputs.

"""

from abc import ABC, ABCMeta, abstractmethod

from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.util.typing import BeamKwargs, CavParams


class SimulationOutputFactory(ABC):
    """A base class for creation of :class:`.SimulationOutput`."""

    _is_3d: bool

    def __init__(
        self, is_multipart: bool, solver_id: str, beam_kwargs: BeamKwargs
    ) -> None:
        self._is_multipart = is_multipart
        self._solver_id = solver_id
        self._beam_kwargs = beam_kwargs

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
    def create(
        self, accelerator_id: str, elts: ListOfElements, *args, **kwargs
    ) -> SimulationOutput:
        """Create the :class:`.SimulationOutput`."""
        pass

    @abstractmethod
    def _get_cav_params(self, *args, **kwargs) -> CavParams:
        """Load and format a dict containing cavity parameters."""
