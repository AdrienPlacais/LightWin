"""Define bayesian optimization algorithms."""

import logging
from typing import Any

import numpy as np
from bayes_opt import BayesianOptimization as BO
from numpy.typing import NDArray

from lightwin.optimisation.algorithms.algorithm import (
    OptimisationAlgorithm,
    OptiSol,
)


class BayesianOptimization(OptimisationAlgorithm):
    """Bayesian optimization algorithm."""

    supports_constraints = False

    def optimize(self) -> OptiSol:
        """Set up the optimization and solve the problem.

        Returns
        -------
            Gives list of solutions, corresponding objective, convergence
            violation if applicable, etc.

        """
        pbounds = self._format_variables()
        optimizer = BO(f=self._to_maximise, pbounds=pbounds, random_state=1)
        optimizer.maximize(**self._default_kwargs)
        self.opti_sol = self._generate_opti_sol(optimizer.max)
        self._finalize(self.opti_sol)
        return self.opti_sol

    def _to_maximise(self, **kwargs) -> float:
        """The function to maximize by BO.

        This is the classic
        :meth:`.OptimisationAlgorithm._norm_wrapper_residuals`, with two
        adaptations:

        - Multiplied by ``-1.0`` to maximize instead of minimize
        - Takes arguments as floats instead of numpy array.
          - Keys are ``Variable.__str__()``

        """
        return -self._norm_wrapper_residuals(self._to_numpy(**kwargs))

    @property
    def _default_kwargs(self) -> dict[str, Any]:
        """Create the ``kwargs`` for the optimisation."""
        kwargs = {"init_points": 50, "n_iter": 300}
        return kwargs

    def _generate_opti_sol(self, result: dict[str, Any]) -> OptiSol:
        """Store the optimization results."""
        status = "compensate (ok)"

        for key in ("params", "target"):
            if key in result:
                continue
            raise ValueError(f"Output of BO should have a {key = }.\n{result}")

        sol = self._to_numpy(**result["params"])
        cavity_settings = self._create_set_of_cavity_settings(sol, status)

        opti_sol: OptiSol = {
            "var": sol,
            "cavity_settings": cavity_settings,
            "fun": result["target"],
            "objectives": self._get_objective_values(sol),
            "success": True,
        }
        return opti_sol

    def _format_variables(self) -> dict[str, tuple[float, float]]:
        """Map every variable name with its limits."""
        pbounds = {str(var): var.limits for var in self.variables}
        return pbounds

    def _to_numpy(self, **kwargs) -> NDArray:
        """Convert dict of variables to numpy array."""
        return np.array([kwargs[str(var)] for var in self.variables])
