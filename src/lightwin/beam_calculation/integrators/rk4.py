"""Define Runge-Kutta integraiton function."""

from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray


def rk4(
    u: NDArray[np.float64],
    du: Callable[[float, NDArray[np.float64]], NDArray[np.float64]],
    x: float,
    dx: float,
) -> NDArray[np.float64]:
    """Compute variation of ``u`` between ``x`` and ``x+dx``.

    Use 4-th order Runge-Kutta method.

    Note
    ----
    This is a slightly modified version of the RK. The ``k_i`` are proportional
    to ``du`` instead of ``du/dx``.

    Parameters
    ----------
    u :
        Vector to integrate.
    du :
        Gives the variation of ``u`` components with ``x``.
    x :
        Where ``u`` is known.
    dx :
        Integration step.

    Return
    ------
        Variation of ``u`` between ``x`` and ``x+dx``.

    """
    half_dx = 0.5 * dx
    k_1 = du(x, u)
    k_2 = du(x + half_dx, u + 0.5 * k_1)
    k_3 = du(x + half_dx, u + 0.5 * k_2)
    k_4 = du(x + dx, u + k_3)
    return (k_1 + 2.0 * k_2 + 2.0 * k_3 + k_4) / 6.0


def rk4_2d(
    u: float,
    v: float,
    delta: Callable[[float, float, float], tuple[float, float]],
    x: float,
    dx: float,
) -> tuple[float, float]:
    """Compute variation of ``u`` and ``v`` between ``x`` and ``x+dx``.

    Use 4-th order Runge-Kutta method. ``u`` and ``v`` are scalar. This version
    is :func:`.rk4` but with two dimensions only.

    Note
    ----
    This is a slightly modified version of the RK. The ``k_i`` are proportional
    to ``delta_u`` instead of ``du_dz``.

    Parameters
    ----------
    u :
        First variable to be integrated.
    v :
        Second variable to be integrated.
    delta :
        Takes in ``x``, ``u``, ``v`` and return variation of ``u`` and ``v``.
    x :
        Where ``u`` and ``v`` are known.
    dx :
        Integration step.

    Return
    ------
        Variation of ``u`` and ``v`` between ``x`` and ``x+dx``.

    """

    half_dx = 0.5 * dx
    k_1u, k_1v = delta(x, u, v)
    k_2u, k_2v = delta(x + half_dx, u + 0.5 * k_1u, v + 0.5 * k_1v)
    k_3u, k_3v = delta(x + half_dx, u + 0.5 * k_2u, v + 0.5 * k_2v)
    k_4u, k_4v = delta(x + dx, u + k_3u, v + k_3v)
    return (
        (k_1u + 2 * k_2u + 2 * k_3u + k_4u) / 6.0,
        (k_1v + 2 * k_2v + 2 * k_3v + k_4v) / 6.0,
    )
