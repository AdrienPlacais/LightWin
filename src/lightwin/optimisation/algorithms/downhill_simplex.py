"""Define the Downhill simplex (or Nelder-Mead) algorihm."""

from typing import Any

import numpy as np
from scipy.optimize import Bounds, OptimizeResult, minimize

from lightwin.optimisation.algorithms.algorithm import (
    OptimisationAlgorithm,
    OptiSol,
)


class DownhillSimplex(OptimisationAlgorithm):
    """Downhill simplex method, which does not use derivatives.

    All the attributes but ``solution`` are inherited from the Abstract Base
    Class :class:`.OptimisationAlgorithm`.

    See also
    --------
    :class:`.DownhillSimplexPenalty`

    """

    supports_constraints = False

    def optimize(self) -> OptiSol:
        """Set up the optimization and solve the problem.

        Returns
        -------
            Gives list of solutions, corresponding objective, convergence
            violation if applicable, etc.

        """
        x_0, bounds = self._format_variables()
        result = minimize(
            fun=self._norm_wrapper_residuals,
            x0=x_0,
            bounds=bounds,
            **self.optimisation_algorithm_kwargs,
        )
        self.opti_sol = self._generate_opti_sol(result)
        complementary_info = ("Nelder-Mead algorithm", result.message)
        self._finalize(self.opti_sol, *complementary_info)
        return self.opti_sol

    @property
    def _default_kwargs(self) -> dict[str, Any]:
        """Create the ``kwargs`` for the optimisation."""
        kwargs = {
            "method": "Nelder-Mead",
            "options": {
                "adaptive": True,
                "disp": True,
            },
        }
        return kwargs

    def _generate_opti_sol(self, result: OptimizeResult) -> OptiSol:
        """Store the optimization results."""
        status = "compensate (ok)"
        if not result.success:
            status = "compensate (not ok)"
        cavity_settings = self._create_set_of_cavity_settings(result.x, status)

        opti_sol: OptiSol = {
            "var": result.x,
            "cavity_settings": cavity_settings,
            "fun": result.fun,
            "objectives": self._get_objective_values(result.x),
            "success": result.success,
        }
        return opti_sol

    def _format_variables(self) -> tuple[np.ndarray, Bounds]:
        """Convert the :class:`.Variable` to an array and ``Bounds``."""
        x_0 = np.array([var.x_0 for var in self.variables])
        _bounds = np.array([var.limits for var in self.variables])
        bounds = Bounds(_bounds[:, 0], _bounds[:, 1])
        return x_0, bounds
