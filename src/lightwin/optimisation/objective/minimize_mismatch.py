"""Hold mismatch related functions.

It has its own module as this quantity is pretty specific.

"""

import logging
from typing import Any

from numpy.typing import NDArray

from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.beam_parameters.helper import mismatch_from_arrays
from lightwin.optimisation.objective.objective import Objective
from lightwin.util.typing import GETTABLE_BEAM_PARAMETERS_T


class MinimizeMismatch(Objective):
    """Minimize a mismatch factor."""

    def __init__(
        self,
        name: str,
        weight: float,
        get_key: GETTABLE_BEAM_PARAMETERS_T,
        get_kwargs: dict[str, Any],
        reference: SimulationOutput,
        descriptor: str | None = None,
    ) -> None:
        """
        Set complementary :meth:`.SimulationOutput.get` flags, reference value.

        Parameters
        ----------
        name :
            A short string to describe the objective and access to it.
        weight :
            A scaling constant to set the weight of current objective.
        get_key :
            Must contain 'twiss' plus the name of a phase-space, or simply
            'twiss' and the phase-space is defined in ``get_kwargs``.
        get_kwargs :
            Keyword arguments for the :meth:`.SimulationOutput.get` method. We
            do not check its validity, but in general you will want to define
            the keys ``elt`` and ``pos``. You should also define the
            ``phase_space_name`` key if it is not defined in the ``get_key``.
        reference :
            The reference simulation output from which the Twiss parameters
            will be taken.
        descriptor :
            A longer string to explain the objective.

        """
        if "twiss" not in get_key:
            logging.warning(
                "The get_key should contain 'twiss'. Taking 'twiss' and "
                "setting phase space to zdelta."
            )
            get_key = "twiss"
            get_kwargs["phase_space_name"] = "zdelta"
        self._check_get_arguments(get_key, get_kwargs)
        self.get_key: GETTABLE_BEAM_PARAMETERS_T = get_key
        self.get_kwargs = get_kwargs
        super().__init__(name, weight, descriptor=descriptor, ideal_value=0.0)
        self._twiss_ref = self._twiss_getter(reference)

    def base_str(self) -> str:
        """Tell nature and position of objective."""
        message = f"{self.name:>23}"

        elt = str(self.get_kwargs.get("elt", "NA"))
        message += f" @elt {elt:>5}"

        pos = str(self.get_kwargs.get("pos", "NA"))
        message += f" ({pos:>3}) | {self.weight:>5} | "
        return message

    def __str__(self) -> str:
        """Give objective information value."""
        return self.base_str() + f"{self.ideal_value:+.14e}"

    def _twiss_getter(self, simulation_output: SimulationOutput) -> NDArray:
        """Get desired value using :meth:`.SimulationOutput.get` method."""
        return simulation_output.beam_parameters.get(
            self.get_key, **self.get_kwargs
        )

    def evaluate(self, simulation_output: SimulationOutput) -> float:
        twiss_fix = self._twiss_getter(simulation_output)
        return self._compute_residuals(twiss_fix)

    def _compute_residuals(self, twiss_fix: NDArray) -> float:
        """Compute residuals, that we want to minimize."""
        res = mismatch_from_arrays(self._twiss_ref, twiss_fix)[0]
        return self.weight * res
