"""Define equation solvers.

For now, used only in acceptance computations.

"""

import logging
from typing import Callable

import numpy as np
from scipy.optimize import brentq


def solve_scalar_equation_brent(
    func: Callable[[float, float], float],
    param_value: float,
    x_bounds: tuple[float, float],
    warning: bool = True,
) -> float:
    """
    Solve a scalar equation for multiple parameters using Brent's method.

    Parameters
    ----------
    func
        Function f(x, param) whose root is to be found for each parameter.
    param_value
        Single parameter value to use when solving the equation.
    x_bounds
        Interval (x_min, x_max) in which to search for the root.
        The bounds will be swapped if provided in reverse order.
    warning
        If True (default), warnings are issued for empty inputs, range inversion,
        or missing roots in the interval.

    Returns
    -------
    float
        Root found for the parameter value. NaN if no root is found.
    """

    x_left, x_right = x_bounds
    if x_left > x_right:
        x_left, x_right = x_right, x_left
        if warning:
            logging.warning(
                f"The range ({x_bounds[0]}, {x_bounds[1]}) is inverted. "
                f"It has been corrected to ({x_left}, {x_right})."
            )
    f = lambda x: func(x, param_value)

    if f(x_left) * f(x_right) > 0:
        solution = np.nan
        if warning:
            logging.warning(
                f"{f(x_left)} and {f(x_right)} have the same sign in solve_scalar_equation_brent(). "
                "There is no root in this range"
            )
            return solution
    try:
        solution = brentq(f, x_left, x_right)

    except (ValueError, RuntimeError) as e:
        solution = np.nan
        if warning:
            logging.warning(
                f"Root finding failed in solve_scalar_equation_brent() with param={param_value}: {e}"
            )

    return solution
