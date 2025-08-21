"""Define bayesian optimization algorithms."""

import logging
from typing import Any

import numpy as np
from bayes_opt import acquisition
from bayes_opt.bayesian_optimization import BayesianOptimization
from numpy.typing import NDArray

from lightwin.optimisation.algorithms.algorithm import (
    OptimisationAlgorithm,
    OptiSol,
)


class BayesianOptimizationLW(OptimisationAlgorithm):
    """Bayesian optimization algorithm.

    Under the hood, relies on :class:`bayes_opt.BayesianOptimization`.

    The keys defined in ``TOML`` key: ``optimisation_algorithm_kwargs`` are
    passed to :meth:`bayes_opt.BayesianOptimization.maximize`.

    Special keys:

    - ``"acquisition"`` table is used to set the acquisition function. See
      :meth:`.BayesianOptimizationLW.acquisition_function`.

    """

    supports_constraints = False

    def optimize(self) -> OptiSol:
        """Set up the optimization and solve the problem.

        Returns
        -------
            Gives list of solutions, corresponding objective, convergence
            violation if applicable, etc.

        """
        x_0, pbounds = self._format_variables()

        optimizer = BayesianOptimization(
            f=self._to_maximise,
            pbounds=pbounds,
            random_state=1,
            acquisition_function=self.acquisition_function(),
        )

        # Force evaluation at nominal working point
        optimizer.register(params=x_0, target=self._to_maximise(**x_0))

        optimizer.maximize(**self.optimisation_algorithm_kwargs)
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
        kwargs = {
            "init_points": 10,
            "n_iter": 500,
            "acquisition": {
                "acquisition_function": "UpperConfidenceBound",
                "kwargs": {"kappa": 10},
            },
        }
        return kwargs

    def _generate_opti_sol(self, result: dict[str, Any] | None) -> OptiSol:
        """Store the optimization results."""
        status = "compensate (ok)"
        if result is None:
            raise ValueError("Optimization failed.")

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

    def _format_variables(
        self,
    ) -> tuple[dict[str, float], dict[str, tuple[float, float]]]:
        """Map every variable name with its limits."""
        x_0 = {str(var): var.x_0 for var in self.variables}
        pbounds = {str(var): var.limits for var in self.variables}
        return x_0, pbounds

    def _to_numpy(self, **kwargs) -> NDArray:
        """Convert dict of variables to numpy array."""
        return np.array([kwargs[str(var)] for var in self.variables])

    def acquisition_function(self) -> acquisition.AcquisitionFunction | None:
        """Get acquisition function.

        .. todo::
           Allow for user-defined acquisition function.

        We use ``kwargs`` from the ``"acquisition"`` key. It can look like:

        .. code-block:: toml

            [wtf.optimisation_algorithm_kwargs]
            # arguments passed to `BayesianOptimization.maximize` method

            [wtf.optimisation_algorithm_kwargs.acquisition]
            # arguments used to define acquisition function
            # Name of a func in `bayes_opt.acquisition`:
            acquisition_name = "UpperConfidenceBound"
            # Kwargs passed to this function:
            kwargs = { kappa = 2.576, random_state = 42 }

        """
        acquisition_kwargs = self.optimisation_algorithm_kwargs.pop(
            "acquisition", None
        )
        if acquisition_kwargs is None:
            logging.info(
                "No `acquisition` key in `optimisation_algorithm_kwargs`. "
                "Using default acquisition function."
            )
            return

        acquisition_name = acquisition_kwargs.get("acquisition_function", None)
        if not hasattr(acquisition, acquisition_name):
            logging.error(
                "`acquisition` package from `bayes_opt` module does not have "
                f"an `acquisition_function` named {acquisition_name}. Using "
                "default instead."
            )
            return

        kwargs = acquisition_kwargs["kwargs"]
        acquisition_function = getattr(acquisition, acquisition_name)(**kwargs)
        return acquisition_function
