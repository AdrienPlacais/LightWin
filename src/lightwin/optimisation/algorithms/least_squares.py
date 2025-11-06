"""Define :class:`LeastSquares`, a simple and fast optimization method."""

from scipy.optimize import least_squares

from lightwin.optimisation.algorithms.algorithm import OptiSol
from lightwin.optimisation.algorithms.downhill_simplex import DownhillSimplex


class LeastSquares(DownhillSimplex):
    """Plain least-squares method, efficient for small problems.

    See also
    --------
    :class:`.LeastSquaresPenalty`

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
        result = least_squares(
            fun=self._wrapper_residuals,
            x0=x_0,
            bounds=bounds,
            **self.optimisation_algorithm_kwargs,
        )
        self.opti_sol = self._generate_opti_sol(result)
        self._finalize(self.opti_sol)
        return self.opti_sol

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
