"""Define a factory function to create :class:`.OptimisationAlgorithm`.

.. todo::
    Docstrings

"""

import logging
from abc import ABCMeta
from functools import partial
from typing import Any, Callable, Literal

from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.core.elements.field_maps.cavity_settings_factory import (
    CavitySettingsFactory,
)
from lightwin.failures.fault import Fault
from lightwin.optimisation.algorithms.algorithm import OptimisationAlgorithm
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
from lightwin.optimisation.algorithms.nsga import NSGA

ALGORITHM_SELECTOR: dict[str, ABCMeta] = {
    "least_squares": LeastSquares,
    "least_squares_penalty": LeastSquaresPenalty,
    "nsga": NSGA,
    "downhill_simplex": DownhillSimplex,
    "downhill_simplex_penalty": DownhillSimplexPenalty,
    "nelder_mead": DownhillSimplex,
    "nelder_mead_penalty": DownhillSimplexPenalty,
    "differential_evolution": DifferentialEvolution,
    "explorator": Explorator,
    "experimental": Explorator,
}  #:
ALGORITHMS_T = Literal[
    "least_squares",
    "least_squares_penalty",
    "nsga",
    "downhill_simplex",
    "downhill_simplex_penalty",
    "nelder_mead",
    "nelder_mead_penalty",
    "differential_evolution",
    "explorator",
    "experimental",
]


def optimisation_algorithm_factory(
    opti_method: ALGORITHMS_T,
    fault: Fault,
    beam_calculator: BeamCalculator,
    **wtf: Any,
) -> OptimisationAlgorithm:
    """Create the proper :class:`.OptimisationAlgorithm` instance.

    Parameters
    ----------
    opti_method : str
        Name of the desired optimisation algorithm.
    fault : Fault
        Fault that will be compensated by the optimisation algorithm.
    beam_calculator : BeamCalculator
        Object that will be used to computte propagation of the beam.
    kwargs :
        Other keyword arguments that will be passed to the
        :class:`.OptimisationAlgorithm`.

    Returns
    -------
    algorithm : OptimisationAlgorithm
        Instantiated optimisation algorithm.

    """
    default_kwargs = _default_kwargs(
        fault,
        beam_calculator.run_with_this,
        beam_calculator.cavity_settings_factory,
    )
    _check_common_keys(wtf, default_kwargs)
    final_kwargs = default_kwargs | wtf

    algorithm_base_class = ALGORITHM_SELECTOR[opti_method]
    algorithm = algorithm_base_class(**final_kwargs)
    return algorithm


def _default_kwargs(
    fault: Fault,
    run_with_this: Callable,
    cavity_settings_factory: CavitySettingsFactory,
) -> dict[str, Any]:
    """Set default arguments to instantiate the optimisation algorithm.

    The kwargs for :class:`.OptimisationAlgorithm` that are defined in
    :meth:`.FaultScenario._set_optimisation_algorithms` will override the ones
    defined here.

    Parameters
    ----------
    fault : Fault
        Fault that will be compensated by the optimisation algorithm.
    compute_beam_propagation : Callable
        Function that takes in a set of cavity settings and a list of elements,
        computes the beam propagation with these, and returns a simulation
        output.

    Returns
    -------
    default_kwargs : dict[str, Any]
        A dictionary of keyword arguments for the initialisation of
        :class:`.OptimisationAlgorithm`.

    """
    compute_beam_propagation = partial(run_with_this, elts=fault.elts)
    default_kwargs: dict[str, Any] = {
        "compensating_elements": fault.compensating_elements,
        "elts": fault.elts,
        "objectives": fault.objectives,
        "variables": fault.variables,
        "compute_beam_propagation": compute_beam_propagation,
        "compute_residuals": fault.compute_residuals,
        "constraints": fault.constraints,
        "compute_constraints": fault.compute_constraints,
        "cavity_settings_factory": cavity_settings_factory,
        "reference_simulation_output": fault.reference_simulation_output,
    }
    return default_kwargs


def _check_common_keys(
    user_kwargs: dict[str, Any], default_kwargs: dict[str, Any]
) -> None:
    """Check keys that are common between the two dictionaries.

    .. todo::
        Redocument ``default_kwargs``.

    Parameters
    ----------
    user_kwargs : dict[str, Any]
        kwargs as defined in the
        :meth:`.FaultScenario._set_optimisation_algorithms` (they have
        precedence).
    default_kwargs : [str, Any]
        kwargs as defined in the `_optimisation_algorithm_kwargs` (they
        will be overriden as they are considered as "default" or "fallback"
        values).

    """
    user_keys = set(user_kwargs.keys())
    default_keys = set(default_kwargs.keys())
    common_keys = user_keys.intersection(default_keys)
    if len(common_keys) > 0:
        logging.info(
            "The following OptimisationAlgorithm arguments are set both in "
            "FaultScenario (user_kwargs) and in "
            "optimisation.algorithms.factory (default_kwargs). We use the ones"
            f" from FaultScenario.\n{common_keys = })"
        )
