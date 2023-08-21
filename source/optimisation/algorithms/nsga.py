#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 18 11:57:32 2023.

@author: placais

This module holds `NSGA`, a genetic algorithm for optimisation.

"""
from dataclasses import dataclass
from typing import Callable
import logging

import numpy as np

from pymoo.core.problem import ElementwiseProblem
from pymoo.core.algorithm import Algorithm
from pymoo.core.result import Result

from pymoo.optimize import minimize

from pymoo.algorithms.moo.nsga2 import NSGA2

from pymoo.termination.default import DefaultMultiObjectiveTermination

from pymoo.mcdm.pseudo_weights import PseudoWeights

from optimisation.algorithms.algorithm import OptimisationAlgorithm
from failures.set_of_cavity_settings import (SetOfCavitySettings,
                                             SingleCavitySettings)


@dataclass
class NSGA(OptimisationAlgorithm):
    """
    Non-dominated Sorted Genetic Algorithm, an algorithm handling constraints.

    All the attributes but `solution` are inherited from the Abstract Base
    Class `OptimisationAlgorithm`.

    """

    def __post_init__(self) -> None:
        """Set additional information."""
        self.supports_constraints = True

    def optimise(self) -> tuple[bool,
                                SetOfCavitySettings,
                                dict[str, list[float]]]:
        """
        Set up the optimisation and solve the problem.

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
        problem = MyElementwiseProblem(
            _wrapper_residuals=self._wrapper_residuals,
            **self._problem_arguments)

        algorithm = self._set_algorithm()
        termination = self._set_termination()

        result: Result = minimize(problem=problem,
                                  algorithm=algorithm,
                                  termination=termination,
                                  # seed=None,
                                  verbose=True,
                                  # display=None,
                                  # callback=None,
                                  # return_least_infeasible=False,
                                  # save_history=False,
                                  )
        success = True

        # add least squares solution
        x_0 = np.array([var.x_0 for var in self.variables])
        result.X = np.vstack((result.X, x_0))

        f, g = self._wrapper_residuals(x_0)
        result.F = np.vstack((result.F, f))
        # result.G.append(g)

        set_of_cavity_settings, info = self._best_solution(result)
        return success, set_of_cavity_settings, info

    @property
    def _problem_arguments(self) -> dict[str, int | np.ndarray]:
        """Gather arguments required for `ElementwiseProblem`."""
        kwargs = {'n_var': self._n_var,
                  'n_obj': self._n_obj,
                  'n_ieq_constr': self._n_ieq_constr,
                  'xl': self._xl,
                  'xu': self._xu}
        return kwargs

    @property
    def _n_var(self) -> int:
        """Number of variables."""
        return len(self.variables)

    @property
    def _n_obj(self) -> int:
        """Number of objectives."""
        logging.warning("Number of objectives manually set.")
        return 3

    @property
    def _n_ieq_constr(self) -> int:
        """Number of inequality constraints."""
        return sum([constraint.n_constraints
                    for constraint in self.constraints])

    @property
    def _xl(self) -> np.ndarray:
        """Return variables lower limits."""
        lower = [var.limits[0] for var in self.variables]
        return np.array(lower)

    @property
    def _xu(self) -> np.ndarray:
        """Return variables upper limits."""
        upper = [var.limits[1] for var in self.variables]
        return np.array(upper)

    def _wrapper_residuals(self, var: np.ndarray
                           ) -> tuple[np.ndarray, np.ndarray]:
        """Compute residuals from an array of variable values."""
        cav_settings = self._create_set_of_cavity_settings(var)
        simulation_output = self.compute_beam_propagation(cav_settings)

        objective = self.compute_residuals(simulation_output)
        constraints = self.compute_constraints(simulation_output)
        return np.abs(objective), constraints

    def _set_algorithm(self) -> Algorithm:
        """Set `pymoo`s `Algorithm` object."""
        algorithm = NSGA2()
        return algorithm

    def _set_termination(self) -> DefaultMultiObjectiveTermination:
        """Set the termination condition."""
        termination = DefaultMultiObjectiveTermination(n_max_gen=1000,
                                                       n_max_evals=10000,
                                                       xtol=1e-8,
                                                       ftol=1e-8)
        return termination

    def _create_set_of_cavity_settings(self, var: np.ndarray
                                       ) -> SetOfCavitySettings:
        """Transform the object given by NSGA to a generic object."""
        # set_of_cavity_settings = result.f
        # return set_of_cavity_settings
        # FIXME
        my_phi = list(var[:var.shape[0] // 2])
        my_ke = list(var[var.shape[0] // 2:])

        variable_names = [variable.name for variable in self.variables]

        if 'phi_s' in variable_names:
            my_set = [SingleCavitySettings(cavity=cavity,
                                           k_e=k_e,
                                           phi_s=phi,
                                           index=self.elts.index(cavity))
                      for cavity, k_e, phi in zip(self.compensating_cavities,
                                                  my_ke,
                                                  my_phi)]
        elif 'phi_0_abs' in variable_names:
            my_set = [SingleCavitySettings(cavity=cavity,
                                           k_e=k_e,
                                           phi_0_abs=phi,
                                           index=self.elts.index(cavity))
                      for cavity, k_e, phi in zip(self.compensating_cavities,
                                                  my_ke,
                                                  my_phi)]
        elif 'phi_0_rel' in variable_names:
            my_set = [SingleCavitySettings(cavity=cavity,
                                           k_e=k_e,
                                           phi_0_rel=phi,
                                           index=self.elts.index(cavity))
                      for cavity, k_e, phi in zip(self.compensating_cavities,
                                                  my_ke,
                                                  my_phi)]
        else:
            logging.critical("Error in the _create_set_of_cavity_settings")
            return None

        my_set = SetOfCavitySettings(my_set)
        return my_set

    def _best_solution(self, result: Result) -> tuple[SetOfCavitySettings,
                                                      dict[str, np.ndarray]]:
        """Take the "best" solution."""
        approx = _characteristic_points(result)

        n_f = (result.F - approx['ideal']) \
            / (approx['nadir'] - approx['ideal'])

        n_obj = len(self.objectives)
        weights = np.ones(n_obj) / n_obj
        idx_best = PseudoWeights(weights).do(n_f)

        set_of_cavity_settings = self._create_set_of_cavity_settings(
            result.X[idx_best])
        info = {'X': result.X[idx_best],
                'F': result.F[idx_best]}
        return set_of_cavity_settings, info

    def _format_variables_and_constraints(self) -> None:
        """Legacy?"""
        pass


class MyElementwiseProblem(ElementwiseProblem):
    """A first test implementation, eval single solution at a time."""

    def __init__(self,
                 _wrapper_residuals: Callable[np.ndarray, np.ndarray],
                 **kwargs: int | np.ndarray) -> None:
        """Create object."""
        self._wrapper_residuals = _wrapper_residuals
        super().__init__(**kwargs)

    def _evaluate(self, x: np.ndarray, out: dict[str, np.ndarray],
                  *args, **kwargs) -> dict[str, np.ndarray]:
        """Calculate and return the objectives."""
        out['F'], out['G'] = self._wrapper_residuals(x)
        return out


def _characteristic_points(result: Result) -> dict[str, np.ndarray]:
    """Give the ideal and Nadir points as a dict."""
    ideal_idx = result.F.argmin(axis=0)
    ideal = result.F.min(axis=0)

    ideal_idx_bis = result.F[:-1].argmin(axis=0)
    ideal_bis = result.F[:-1].min(axis=0)

    nadir_idx = result.F.argmax(axis=0)
    nadir = result.F.max(axis=0)

    logging.info(
        f"Manually added: idx {result.F.shape[0] - 1}\n"
        f"Ideal points are {ideal} (idx {ideal_idx})\n"
        f"(without manually added lsq: {ideal_bis} @ {ideal_idx_bis}\n"
        f"Nadir points are {nadir} (idx {nadir_idx})")
    approx = {'ideal': ideal,
              'nadir': nadir}
    return approx
