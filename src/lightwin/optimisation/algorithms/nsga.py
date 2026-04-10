"""Define the NSGA-III many-objective optimisation algorithm."""

import logging
import os
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from math import comb
from typing import Any

import numpy as np
from numpy.typing import NDArray
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.core.problem import Problem
from pymoo.core.result import Result
from pymoo.optimize import minimize as pymoo_minimize
from pymoo.util.ref_dirs import get_reference_directions

from lightwin.optimisation.algorithms.algorithm import (
    OptimisationAlgorithm,
    OptiSol,
)


class _LightWinProblem(Problem):
    """Wrap LightWin's residual evaluation into a pymoo :class:`.Problem`."""

    def __init__(
        self,
        n_var: int,
        n_obj: int,
        n_constr: int,
        xl: NDArray[np.float64],
        xu: NDArray[np.float64],
        eval_fn: Callable,
        **kwargs,
    ) -> None:
        """Init the object.

        Parameters
        ----------
        n_var :
            Number of variables.
        n_obj :
            Number of objectives.
        n_constr :
            Number of constraints.
        xl :
            ``(n_var, )`` array of lower limits for variables.
        xu :
            ``(n_var, )`` array of upper limits for variables.
        eval_fn :
            Residue function.

        """
        super().__init__(
            n_var=n_var,
            n_obj=n_obj,
            n_ieq_constr=n_constr,
            xl=xl,
            xu=xu,
            **kwargs,
        )
        self._eval_fn = eval_fn

    def _evaluate(
        self,
        x: NDArray[np.float64],
        out: dict[str, NDArray[np.float64]],
        *args,
        **kwargs,
    ) -> None:
        """Evaluate objectives (and constraints) for a batch of individuals.

        Parameters
        ----------
        x :
            ``(n_var, )`` array of variables.
        out :
            Dictionary keeping track of objectives, constraint violation, etc.

        """
        results = [self._eval_fn(xi) for xi in x]
        out["F"] = np.array([r[0] for r in results])
        if self.n_ieq_constr > 0:
            out["G"] = np.array([r[1] for r in results])


