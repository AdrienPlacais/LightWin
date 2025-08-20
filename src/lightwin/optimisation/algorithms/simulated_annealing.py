"""Define the simulated annealing algorithm."""

from typing import Any

from scipy.optimize import OptimizeResult, dual_annealing

from lightwin.optimisation.algorithms.algorithm import (
    OptimisationAlgorithm,
    OptiSol,
)


class SimulatedAnnealing(OptimisationAlgorithm):
    """Simulated Annealing method for global optimization."""

    supports_constraints = False

    def optimize(self) -> OptiSol:
        """Set up and run the simulated annealing algorithm.

        Returns
        -------
            Contains solution(s), objective value(s), status, etc.

        """
        bounds = self._format_bounds()
        result = dual_annealing(
            func=self._norm_wrapper_residuals,
            bounds=bounds,
            **self.optimisation_algorithm_kwargs,
        )
        self.opti_sol = self._generate_opti_sol(result)
        message = result.message
        if isinstance(message, list):
            message = "\n".join(message)
        complementary_info = ("Simulated Annealing", message)
        self._finalize(self.opti_sol, *complementary_info)
        return self.opti_sol

    @property
    def _default_kwargs(self) -> dict[str, Any]:
        """Default parameters for dual_annealing."""
        kwargs = {
            "maxiter": 100,
            "initial_temp": 5230.0,
            "restart_temp_ratio": 2e-5,
            "visit": 2.62,
            "accept": -5.0,
            "no_local_search": False,
        }
        return kwargs

    def _generate_opti_sol(self, result: OptimizeResult) -> OptiSol:
        """Package the results into an OptiSol dictionary."""
        status = "compensate (ok)" if result.success else "compensate (not ok)"
        cavity_settings = self._create_set_of_cavity_settings(result.x, status)

        opti_sol: OptiSol = {
            "var": result.x,
            "cavity_settings": cavity_settings,
            "fun": result.fun,
            "objectives": self._get_objective_values(result.x),
            "success": result.success,
        }
        return opti_sol

    def _format_bounds(self) -> list[tuple[float, float]]:
        """Convert Variable objects to a list of bounds."""
        return [var.limits for var in self.variables]
