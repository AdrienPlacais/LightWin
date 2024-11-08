"""Define :class:`Explorator`, a module to explore the design space.

In order to be consistent with the ABC :class:`.OptimisationAlgorithm`,
it also returns the solution with the lowest residue value -- hence it is also
a "brute-force" optimisation algorithm.

.. todo::
    Make this class more robust. In particular: save all objectives (not just
    the norm), handle export when there is more than two variables, also save
    complementary data (e.g.: always save ``phi_s`` even it is not in the
    constraints nor variables).

.. todo::
    Allow for different number of points according to variable.

"""

from dataclasses import dataclass
from typing import Literal

import numpy as np

from lightwin.failures.set_of_cavity_settings import SetOfCavitySettings
from lightwin.optimisation.algorithms.algorithm import (
    ComputeConstraintsT,
    OptimisationAlgorithm,
    OptiSol,
)


@dataclass
class Explorator(OptimisationAlgorithm):
    """Method that tries all the possible solutions.

    Notes
    -----
    Very inefficient for optimisation. It is however useful to study a specific
    case.

    All the attributes but ``solution`` are inherited from the Abstract Base
    Class :class:`.OptimisationAlgorithm`.

    """

    supports_constraints = True
    compute_constraints: ComputeConstraintsT

    def __init__(self, *args, **kwargs) -> None:
        """Instantiate object."""
        return super().__init__(*args, **kwargs)

    def optimise(self) -> tuple[bool, SetOfCavitySettings | None, OptiSol]:
        """
        Set up the optimisation and solve the problem.

        Returns
        -------
        success : bool
            Tells if the optimisation algorithm managed to converge.
        optimized_cavity_settings : SetOfCavitySettings | None
            Best solution found by the optimization algorithm.
        info : OptiSol
            Gives list of solutions, corresponding objective, convergence
            violation if applicable, etc.

        """
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

        best_solution, best_objective = self._take_best_solution(
            variables_values,
            objectives_values,
            criterion="minimize norm of objective",
        )
        assert best_solution is not None
        assert best_objective is not None
        info: OptiSol = {
            "X": best_solution.tolist(),
            "F": best_objective.tolist(),
            "objectives_values": {},
        }

        optimized_cavity_settings = self._create_set_of_cavity_settings(
            np.array(info["X"])
        )
        self._finalize()
        return True, optimized_cavity_settings, info

    def _algorithm_parameters(self) -> dict:
        """Create the ``kwargs`` for the optimisation."""
        kwargs = {"n_points": 20}
        return kwargs

    def _generate_combinations(
        self, n_points: int = 10, **kwargs
    ) -> tuple[np.ndarray, np.ndarray]:
        """Generate all the possible combinations of the variables."""
        limits = []
        for var in self.variables:
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

    def _take_best_solution(
        self,
        variable_comb: np.ndarray,
        objectives_values: np.ndarray,
        criterion: Literal["minimize norm of objective",],
    ) -> tuple[np.ndarray | None, np.ndarray | None]:
        """Take the "best" of the calculated solutions.

        Parameters
        ----------
        variable_comb : numpy.ndarray
            All the set of variables (cavity parameters) that were tried.
        objectives_values : numpy.ndarray
            The values of the objective corresponding to ``variable_comb``.
        criterion : Literal['minimize norm of objective']
            Name of the criterion that will determine which solution is the
            "best". Only one is implemented for now, may add others in the
            future.

        Returns
        -------
        best_solution : numpy.ndarray | None
            "Best" solution.
        best_objective : numpy.ndarray | None
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
