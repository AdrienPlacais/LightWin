"""Define :class:`Constraint`, which stores a constraint.

It saves it's name, limits, and methods to evaluate if it is violated or not.

"""

import logging
import math
from dataclasses import dataclass

import numpy as np

from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.optimisation.design_space.design_space_parameter import (
    DesignSpaceParameter,
)
from lightwin.util.typing import CONSTRAINTS


@dataclass
class Constraint(DesignSpaceParameter):
    """A single constraint.

    For now, it can only be a synchronous phase limits. By convention, all
    calculations are done in rad, and phases are always printed in deg.

    """

    def __post_init__(self):
        """Convert values in deg for output if it is angle."""
        logging.critical("Dirty patch, phi_s is hard-coded")
        if self.name not in CONSTRAINTS:
            raise ValueError("phi_s constraint hard-coded!!")
            logging.warning("Constraint not tested.")
        # in particular: phi_s is hard-coded in get_value!!

        super().__post_init__()
        self._to_deg = False
        self._to_numpy = False
        if "phi" not in self.name:
            return

        for lim in self.limits:
            if lim < -math.pi or lim > math.pi:
                logging.error(
                    f"Phase limits are expected to be in [-pi, +pi]. {lim = }"
                )

    @property
    def kwargs(self) -> dict[str, bool]:
        """Return the `kwargs` to send a `get` method."""
        _kwargs = {
            "to_deg": self._to_deg,
            "to_numpy": self._to_numpy,
            "elt": self.element_name,
        }
        return _kwargs

    @property
    def n_constraints(self) -> int:
        """Return number of embedded constraints in this object.

        A lower + and upper bound count as two constraints.

        """
        return np.where(~np.isnan(np.array(self.limits)))[0].shape[0]

    def get_value(self, simulation_output: SimulationOutput) -> float:
        """Get from the `SimulationOutput` the quantity called `self.name`.

        Currently bugged. When trying too access ``phi_s``, we get the value
        stored in ``SimulationOutput.elts`` instead of the one in
        ``SetOfCavitySettings``.
        So we end up with the ``phi_s`` from the broken linac instead of the
        ones in the cavity settings we just tried.

        """
        for key, value in simulation_output.set_of_cavity_settings.items():
            if key.name == self.element_name:
                return value.phi_s
        raise ValueError("phi_s not found")
        return simulation_output.get(self.name, **self.kwargs)

    def evaluate(
        self, simulation_output: SimulationOutput
    ) -> tuple[float, float]:
        """Check if constraint is respected.

        They should be < 0.

        """
        value = self.get_value(simulation_output)
        const = (self.limits[0] - value, value - self.limits[1])
        return const
