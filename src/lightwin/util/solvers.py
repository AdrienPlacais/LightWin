"Gives useful functions used to compute acceptances"

from scipy.optimize import brentq
from typing import Callable
import logging

import numpy as np

def is_in_range(array: np.ndarray, range: tuple[float, float], warning: bool = True) -> np.ndarray:
    """
    Check which elements of an array are outside a specified numerical range.

    Parameters
    ----------
    array : np.ndarray
        Array of numeric values to validate.
    range : tuple[float, float]
        Tuple specifying the lower and upper bounds of the accepted range (inclusive).
        If the bounds are given in reverse order, they will be corrected automatically.
    warning : bool, optional
        If True (default), warnings are issued for empty input, range inversion,
        and out-of-range elements.

    Returns
    -------
    np.ndarray
        Boolean array where True indicates values that are outside the specified range.
        NaN values are ignored (returned as False).
    """

    if array.size == 0 and warning:
        logging.warning("The input array of is_in_range() is empty. The result will also be an empty boolean array.")
    range_left, range_right = range
    if range_left > range_right:
        range_left, range_right = range_right, range_left
        if warning:
            logging.warning(
                f"The range ({range[0]}, {range[1]}) is inverted. "
                f"It has been corrected to ({range_left}, {range_right})."
            )

    invalid_mask = ~np.isnan(array) & ((array <= range_left) | (array >= range_right))
    if warning and np.any(invalid_mask):
        logging.warning(
            f"Invalid array {array}"
            f"All elements should be in the range [{range_left},{range_right}]."
        )
    return invalid_mask

def solve_scalar_equation_brent(
    func: Callable[[float, float], float],
    param_values: np.ndarray,
    x_bounds: tuple[float, float],
    warning: bool = True
) -> np.ndarray:
    """
    Solve a scalar equation for multiple parameters using Brent's method.

    Parameters
    ----------
    func : Callable[[float, float], float]
        Function f(x, param) whose root is to be found for each parameter.
    param_values : np.ndarray
        Array of parameter values to use when solving the equation.
    x_bounds : tuple[float, float]
        Interval (x_min, x_max) in which to search for the root.
        The bounds will be swapped if provided in reverse order.
    warning : bool, optional
        If True (default), warnings are issued for empty inputs, range inversion,
        or missing roots in the interval.

    Returns
    -------
    np.ndarray
        Array of roots found for each parameter value. NaN if no root is found.
    """

    if param_values.size == 0 and warning:
        logging.warning("The input param_values of solve_scalar_equation_brent() is empty. The result will also be an empty float array.")
    x_left, x_right = x_bounds
    if x_left > x_right:
        x_left, x_right = x_right, x_left
        if warning:
            logging.warning(
                f"The range ({x_bounds[0]}, {x_bounds[1]}) is inverted. "
                f"It has been corrected to ({x_left}, {x_right})."
            )

    solutions = []

    for param in param_values:
        f = lambda x: func(x, param)

        if f(x_left) * f(x_right) > 0:
            solutions.append(np.nan)
            if warning : 
                logging.warning(f"{f(x_left)} and {f(x_right)} have the same sign in solve_scalar_equation_brent(). "
                                "There is no root in this range")
        else:
            try:
                sol = brentq(f, x_left, x_right)
                solutions.append(sol)

            except Exception:
                solutions.append(np.nan)

    return np.array(solutions)

def compute_phi_2(phi_2: float, phi_s: float) -> float:
    """
    Function whose root gives the left boundary of the phase acceptance (phi_2).

    Parameters
    ----------
    phi_2 : float
        Phase value in radians to test as the boundary.
    phi_s : float
        Synchronous phase in radians.

    Returns
    -------
    float
        Function value to be used in root-finding (zero crossing corresponds to phi_2).
    """
    term1 = np.sin(phi_2) - phi_2 * np.cos(phi_s)
    term2 = np.sin(phi_s) - phi_s * np.cos(phi_s)
    return term1 + term2