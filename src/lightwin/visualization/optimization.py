"""Define functions related to optimization and failures plotting."""

import logging
from collections.abc import Sequence

import matplotlib.patches as pat
import numpy as np
from matplotlib.axes import Axes

from lightwin.failures.fault import Fault
from lightwin.optimisation.objective.helper import by_element
from lightwin.optimisation.objective.objective import Objective
from lightwin.visualization.helper import X_AXIS_T, create_fig_if_not_exists
from lightwin.visualization.structure import patch_kwargs


def _get_objectives(fault_scenario: list[Fault] | None) -> list[Objective]:
    """Get the objectives stored in ``fault_scenario``."""
    if fault_scenario is None or len(fault_scenario) == 0:
        return []
    if len(fault_scenario) > 1:
        logging.info(
            "There are several failures, so I'll plot only the objectives "
            "corresponding to the first one."
        )
    fault = fault_scenario[0]
    return fault.objectives


def mark_objectives_position(
    ax: Axes,
    fault_scenarios: Sequence[list[Fault]] | None,
    y_axis: str = "struct",
    x_axis: X_AXIS_T = "z_abs",
) -> None:
    """Show where objectives are evaluated.

    In a first time, we only put a lil start or something on the structure
    plot.

    """
    if fault_scenarios is None:
        return
    if y_axis != "struct":
        return
    objectives = _get_objectives(fault_scenarios[0])
    objectives_by_element = by_element(objectives)
    for elt in objectives_by_element:
        kwargs = patch_kwargs(elt, x_axis)
        ax.add_patch(_plot_objective(**kwargs))


def _plot_objective(x_0: float, width: float, **kwargs) -> pat.Circle:
    """Add a marker at the exit of provided element."""
    height = 1.0
    y_0 = -height * 0.5
    patch = pat.Circle((x_0 + width, y_0), radius=0.5, fill=True, lw=0.5)
    return patch


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
