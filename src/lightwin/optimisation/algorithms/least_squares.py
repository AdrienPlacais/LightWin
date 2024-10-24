"""Define :class:`LeastSquares`, a simple and fast optimisation method."""

import logging
from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, least_squares

from lightwin.failures.set_of_cavity_settings import SetOfCavitySettings
from lightwin.optimisation.algorithms.algorithm import (
    OptiInfo,
    OptimisationAlgorithm,
)


@dataclass
class LeastSquares(OptimisationAlgorithm):
    """Plain least-squares method, efficient for small problems.

    Notes
    -----
    Works very well with :class:`.Envelope1D`, has issues converging with
    :class:`.TraceWin`.

    All the attributes but ``solution`` are inherited from the Abstract Base
    Class :class:`.OptimisationAlgorithm`.

    See also
    --------
    :class:`.LeastSquaresPenalty`

    """

    supports_constraints = False

    def __init__(self, *args, **kwargs) -> None:
        """Instantiate object."""
        return super().__init__(*args, **kwargs)

    def optimise(
        self,
        keep_history: bool = False,
        save_history: bool = False,
    ) -> tuple[bool, SetOfCavitySettings | None, OptiInfo]:
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
        if keep_history or save_history:
            raise NotImplementedError
        x_0, bounds = self._format_variables()

        solution = least_squares(
            fun=self._wrapper_residuals,
            x0=x_0,
            bounds=bounds,
            **self.optimisation_algorithm_kwargs,
        )

        self.solution = solution
        optimized_cavity_settings = self._create_set_of_cavity_settings(
            solution.x
        )
        # TODO: output some info could be much more clear by using the __str__
        # methods of the various objects.

        objectives_values = self._get_objective_values()
        self._output_some_info(objectives_values)

        success = self.solution.success
        info = {
            "X": self.solution.x.tolist(),
            "F": self.solution.fun.tolist(),
            "objectives_values": objectives_values,
        }
        return success, optimized_cavity_settings, info

    @property
    def _default_kwargs(self) -> dict:
        """Create the ``kwargs`` for the optimisation."""
        kwargs = {
            "jac": "2-point",  # Default
            # 'trf' not ideal as jac is not sparse. 'dogbox' may have
            # difficulties with rank-defficient jacobian.
            "method": "dogbox",
            "ftol": 1e-10,
            "gtol": 1e-8,
            "xtol": 1e-8,
            # 'x_scale': 'jac',
            # 'loss': 'arctan',
            "diff_step": None,
            "tr_solver": None,
            "tr_options": {},
            "jac_sparsity": None,
            "verbose": 0,
        }
        return kwargs

    def _format_variables(self) -> tuple[np.ndarray, Bounds]:
        """Convert the :class:`.Variable` to an array and ``Bounds``."""
        x_0 = np.array([var.x_0 for var in self.variables])
        _bounds = np.array([var.limits for var in self.variables])
        bounds = Bounds(_bounds[:, 0], _bounds[:, 1])
        return x_0, bounds

    def _output_some_info(self, objectives_values: dict[str, float]) -> None:
        """Show the most useful data from scipy's `least_squares`."""
        sol = self.solution
        info_string = "Objective functions results:\n"
        for i, fun in enumerate(objectives_values.values()):
            info_string += f"{i}: {' ':>35} | {fun}\n"
        info_string += f"Norm: {sol.fun}"
        logging.info(info_string)
        info_string = "least_squares algorithm output:"
        info_string += f"\nmessage: {sol.message}\n"
        info_string += f"nfev: {sol.nfev}\tnjev: {sol.njev}\n"
        info_string += f"optimality: {sol.optimality}\nstatus: {sol.status}\n"
        info_string += f"success: {sol.success}\nsolution: {sol.x}\n"
        logging.debug(info_string)
