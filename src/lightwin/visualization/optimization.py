"""Define functions related to optimization and failures plotting."""

from collections.abc import Collection

import numpy as np
from matplotlib.axes import Axes

from lightwin.optimisation.objective.helper import by_element
from lightwin.optimisation.objective.objective import Objective
from lightwin.visualization.helper import X_AXIS_T, create_fig_if_not_exists


def mark_objective_position(
    axis: Axes,
    objectives: Collection[Objective],
    x_axis: X_AXIS_T = "z_abs",
) -> None:
    """Show where objectives are evaluated."""
    objectives_by_element = by_element(objectives)


def plot_fit_progress(hist_f, l_label, nature="Relative"):
    """Plot the evolution of the objective functions w/ each iteration."""
    _, axx = create_fig_if_not_exists(1, num=32)
    axx = axx[0]

    scales = {
        "Relative": lambda x: x / x[0],
        "Absolute": lambda x: x,
    }

    # Number of objectives, number of evaluations
    n_f = len(l_label)
    n_iter = len(hist_f)
    iteration = np.linspace(0, n_iter - 1, n_iter)

    __f = np.empty([n_f, n_iter])
    for i in range(n_iter):
        __f[:, i] = scales[nature](hist_f)[i]

    for j, label in enumerate(l_label):
        axx.plot(iteration, __f[j], label=label)

    axx.grid(True)
    axx.legend()
    axx.set_xlabel("Iteration #")
    axx.set_ylabel(f"{nature} variation of error")
    axx.set_yscale("log")
