#!/usr/bin/env python3
"""Provide functions to study optimization history."""
from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axis import Axis


def load(
    folder: Path, flag_constraints: bool = False
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load the threee optimization history files in ``folder``."""
    settings = pd.read_csv(folder / "settings.csv")
    objectives = pd.read_csv(folder / "objectives.csv")

    constraints = pd.DataFrame({"dummy": [0, 1]})
    if flag_constraints:
        constraints = pd.read_csv(folder / "constraints.csv")
    return settings, objectives, constraints


def get_optimization_objective_names(
    objectives: pd.DataFrame,
) -> tuple[list[str], list[str]]:
    """Get the columns corresponding to optimization objectives.

    Also return columns taken from simulation outputs.

    """
    cols = objectives.columns
    opti_cols = [col for col in cols if "@" not in col]
    simulation_output_cols = [col for col in cols if "@" in col]
    return opti_cols, simulation_output_cols


def plot_optimization_objectives(
    objectives: pd.DataFrame,
    opti_cols: list[str],
    subplots: bool = False,
    logy: bool | Literal["sym"] | None = None,
    **kwargs,
) -> Axis | np.ndarray:
    """Plot evolution of optimization objectives."""
    to_plot = objectives[opti_cols]
    ylabel = "Objective"
    if isinstance(logy, bool) and logy:
        to_plot = abs(objectives[opti_cols])
        ylabel = "Objective (abs)"

    axis = to_plot.plot(
        y=opti_cols,
        xlabel="Iteration",
        ylabel=ylabel,
        subplots=subplots,
        logy=logy,
        **kwargs,
    )
    return axis


def plot_additional_objectives(
    objectives: pd.DataFrame,
    simulation_output_cols: list[str],
    subplots: bool = False,
    logy: bool | Literal["sym"] | None = None,
    **kwargs,
) -> Axis | np.ndarray | list:
    """Plot evolution of additional objectives."""
    to_plot = objectives[simulation_output_cols]
    ylabel = "SimOut"
    if isinstance(logy, bool) and logy:
        to_plot = abs(objectives[simulation_output_cols])

    quantities = set(col.split("@")[0] for col in simulation_output_cols)
    axis = []
    for qty in quantities:
        cols = [col for col in simulation_output_cols if qty in col]
        axis.append(
            to_plot.plot(
                y=cols,
                xlabel="Iteration",
                ylabel=ylabel,
                subplots=subplots,
                logy=logy,
                **kwargs,
            )
        )
    return axis


def main(folder: Path) -> pd.DataFrame:
    """Provide an example of complete study."""
    variables, objectives, constants = load(folder)

    kwargs = {"grid": True}
    opti_cols, simulation_output_cols = get_optimization_objective_names(
        objectives
    )
    plot_optimization_objectives(
        objectives, opti_cols, subplots=True, logy=True, **kwargs
    )
    plot_additional_objectives(
        objectives, simulation_output_cols, logy=True, **kwargs
    )
    return objectives


if __name__ == "__main__":
    plt.close("all")
    folder = Path("/home/placais/Downloads/")
    objectives = main(folder)
