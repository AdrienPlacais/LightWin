"""Define :class:`DifferentialEvolution`."""

from scipy.optimize import differential_evolution

from lightwin.optimisation.algorithms.algorithm import OptiSol
from lightwin.optimisation.algorithms.downhill_simplex import DownhillSimplex


class DifferentialEvolution(DownhillSimplex):
    """Differential evolution method, which does not use derivatives.

    .. warning::
        This method was not tuned for this problem yet.

    """

    supports_constraints = False

    def optimize(self) -> OptiSol:
        """Set up the optimisation and solve the problem.

        Returns
        -------
            Gives list of solutions, corresponding objective, convergence
            violation if applicable, etc.

        """
        kwargs = self._algorithm_parameters()
        x_0, bounds = self._format_variables()

        result = differential_evolution(
            func=self._norm_wrapper_residuals, x0=x_0, bounds=bounds, **kwargs
        )
        self.opti_sol = self._generate_opti_sol(result)
        complementary_info = ("Differential Evolution", result.message)
        self._finalize(self.opti_sol, *complementary_info)
        return self.opti_sol

    def _algorithm_parameters(self) -> dict:
        """Create the ``kwargs`` for the optimisation."""
        kwargs = {
            "disp": True,
        }
        return kwargs
