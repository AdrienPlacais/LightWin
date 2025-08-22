#!/usr/bin/env python3
"""Provide functions to study optimization history."""
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axis import Axis


def load(
    folder: Path, flag_constraints: bool = False
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load the three optimization history files in ``folder``."""
    settings = pd.read_csv(folder / "settings.csv")
    objectives = pd.read_csv(folder / "objectives.csv")

    constraints = pd.DataFrame({"dummy": [0, 1]})
    if flag_constraints:
        constraints = pd.read_csv(folder / "constraints.csv")
    return settings, objectives, constraints


def get_optimization_objective_names(
    objectives: pd.DataFrame,
) -> tuple[list[str], list[str]]:
    """
    Separate data from :class:`.Objective` and from :class:`.SimulationOutput`.

    We expect that objectives have a ``|`` in their name, simulation outputs do
    not.

    """
    cols = objectives.columns
    opti_cols = [col for col in cols if "|" in col]
    simulation_output_cols = [col for col in cols if col not in opti_cols]
    return opti_cols, simulation_output_cols


def add_objective_norm(
    objectives: pd.DataFrame,
    opti_cols: list[str],
    norm_name: str = "Objectives norm",
) -> tuple[pd.DataFrame, list[str]]:
    """Compute norm of objectives and add it to the df."""
    squared = (objectives[col] ** 2 for col in opti_cols)
    objectives = objectives.assign(**{norm_name: np.sqrt(sum(squared))})
    opti_cols.append(norm_name)
    return objectives, opti_cols


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
    assert fig.canvas.manager is not None
    fig.canvas.manager.set_window_title("objectives")
    return axis


def _extract_qty_nature(column_name: str) -> str:
    """Get the quantity that is stored in the column ``column_name``.

    It is expected that the header of the column is ``qty @ position``.

    """
    return column_name.split("@")[0].strip()


def _extract_qty_pos(column_name: str) -> str:
    """Get where was evaluated what is stored in the column ``column_name``.

    It is expected that the header of the column is ``qty @ position``.

    """
    return column_name.split("@")[1].split("(")[0].strip()


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


def plot_simulation_outputs(
    objectives: pd.DataFrame,
    simulation_output_cols: list[str],
    subplots: bool = False,
    logy: bool | Literal["sym"] | None = None,
    post_treat: Literal["relative difference", "difference"] | None = None,
    **kwargs,
) -> Axis | np.ndarray | list:
    """Plot evolution of additional objectives."""
    do_not_logify = ("phi_s", "v_cav_mv")
    set_of_quantities = {
        _extract_qty_nature(col) for col in simulation_output_cols
    }
    axis = []
    for quantity in set_of_quantities:
        cols_to_plot = [
            col
            for col in simulation_output_cols
            if _extract_qty_nature(col) == quantity
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


def identify_pareto(df: pd.DataFrame, objectives: list[str]) -> pd.DataFrame:
    """Get the Pareto front."""
    data = df[objectives].values

    for obj in objectives:
        max_abs = df[obj].abs().max()
        df[obj + "_norm"] = df[obj] / max_abs

    normalized_objectives = [obj + "_norm" for obj in objectives]

    is_efficient = np.ones(data.shape[0], dtype=bool)
    for i, obj_values in enumerate(data):
        if is_efficient[i]:
            # Calculate absolute values since we want to be close to zero
            abs_values = np.abs(data)
            # Check if any other point dominates the current point
            is_dominated = np.all(
                abs_values <= np.abs(obj_values), axis=1
            ) & np.any(abs_values < np.abs(obj_values), axis=1)
            is_efficient[is_dominated] = False
    pareto = df[is_efficient]
    pareto["distance"] = np.linalg.norm(pareto[normalized_objectives], axis=1)

    return pareto


def plot_solutions_3d(
    df: pd.DataFrame, objective_names: Sequence[str], pareto: pd.DataFrame
) -> None:
    """Represent the solutions in 3d."""
    if len(objective_names) != 3:
        logging.warning(f"Cannot 3D plot non-3D {objective_names = }")
        return
    w_kin = objective_names[0]
    phi_abs = objective_names[1]
    mzdelta = objective_names[2]

    # Plotting all solutions
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(
        df[w_kin],
        df[phi_abs],
        df[mzdelta],
        color="blue",
        label="All Solutions",
        s=1.0,
    )

    # Highlight Pareto front solutions
    ax.scatter(
        pareto[w_kin],
        pareto[phi_abs],
        pareto[mzdelta],
        color="red",
        label="Pareto Front",
        s=5.0,
    )
    best_solution = pareto.loc[pareto["distance"].idxmin()]
    ax.scatter(
        best_solution[w_kin],
        best_solution[phi_abs],
        best_solution[mzdelta],
        color="green",
        label="Best",
        s=20.0,
    )

    ax.scatter(0, 0, 0, color="k", label="Ideal", s=20)

    ax.set_xlabel("w_kin")
    ax.set_ylabel("phi_abs")
    ax.set_zlabel("Mzdelta")
    ax.set_title("Pareto Front Visualization")
    ax.legend()


def main(
    folder: Path,
    plot_objectives: bool = True,
    plot_objective_norm: bool = True,
    plot_so: bool = False,
    plot_objectives_3d: bool = True,
) -> pd.DataFrame:
    """Provide an example of complete study."""
    kwargs = {"grid": True}
    _, objectives, _ = load(folder)
    opti_cols, simulation_output_cols = get_optimization_objective_names(
        objectives
    )
    norm_name = "Objectives norm"
    objectives, opti_cols = add_objective_norm(
        objectives, opti_cols, norm_name=norm_name
    )
    if plot_objectives:
        plot_optimization_objectives(
            objectives, opti_cols, subplots=True, logy=True, **kwargs
        )
    if plot_objective_norm:
        objectives.plot(y=norm_name, logy=True, **kwargs)

    if plot_so:
        plot_simulation_outputs(
            objectives,
            simulation_output_cols,
            logy=True,
            post_treat="relative difference",
            **kwargs,
        )

    if plot_objectives_3d:
        pareto = identify_pareto(objectives, opti_cols)
        plot_solutions_3d(objectives, opti_cols, pareto)
    return objectives


if __name__ == "__main__":
    plt.close("all")
    folder = Path(
        "/home/placais/Documents/projects/compensation/spiral2/lightwin_project/optimization_history/"
    )
    objectives = main(folder)
