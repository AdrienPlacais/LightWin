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
    fig = plt.gcf()
    fig.canvas.manager.set_window_title("objectives")
    return axis


def _qty_sim_output(column_name: str) -> str:
    """Get the quantity that is stored in the column ``column_name``.

    It is expected that the header of the column is ``qty @ position``; it only
    works for the quantites taken from :class:`.SimulationOutput` and written
    in the ``objectives.csv``.

    """
    return column_name.split("@")[0].strip()


def _post_treat(
    df: pd.DataFrame,
    post_treat: Literal["relative difference", "difference"] | None = None,
    make_absolute: bool = False,
) -> tuple[pd.DataFrame, str]:
    """Post-treat the SimulationOutput data."""
    if post_treat == "relative difference":
        treated_df = (df.iloc[0] - df.iloc[1:]) / df.iloc[0]
        ylabel = "SimOut (relative difference)"
    elif post_treat == "difference":
        treated_df = df.iloc[0] - df.iloc[1:]
        ylabel = "SimOut (difference)"
    else:
        treated_df = df.iloc[1:]
        ylabel = "SimOut"

    if make_absolute:
        treated_df = abs(treated_df)

    return treated_df, ylabel


def plot_additional_objectives(
    objectives: pd.DataFrame,
    simulation_output_cols: list[str],
    subplots: bool = False,
    logy: bool | Literal["sym"] | None = None,
    post_treat: Literal["relative difference", "difference"] | None = None,
    **kwargs,
) -> Axis | np.ndarray | list:
    """Plot evolution of additional objectives."""
    do_not_logify = ("phi_s", "v_cav_mv")
    set_of_quantities = set(
        _qty_sim_output(col) for col in simulation_output_cols
    )
    axis = []
    for quantity in set_of_quantities:
        cols_to_plot = [
            col
            for col in simulation_output_cols
            if _qty_sim_output(col) == quantity
        ]
        actual_logy = logy if quantity not in do_not_logify else None

        to_plot, ylabel = _post_treat(
            objectives[cols_to_plot],
            post_treat=post_treat,
            make_absolute=actual_logy == True,
        )

        axis.append(
            to_plot.plot(
                y=cols_to_plot,
                xlabel="Iteration",
                ylabel=ylabel,
                subplots=subplots,
                logy=actual_logy,
                title=quantity,
                **kwargs,
            )
        )
        fig = plt.gcf()
        fig.canvas.manager.set_window_title(quantity)
    return axis


def main(folder: Path) -> pd.DataFrame:
    """Provide an example of complete study."""
    variables, objectives, constants = load(folder)

    kwargs = {"grid": True}
    opti_cols, simulation_output_cols = get_optimization_objective_names(
        objectives
    )
    plot_optimization_objectives(
        objectives, opti_cols, subplots=False, logy=True, **kwargs
    )
    plot_additional_objectives(
        objectives,
        simulation_output_cols,
        logy=False,
        post_treat="relative difference",
        **kwargs,
    )
    return objectives


if __name__ == "__main__":
    plt.close("all")
    folder = Path("/home/placais/Documents/projects/compensation/spiral2/lightwin_project/optimization_history/")
    objectives = main(folder)