class NSGA3Algorithm(OptimisationAlgorithm):
    """NSGA-III many-objective optimisation algorithm, powered by pymoo.

    Suitable for problems with 4+ objectives. Uses structured reference points
    on a Das-Dennis simplex lattice to maintain diversity across the Pareto
    front.

    All attributes but ``solution`` are inherited from
    :class:`.OptimisationAlgorithm`.

    See also
    --------
    pymoo.algorithms.moo.nsga3.NSGA3

    """

    supports_constraints = True

    def optimize(self) -> OptiSol:
        """Set up the optimisation and solve the problem.

        Returns
        -------
            Gives list of solutions, corresponding objectives, constraint
            violations if applicable, etc.

        """
        problem = self._problem()

        kw = self.optimisation_algorithm_kwargs
        ref_dirs = get_reference_directions(
            "das-dennis", self.n_obj, n_partitions=kw["n_partitions"]
        )

        algorithm = NSGA3(ref_dirs=ref_dirs, pop_size=kw["pop_size"])

        result = pymoo_minimize(
            problem,
            algorithm,
            termination=("n_gen", kw["n_gen"]),
            verbose=True,
        )

        self.opti_sol = self._generate_opti_sol(result)
        self._finalize(self.opti_sol)
        return self.opti_sol

    @property
    def _default_kwargs(self) -> dict[str, Any]:
        """Compute sensible NSGA-III defaults from the problem dimensions.

        ``n_partitions`` is the smallest value that yields at least
        ``_MIN_REF_DIRS`` Das-Dennis reference directions, ensuring enough
        diversity pressure across the Pareto front.

        ``pop_size`` is set to the number of reference directions (the natural
        lower bound for NSGA-III) rounded up to the nearest hundred.

        ``n_gen`` scales with the number of variables: more variables generally
        need more generations to converge.

        """
        _MIN_REF_DIRS = max(50, 10 * self.n_obj)
        n_partitions = next(
            p
            for p in range(1, 500)
            if comb(self.n_obj + p - 1, p) >= _MIN_REF_DIRS
        )
        n_ref_dirs = comb(self.n_obj + n_partitions - 1, n_partitions)

        pop_size = int(np.ceil(n_ref_dirs / 100) * 100)
        n_gen = 50 * self.n_var

        return {
            "n_partitions": n_partitions,
            "pop_size": pop_size,
            "n_gen": n_gen,
        }

    def _evaluate_individual(
        self, var: NDArray[np.float64]
    ) -> tuple[NDArray[np.float64], NDArray[np.float64] | None]:
        """Evaluate objectives and constraints for a single individual.

        Mirrors the logic of :meth:`.OptimisationAlgorithm._wrapper_residuals`
        but also returns constraint values so that a single beam propagation
        call covers both, avoiding redundant simulations.

        Parameters
        ----------
        var :
            Array of variable values for one candidate solution.

        Returns
        -------
        residuals :
            Objective values.
        constraints :
            Constraint values (``<= 0`` means feasible), or ``None`` if no
            constraints are defined.

        """
        objectives, constraints = self._evaluate_solution(var)
        residuals = np.array(list(objectives.values()))
        constraints_arr = (
            np.array(list(constraints.values()))
            if constraints is not None
            else None
        )
        return residuals, constraints_arr

    def _generate_opti_sol(self, result: Result) -> OptiSol:
        """Pick the best solution from the Pareto front and format it.

        "Best" is defined as the Pareto-front member with the smallest
        Euclidean norm of its objective vector - a reasonable neutral choice
        when no preference ordering over objectives is specified.

        Parameters
        ----------
        result :
            The pymoo :class:`~pymoo.core.result.Result` object returned by
            :func:`~pymoo.optimize.minimize`.

        """
        if result.X is None:
            x_best = np.array([var.x_0 for var in self._variables])
            funs = np.full(self.n_obj, np.nan)
            success = False
            message = "No feasible solution found by NSGA-III."
        else:
            norms = np.linalg.norm(result.F, axis=1)
            best_idx = int(np.argmin(norms))
            x_best = result.X[best_idx]
            funs = result.F[best_idx]
            success = True
            message = (
                f"NSGA-III converged. "
                f"Pareto front contains {len(result.X)} solution(s)."
            )

        cavity_settings = self._to_cavity_settings(x_best)
        objectives, _ = self._evaluate_solution(x_best)

        opti_sol: OptiSol = {
            "var": x_best,
            "cavity_settings": cavity_settings,
            "fun": funs,
            "objectives": objectives,
            "success": success,
            "info": [self.__class__.__name__, message],
        }
        return opti_sol

    def _problem(self) -> _LightWinProblem:
        """Create a single-threaded problem."""
        xl, xu = self._format_variables()
        return _LightWinProblem(
            n_var=self.n_var,
            n_obj=self.n_obj,
            n_constr=self.n_constr,
            xl=xl,
            xu=xu,
            eval_fn=self._evaluate_individual,
        )

    def _format_variables(
        self,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Extract lower and upper bounds from :class:`.Variable` objects."""
        bounds = np.array([var.limits for var in self._variables])
        return bounds[:, 0], bounds[:, 1]


# =============================================================================
# Multi-threaded versions
# =============================================================================
class _LightWinProblemMulti(_LightWinProblem):
    """Wrap LightWin's residual evaluation into a pymoo Problem."""

    def __init__(self, *args, n_workers=1, **kwargs) -> None:
        """Set a number of CPU cores."""
        super().__init__(*args, **kwargs)
        self._n_workers = n_workers

    def _evaluate(
        self,
        x: NDArray[np.float64],
        out: dict[str, NDArray[np.float64]],
        *args,
        **kwargs,
    ) -> None:
        """Evaluate a batch of individuals, optionally in parallel."""
        if self._n_workers == 1:
            return super()._evaluate(x, out, *args, **kwargs)

        results: list[list[float] | None]
        results = [None] * len(x)
        with ThreadPoolExecutor(max_workers=self._n_workers) as pool:
            futures = {
                pool.submit(self._eval_fn, xi): i for i, xi in enumerate(x)
            }
            for future in as_completed(futures):
                results[futures[future]] = future.result()

        out["F"] = np.array([r[0] for r in results])
        if self.n_ieq_constr > 0:
            out["G"] = np.array([r[1] for r in results])


class NSGA3AlgorithmMulti(NSGA3Algorithm):
    """NSGA-III many-objective optimisation algorithm, powered by pymoo.

    Suitable for problems with 4+ objectives. Uses structured reference points
    on a Das-Dennis simplex lattice to maintain diversity across the Pareto
    front.

    All attributes but ``solution`` are inherited from
    :class:`.OptimisationAlgorithm`.

    See also
    --------
    pymoo.algorithms.moo.nsga3.NSGA3

    """

    def __init__(self, *args, **kwargs) -> None:
        """Create object.

        Also set ``_history_lock``, which guards history writes, as they are
        not thread-safe.

        """
        super().__init__(*args, **kwargs)
        self._history_lock = threading.Lock()

    @property
    def _default_kwargs(self) -> dict[str, Any]:
        _MIN_REF_DIRS = max(50, 10 * self.n_obj)
        n_partitions = next(
            p
            for p in range(1, 500)
            if comb(self.n_obj + p - 1, p) >= _MIN_REF_DIRS
        )
        n_ref_dirs = comb(self.n_obj + n_partitions - 1, n_partitions)
        return {
            "n_partitions": n_partitions,
            "pop_size": int(np.ceil(n_ref_dirs / 100) * 100),
            "n_gen": 50 * self.n_var,
            "n_workers": os.cpu_count(),
        }

    def _evaluate_individual(
        self, var: NDArray[np.float64]
    ) -> tuple[NDArray[np.float64], NDArray[np.float64] | None]:
        """Evaluate one candidate — thread-safe via lock on history writes.

        The simulation runs outside the lock (fully parallel). History writes
        are batched and serialised via ``_history_lock``.

        """
        raise NotImplementedError
        cav_settings = self._to_cavity_settings(var)
        simulation_output = self.compute_beam_propagation(cav_settings)

        residuals = self._compute_residuals(simulation_output)
        objectives = {
            str(objective): value
            for objective, value in zip(
                self.objectives, residuals, strict=True
            )
        }

        constraints = None
        constraints_arr = None
        if self.n_constr > 0:
            constraints = {}
            for constraint in self._constraints:
                value = constraint.get_value(simulation_output)
                if not np.isnan(constraint.x_min):
                    constraints[f"{constraint} (lower)"] = float(
                        constraint.x_min - value
                    )
                if not np.isnan(constraint.x_max):
                    constraints[f"{constraint} (upper)"] = float(
                        value - constraint.x_max
                    )
            constraints_arr = np.array(list(constraints.values()))

        with self._history_lock:
            self.history.add_settings(var)
            self.history.add_objective_values(
                list(residuals), simulation_output
            )
            if constraints is not None:
                self.history.add_constraint_values(list(constraints.values()))
            self.history.checkpoint()

        return residuals, constraints_arr

    def _problem(self) -> _LightWinProblemMulti:
        """Create a multi-threaded problem."""
        xl, xu = self._format_variables()
        return _LightWinProblemMulti(
            n_var=self.n_var,
            n_obj=self.n_obj,
            n_constr=self.n_constr,
            xl=xl,
            xu=xu,
            eval_fn=self._evaluate_individual,
            n_workers=self.optimisation_algorithm_kwargs["n_workers"],
        )
