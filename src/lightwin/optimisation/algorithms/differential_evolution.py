"""Define :class:`DifferentialEvolution`."""

import logging
from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, differential_evolution

from lightwin.failures.set_of_cavity_settings import SetOfCavitySettings
from lightwin.optimisation.algorithms.algorithm import OptimisationAlgorithm


@dataclass
class DifferentialEvolution(OptimisationAlgorithm):
    """
    Downhill simplex method, which does not use derivatives.

    All the attributes but ``solution`` are inherited from the Abstract Base
    Class :class:`.OptimisationAlgorithm`.

    """

    def __post_init__(self) -> None:
        """Set additional information."""
        super().__post_init__()
        self.supports_constraints = False

    def optimise(
        self,
    ) -> tuple[bool, SetOfCavitySettings, dict[str, list[float]]]:
        """Set up the optimisation and solve the problem.

        Returns
        -------
        success : bool
            Tells if the optimisation algorithm managed to converge.
        optimized_cavity_settings : SetOfCavitySettings
            Best solution found by the optimization algorithm.
        info : dict[str, list[float]]] | None
            Gives list of solutions, corresponding objective, convergence
            violation if applicable, etc.

        """
        kwargs = self._algorithm_parameters()
        x_0, bounds = self._format_variables()

        solution = differential_evolution(
            func=self._norm_wrapper_residuals, x0=x_0, bounds=bounds, **kwargs
        )

        self.solution = solution
        optimized_cavity_settings = self._create_set_of_cavity_settings(
            solution.x
        )
        # TODO: output some info could be much more clear by using the __str__
        # methods of the various objects.

        self._output_some_info()

        success = self.solution.success
        info = {
            "X": self.solution.x.tolist(),
            "F": self.solution.fun.tolist(),
        }
        return success, optimized_cavity_settings, info

    def _algorithm_parameters(self) -> dict:
        """Create the ``kwargs`` for the optimisation."""
        kwargs = {
            "disp": True,
        }
        return kwargs

    def _format_variables(self) -> tuple[np.ndarray, Bounds]:
        """Convert the :class:`.Variable` to an array and ``Bounds``."""
        x_0 = np.array([var.x_0 for var in self.variables])
        _bounds = np.array([var.limits for var in self.variables])
        bounds = Bounds(_bounds[:, 0], _bounds[:, 1])
        return x_0, bounds

    def _output_some_info(self) -> None:
        """Show the most useful data from least_squares."""
        sol = self.solution
        info_string = "Objective functions results:\n"
        objectives = self._wrapper_residuals(sol.x)
        for i, fun in enumerate(objectives):
            info_string += f"{i}: {' ':>35} | {fun}\n"
        info_string += f"Norm: {sol.fun}"
        logging.info(info_string)
        info_string = "Nelder-Mead algorithm output:"
        info_string += f"\nmessage: {sol.message}\n"
        # info_string += f"nfev: {sol.nfev}\tnjev: {sol.njev}\n"
        # info_string += f"optimality: {sol.optimality}\nstatus: {sol.status}\n"
        info_string += f"success: {sol.success}\nsolution: {sol.x}\n"
        logging.debug(info_string)
