"""Define :class:`Explorator`, a module to explore the design space.

In order to be consistent with the ABC :class:`.OptimisationAlgorithm`,
it also returns the solution with the lowest residual value -- hence it is also
a "brute-force" optimisation algorithm.

.. todo::
    Make this class more robust. In particular: save all objectives (not just
    the norm), handle export when there is more than two variables, also save
    complementary data (e.g.: always save ``phi_s`` even it is not in the
    constraints nor variables).

.. todo::
    Allow for different number of points according to variable.

"""

import logging
from typing import Literal

import numpy as np

from lightwin.optimisation.algorithms.algorithm import (
    ComputeConstraintsT,
    OptimisationAlgorithm,
    OptiSol,
)


class Explorator(OptimisationAlgorithm):
    """Method that tries all the possible solutions.

    Notes
    -----
    Very inefficient for optimization. It is however useful to study a specific
    case.

    All the attributes but ``solution`` are inherited from the Abstract Base
    Class :class:`.OptimisationAlgorithm`.

    """

    supports_constraints = True
    compute_constraints: ComputeConstraintsT

    def optimize(self) -> OptiSol:
        """Set up the optimization and solve the problem.

        Returns
        -------
            Gives list of solutions, corresponding objective, convergence
            violation if applicable, etc.

        """
        if self.n_var != 2:
            logging.warning("I think this algo only works with 2 vars")
        kwargs = self._algorithm_parameters()

        _, variables_values = self._generate_combinations(**kwargs)
        results = [self._wrapper_residuals(var) for var in variables_values]
        objectives_values = np.array([res[0] for res in results])
        constraints_values = np.array([res[1] for res in results])

        # objectives_as_mesh = self._array_of_values_to_mesh(
        #     objectives_values, **kwargs
        # )
        # constraints_as_mesh = self._array_of_values_to_mesh(
        #     constraints_values, **kwargs
        # )

        self.opti_sol = self._generate_opti_sol(
            variables_values,
            objectives_values,
            criterion="minimize norm of objective",
        )
        self._finalize(self.opti_sol)
        return self.opti_sol

    def _algorithm_parameters(self) -> dict:
        """Create the ``kwargs`` for the optimisation."""
        kwargs = {"n_points": 20}
        return kwargs

    def _generate_combinations(
        self, n_points: int = 10, **kwargs
    ) -> tuple[np.ndarray, np.ndarray]:
        """Generate all the possible combinations of the variables."""
        limits = []
        for var in self._variables:
            lim = (var.limits[0], var.limits[1])

            if "phi" in var.name and lim[1] - lim[0] >= 2.0 * np.pi:
                lim = (0.0, 2.0 * np.pi)
            limits.append(lim)

        variables_values = [
            np.linspace(lim[0], lim[1], n_points) for lim in limits
        ]
        variables_mesh = np.array(
            np.meshgrid(*variables_values, indexing="ij")
        )
        variables_combinations = np.concatenate(variables_mesh.T)
        return variables_mesh, variables_combinations

    def _array_of_values_to_mesh(
        self, objectives_values: np.ndarray, n_points: int = 10, **kwargs
    ) -> np.ndarray:
        """Reformat the results for plotting purposes."""
        return objectives_values.reshape((n_points, n_points)).T

    def _generate_opti_sol(
        self,
        variables_values: np.ndarray,
        objectives_values: np.ndarray,
        criterion: Literal["minimize norm of objective",],
    ) -> OptiSol:
        """Create the dictionary holding all relatable information."""
        var, fun = self._take_best_solution(
            variables_values, objectives_values, criterion
        )
        assert var is not None
        assert fun is not None

        cavity_settings = self._create_set_of_cavity_settings(var)
        opti_sol: OptiSol = {
            "var": var,
            "cavity_settings": cavity_settings,
            "fun": fun,
            "objectives": self._get_objective_values(var),
            "success": True,
            "info": ["Explorator"],
        }
        return opti_sol

    def _take_best_solution(
        self,
        variable_comb: np.ndarray,
        objectives_values: np.ndarray,
        criterion: Literal["minimize norm of objective",],
    ) -> tuple[np.ndarray | None, np.ndarray | None]:
        """Take the "best" of the calculated solutions.

        Parameters
        ----------
        variable_comb :
            All the set of variables (cavity parameters) that were tried.
        objectives_values :
            The values of the objective corresponding to ``variable_comb``.
        criterion :
            Name of the criterion that will determine which solution is the
            "best". Only one is implemented for now, may add others in the
            future.

        Returns
        -------
        best_solution :
            "Best" solution.
        best_objective :
            Objective values corresponding to ``best_solution``.

        """
        if criterion == "minimize norm of objective":
            norm_of_objective = objectives_values
            if len(norm_of_objective.shape) > 1:
                norm_of_objective = np.linalg.norm(norm_of_objective, axis=1)
            best_idx = np.nanargmin(norm_of_objective)
            best_solution = variable_comb[best_idx]
            best_objective = objectives_values[best_idx]
            return best_solution, best_objective
