"""Define a class to hold optimisation objective with its ideal value."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.util.typing import GETTABLE_SIMULATION_OUTPUT


@dataclass
class Objective(ABC):
    """Hold an objective and methods to evaluate it.

    Parameters
    ----------
    name :
        A short string to describe the objective and access to it.
    weight :
        A scaling constant to set the weight of current objective.
    descriptor :
        A longer string to explain the objective.
    ideal_value :
        The ideal value or range of values that we should tend to.

    """

    name: str
    weight: float
    descriptor: str | None = None
    ideal_value: Any | None = None

    def __post_init__(self) -> None:
        """Avoid line jumps in the descriptor."""
        if self.descriptor is None:
            self.descriptor = ""
            return
        self.descriptor = " ".join(self.descriptor.split())

    @abstractmethod
    def __str__(self) -> str:
        """Output info on what is this objective about."""

    @abstractmethod
    def base_str(self) -> str:
        """Tell nature and position of objective."""

    @staticmethod
    def str_header() -> str:
        """Give a header to explain what :meth:`__str__` returns."""
        header = f"{'What, where, etc': ^40} | {'wgt.':>5} | "
        header += f"{'ideal value': ^21}"
        return header

    @abstractmethod
    def evaluate(self, simulation_output: SimulationOutput) -> float:
        """Compute residuals of this objective.

        Parameters
        ----------
        simulation_output :
            Object containing simulation results of the broken linac.

        Returns
        -------
            Difference between current evaluation and ``ideal_value`` value for
            ``self.name``, scaled by ``self.weight``.

        """

    def _compute_residuals(self, *args, **kwargs) -> float:
        """Compute residual (loss), for a given value.

        In general, you will want to call this function from
        :meth:`.Objective.evaluate`.

        """
        raise NotImplementedError

    def _check_get_arguments(
        self, get_key: str, get_kwargs: dict[str, Any]
    ) -> None:
        """Check validity of ``get_args``, ``get_kwargs``.

        In general, residuals evaluation relies on a
        :meth:`.SimulationOutput.get` method. This method uses ``get_args`` and
        ``get_kwargs``; we perform here some basic checks.

        """
        if get_key not in GETTABLE_SIMULATION_OUTPUT:
            logging.warning(
                f"{get_key = } may not be gettable by SimulationOutput.get "
                "method. Authorized values are:\n"
                f"{GETTABLE_SIMULATION_OUTPUT = }"
            )

        advised_keys = ["elt", "pos", "to_numpy"]
        if "phi" in get_key:
            advised_keys.append("to_deg")
        for key in advised_keys:
            if key in get_kwargs:
                continue
            logging.warning(
                f"{key = } is recommended to avoid undetermined behavior but "
                "was not found."
            )
