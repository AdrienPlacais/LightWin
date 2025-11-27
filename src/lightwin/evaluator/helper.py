"""Provide evaluator helpers."""

import logging
from collections.abc import Sequence
from functools import partial
from typing import Callable

import numpy as np

from lightwin.evaluator.types import ref_value_t, value_t


# =============================================================================
# Helpers
# =============================================================================
def need_to_resample(value: value_t, ref_value: ref_value_t) -> bool:
    """Determine if we need to resample ``value`` or ``ref_value``."""
    if isinstance(value, float) or isinstance(ref_value, float):
        return False
    assert isinstance(value, np.ndarray) and isinstance(ref_value, np.ndarray)
    if value.shape == () or ref_value.shape == ():
        return False
    if value.shape == ref_value.shape:
        return False
    return True


def return_value_should_be_plotted(partial_function: Callable) -> bool:
    """Determine if keyword 'to_plot' was passed and is True.

    This function only works on functions defined by ``functools.partial``. If
    it is not (lambda function, "classic" function), we consider that the
    plotting was not desired.
    We check if the 'to_plot' keyword was given in the partial definition, and
    if it is not we also consider that the plot was not wanted.

    """
    if not isinstance(partial_function, partial):
        return False

    keywords = partial_function.keywords
    if "to_plot" not in keywords:
        return False

    return keywords["to_plot"]


def limits_given_in_functoolspartial_args(
    partial_function: Callable,
) -> Sequence[np.ndarray | float]:
    """Extract the limits given to a test function."""
    if not isinstance(partial_function, partial):
        logging.error("Given function must be a functools.partial func.")
        return (np.nan, np.nan)

    keywords = partial_function.keywords
    if "limits" in keywords:
        return keywords["limits"]

    limits = [
        keywords[key]
        for key in keywords.keys()
        if key in ["lower_limit", "upper_limit", "objective_value"]
    ]
    assert len(limits) in (1, 2)
    return tuple(limits)
