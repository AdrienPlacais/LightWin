"""Define functions related to optimization and failures plotting.

.. todo::
    Information on the element under the cursor (hover).

"""

import logging
from collections.abc import Sequence

import matplotlib.patches as pat
import numpy as np
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.typing import ColorType

from lightwin.core.elements.element import Element
from lightwin.failures.fault import Fault
from lightwin.optimisation.objective.helper import by_element
from lightwin.optimisation.objective.objective import Objective
from lightwin.visualization.helper import X_AXIS_T, create_fig_if_not_exists
from lightwin.visualization.structure import patch_kwargs

OBJECTIVE_COLOR = "blue"


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
    color: ColorType = OBJECTIVE_COLOR,
    alpha: float = 0.5,
) -> None:
    """Show where objectives are evaluated."""
    if fault_scenarios is None:
        logging.info(
            "The ``fault_scenarios`` must be given to plot.factory for the "
            "objectives to be displayed."
        )
        return

    objectives_by_element: dict[Element, list[Objective]]
    objectives_by_element = by_element(_get_objectives(fault_scenarios[0]))
    for elt in objectives_by_element:
        kwargs = patch_kwargs(elt, x_axis, color=color, alpha=alpha, pos="out")

        if y_axis != "struct":
            _line_objective(ax, **kwargs)
            continue

        ax.add_patch(_patch_objective(**kwargs))


def _line_objective(
    ax: Axes, x_0: float, color: ColorType, alpha: float, **kwargs
) -> Line2D:
    """Give a vertical line to add to a plot.

    This function is mainly to intercept the kwargs axvline would not
    understand, such as x_0 or width.

    """
    return ax.axvline(x=x_0, color=color, alpha=alpha)


def _patch_objective(
    x_0: float, width: float, color: ColorType, alpha: float, **kwargs
) -> pat.Arrow:
    """Add a marker at the exit of provided element."""
    starting_height = 0.75
    ending_height = 0.05
    patch = pat.Arrow(
        x=x_0,
        y=starting_height,
        dx=0,
        dy=ending_height - starting_height,
        width=2 * width,
        color=color,
        alpha=alpha,
    )
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
