"""Define the Bayesian optimization algorithm using bayes_opt."""

from typing import Any
import numpy as np
from bayes_opt import BayesianOptimization as BO
from bayes_opt.util import UtilityFunction

from lightwin.optimisation.algorithms.algorithm import (
    OptimisationAlgorithm,
    OptiSol,
)


class BayesianOptimization(OptimisationAlgorithm):
    """Bayesian optimization method using bayes_opt.BayesianOptimization.

    All the attributes but ``solution`` are inherited from the Abstract Base
    Class :class:`.OptimisationAlgorithm`.
    """

    supports_constraints = False

    def optimize(self) -> OptiSol:
        """Set up the optimization and solve the problem."""
        pbounds = self._format_bounds()
        # Remove init_points and n_iter from kwargs for the constructor
        bo_kwargs = {k: v for k, v in self.optimisation_algorithm_kwargs.items() if k not in ("init_points", "n_iter")}
        optimizer = BO(
            f=self._norm_wrapper_residuals_bayes,
            pbounds=pbounds,
            verbose=2,
            **bo_kwargs,
        )
        utility = UtilityFunction(kind="ei", kappa=0.1, xi=1)
        # Get init_points and n_iter from kwargs or defaults
        init_points = self.optimisation_algorithm_kwargs.get("init_points", self._default_kwargs["init_points"])
        n_iter = self.optimisation_algorithm_kwargs.get("n_iter", self._default_kwargs["n_iter"])
        optimizer.maximize(
            init_points=init_points,
            n_iter=n_iter,
            acq=utility.kind,
            kappa=utility.kappa,
            xi=utility.xi,
        )
        x_best = np.array([optimizer.max["params"][name] for name in pbounds])
        self.opti_sol = self._generate_opti_sol(x_best, optimizer)
        complementary_info = ("Bayesian Optimization", "Finished")
        self._finalize(self.opti_sol, *complementary_info)
        return self.opti_sol

    @property
    def _default_kwargs(self) -> dict[str, Any]:
        """Create the ``kwargs`` for the optimisation."""
        kwargs = {
            "init_points": 5,
            "n_iter": 500,
        }
        return kwargs

    def _generate_opti_sol(self, x_best: np.ndarray, optimizer: BO) -> OptiSol:
        """Store the optimization results."""
        status = "compensate (ok)"
        cavity_settings = self._create_set_of_cavity_settings(x_best, status)

        opti_sol: OptiSol = {
            "var": x_best,
            "cavity_settings": cavity_settings,
            "fun": optimizer.max["target"],
            "objectives": self._get_objective_values(x_best),
            "success": True,
        }
        return opti_sol

    def _format_bounds(self) -> dict[str, tuple[float, float]]:
        """Convert the :class:`.Variable` to a dict for bayes_opt."""
        return {f"x{i}": tuple(var.limits) for i, var in enumerate(self.variables)}

    def _norm_wrapper_residuals_bayes(self, **kwargs) -> float:
        """Wraps the objective for bayes_opt, mapping dict to array."""
        x = np.array([kwargs[f"x{i}"] for i in range(len(self.variables))])
        return -self._norm_wrapper_residuals(x)  # bayes_opt maximizes, so negate