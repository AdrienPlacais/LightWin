"""Define a factory function to create :class:`.OptimisationAlgorithm`.

.. todo::
    Docstrings

"""

import logging
from abc import ABCMeta
from collections.abc import Collection
from functools import partial
from typing import Any, Literal

from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.elements.element import Element
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.optimisation.algorithms.algorithm import OptimisationAlgorithm
from lightwin.optimisation.algorithms.bayesian_optimization import (
    BayesianOptimizationLW,
)
from lightwin.optimisation.algorithms.differential_evolution import (
    DifferentialEvolution,
)
from lightwin.optimisation.algorithms.downhill_simplex import DownhillSimplex
from lightwin.optimisation.algorithms.downhill_simplex_penalty import (
    DownhillSimplexPenalty,
)
from lightwin.optimisation.algorithms.explorator import Explorator
from lightwin.optimisation.algorithms.least_squares import LeastSquares
from lightwin.optimisation.algorithms.least_squares_penalty import (
    LeastSquaresPenalty,
)
from lightwin.optimisation.algorithms.simulated_annealing import (
    SimulatedAnnealing,
)
from lightwin.optimisation.design_space.design_space import DesignSpace
from lightwin.optimisation.objective.factory import ObjectiveFactory

#: Maps the ``optimisation_algorithm`` key in the ``TOML`` file to the actual
#: :class:`.OptimisationAlgorithm` we use.
ALGORITHM_SELECTOR: dict[str, ABCMeta] = {
    "bayesian_optimization": BayesianOptimizationLW,
    "differential_evolution": DifferentialEvolution,
    "downhill_simplex": DownhillSimplex,
    "downhill_simplex_penalty": DownhillSimplexPenalty,
    "experimental": BayesianOptimizationLW,
    "explorator": Explorator,
    "least_squares": LeastSquares,
    "least_squares_penalty": LeastSquaresPenalty,
    "nelder_mead": DownhillSimplex,
    "nelder_mead_penalty": DownhillSimplexPenalty,
    # "nsga": NSGA,
    "simulated_annealing": SimulatedAnnealing,
}

#: Implemented optimization algorithms.
ALGORITHMS_T = Literal[
    "bayesian_optimization",
    "differential_evolution",
    "downhill_simplex",
    "downhill_simplex_penalty",
    "experimental",
    "explorator",
    "least_squares",
    "least_squares_penalty",
    "nelder_mead",
    "nelder_mead_penalty",
    # "nsga",
    "simulated_annealing",
]


class OptimisationAlgorithmFactory:
    """Holds methods to easily create :class:`.OptimisationAlgorithm`."""

    def __init__(
        self,
        opti_method: ALGORITHMS_T,
        beam_calculator: BeamCalculator,
        reference_simulation_output: SimulationOutput,
        **wtf: Any,
    ) -> None:
        """Save properties common to every optimization algorithhm.

        Parameters
        ----------
        opti_method :
            Name of the desired optimisation algorithm.
        beam_calculator :
            Object that will be used to compute propagation of the beam.
        reference_simulation_output :
            Simulation of the nominal accelerator.
        kwargs :
            Other keyword arguments that will be passed to the
            :class:`.OptimisationAlgorithm`.

        """
        self._class = ALGORITHM_SELECTOR[opti_method]
        self._beam_calculator = beam_calculator
        self._wtf = wtf
        self._reference_simulation_output = reference_simulation_output

    def create(
        self,
        compensating_elements: Collection[Element],
        objective_factory: ObjectiveFactory,
        design_space: DesignSpace,
        subset_elts: ListOfElements,
    ) -> OptimisationAlgorithm:
        """Instantiate an optimisation algorithm for a given fault."""
        default_kwargs = self._make_default_kwargs(
            compensating_elements,
            objective_factory,
            design_space,
            subset_elts,
        )
        self._log_common_keys(self._wtf, default_kwargs)
        final_kwargs = {**default_kwargs, **self._wtf}
        algorithm = self._class(**final_kwargs)
        return algorithm

    def _make_default_kwargs(
        self,
        compensating_elements: Collection[Element],
        objective_factory: ObjectiveFactory,
        design_space: DesignSpace,
        subset_elts: ListOfElements,
    ) -> dict[str, Any]:
        """Build default arguments for :class:`.OptimisationAlgorithm`.

        The kwargs for :class:`.OptimisationAlgorithm` that are defined in
        :meth:`.Fault._optimisation_algorithms` will override the ones defined
        here.

        Returns
        -------
            A dictionary of keyword arguments for the initialisation of
            :class:`.OptimisationAlgorithm`.

        """
        compute_beam_propagation = partial(
            self._beam_calculator.run_with_this, elts=subset_elts
        )
        default_kwargs: dict[str, Any] = {
            "compensating_elements": compensating_elements,
            "objective_factory": objective_factory,
            "design_space": design_space,
            "compute_beam_propagation": compute_beam_propagation,
            "cavity_settings_factory": self._beam_calculator.cavity_settings_factory,
            "reference_simulation_output": self._reference_simulation_output,
        }
        return default_kwargs

    def _log_common_keys(
        self, user_kwargs: dict[str, Any], default_kwargs: dict[str, Any]
    ) -> None:
        """Log when user-provided and default kwargs overlap.

        Parameters
        ----------
        user_kwargs :
            kwargs as defined in the
            :meth:`.Fault._optimisation_algorithms` (they have precedence).
        default_kwargs :
            kwargs as defined in the `_optimisation_algorithm_kwargs` (they
            will be overriden as they are considered as "default" or "fallback"
            values).

        """
        overlap = user_kwargs.keys() & default_kwargs.keys()
        if not overlap:
            return
        logging.info(
            "Overlapping OptimisationAlgorithm kwargs detected:\n"
            f"{', '.join(overlap)}. User-provided values (from FaultScenario) "
            "will override defaults."
        )
