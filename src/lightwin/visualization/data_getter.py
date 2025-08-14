"""Define the function to extract the data to plot.

.. todo::
   Fix the TransferMatrix plot with TraceWin solver.

"""

import itertools
import logging
from typing import Any, Callable

import numpy as np
from numpy.typing import NDArray

import lightwin.util.dicts_output as dic
from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.util import helper
from lightwin.util.typing import GETTABLE_SIMULATION_OUTPUT_T
from lightwin.visualization.helper import (
    X_AXIS_T,
)


def all_accelerators_data(
    x_axis: X_AXIS_T,
    y_axis: GETTABLE_SIMULATION_OUTPUT_T,
    *accelerators: Accelerator,
    error_presets: dict[str, dict[str, Any]],
    error_reference: str,
    to_deg: bool = True,
    none_to_nan: bool = True,
    to_numpy: bool = True,
    warn_structure_dependent: bool = False,
    **get_kwargs,
) -> tuple[list[np.ndarray], list[np.ndarray], list[dict[str, Any]]]:
    """Get x_data, y_data, kwargs from all Accelerators (<=> for 1 subplot)."""
    x_data, y_data, plt_kwargs = [], [], []

    key = y_axis
    error_plot = y_axis[-4:] == "_err"
    if error_plot:
        key = y_axis[:-4]

    for accelerator in accelerators:
        x_dat, y_dat, plt_kw = _single_accelerator_all_simulations_data(
            x_axis,
            key,
            accelerator,
            to_deg=to_deg,
            none_to_nan=none_to_nan,
            to_numpy=to_numpy,
            warn_structure_dependent=warn_structure_dependent,
            **get_kwargs,
        )
        x_data += x_dat
        y_data += y_dat
        plt_kwargs += plt_kw

    if error_plot:
        fun_error = _error_calculation_function(
            y_axis, error_presets=error_presets
        )
        x_data, y_data, plt_kwargs = _compute_error(
            x_data,
            y_data,
            plt_kwargs,
            fun_error,
            error_reference=error_reference,
        )

    plt_kwargs = _avoid_similar_labels(plt_kwargs)
    return x_data, y_data, plt_kwargs


def _single_accelerator_all_simulations_data(
    x_axis: X_AXIS_T,
    y_axis: GETTABLE_SIMULATION_OUTPUT_T,
    accelerator: Accelerator,
    **get_kwargs,
) -> tuple[list[np.ndarray], list[np.ndarray], list[dict[str, Any]]]:
    """Get x_data, y_data, kwargs from all SimulationOutputs of Accelerator."""
    x_data, y_data, plt_kwargs = [], [], []
    ls = "-"
    for solver, simulation_output in accelerator.simulation_outputs.items():
        short_solver = solver.split("(")[0]
        if simulation_output.is_multiparticle:
            short_solver += " (multipart)"
        label = f"{accelerator.name} {short_solver}"

        x_dat, y_dat, plt_kw = _single_simulation_all_data(
            x_axis, y_axis, simulation_output, label=label, **get_kwargs
        )

        plt_kw["label"] = label
        plt_kw["ls"] = ls
        ls = "--"

        x_data.append(x_dat)
        y_data.append(y_dat)
        plt_kwargs.append(plt_kw)

    return x_data, y_data, plt_kwargs


def _single_simulation_all_data(
    x_axis: X_AXIS_T,
    y_axis: GETTABLE_SIMULATION_OUTPUT_T,
    simulation_output: SimulationOutput,
    label: str,
    **get_kwargs,
) -> tuple[NDArray[np.float64], NDArray[np.float64], dict[str, Any]]:
    """Get x data, y data, kwargs from a SimulationOutput."""
    x_data = _single_simulation_data(x_axis, simulation_output, **get_kwargs)
    y_data = _single_simulation_data(y_axis, simulation_output, **get_kwargs)

    if x_data is None or y_data is None:
        if x_data is None:
            logging.error(
                f"{x_axis} not found in {label}. Setting it to dummy data. "
                f"Complete SimulationOutput is:\n{simulation_output}"
            )
        if y_data is None:
            logging.error(
                f"{y_axis} not found in {label}. Setting it to dummy data. "
                f"Complete SimulationOutput is:\n{simulation_output}"
            )
        x_data = np.full((10, 1), np.nan)
        y_data = np.full((10, 1), np.nan)
        return x_data, y_data, {}

    if (leny := y_data.shape) != (lenx := x_data.shape):
        logging.error(
            f"Shape mismatch in {label}: {x_axis} has shape {lenx} while "
            f"{y_axis} has shape {leny}. If this is a TransferMatrix plot "
            "with TraceWin solver, it is because TraceWin exports one transfer"
            " matrix per element while LightWin exports one per thin-lense "
            "(FIXME). Also happends with acceptance_phi and TraceWin. Skipping"
            f" this plot. Complete SimulationOuptut is:\n{simulation_output}"
        )
        y_data = np.full_like(x_data, np.nan)
        return x_data, y_data, {}

    plt_kwargs = dic.plot_kwargs[y_axis].copy()
    return x_data, y_data, plt_kwargs


def _single_simulation_data(
    axis: GETTABLE_SIMULATION_OUTPUT_T,
    simulation_output: SimulationOutput,
    to_deg: bool = True,
    **get_kwargs,
) -> NDArray[np.float64] | None:
    """Get single data array from single SimulationOutput."""
    # Patch to avoid envelopes being converted again to degrees
    if "envelope_pos" in axis:
        to_deg = False
    data = simulation_output.get(axis, to_deg=to_deg, **get_kwargs)
    return data


def _avoid_similar_labels(plt_kwargs: list[dict]) -> list[dict]:
    """Append a number at the end of labels in doublons."""
    my_labels = []
    for kwargs in plt_kwargs:
        label = kwargs["label"]
        if label not in my_labels:
            my_labels.append(label)
            continue

        while kwargs["label"] in my_labels:
            try:
                i = int(label[-1])
                kwargs["label"] += str(i + 1)
            except ValueError:
                kwargs["label"] += "_0"

        my_labels.append(kwargs["label"])
    return plt_kwargs


# Error related
def _error_calculation_function(
    y_axis: str,
    error_presets: dict[str, dict[str, Any]],
) -> tuple[Callable[[np.ndarray, np.ndarray], np.ndarray], str]:
    """Set the function called to compute error."""
    scale = error_presets[y_axis]["scale"]
    error_computers = {
        "simple": lambda y_ref, y_lin: scale * (y_ref - y_lin),
        "abs": lambda y_ref, y_lin: scale * np.abs(y_ref - y_lin),
        "rel": lambda y_ref, y_lin: scale * (y_ref - y_lin) / y_ref,
        "log": lambda y_ref, y_lin: scale * np.log10(np.abs(y_lin / y_ref)),
    }
    key = error_presets[y_axis]["diff"]
    fun_error = error_computers[key]
    return fun_error


def _compute_error(
    x_data: list[np.ndarray],
    y_data: list[np.ndarray],
    plt_kwargs: list[dict[str, Any]],
    fun_error: Callable[[np.ndarray, np.ndarray], np.ndarray],
    error_reference: str,
) -> tuple[list[np.ndarray], list[np.ndarray], list[dict[str, Any]]]:
    """Compute error with proper reference and proper function."""
    simulation_indexes = range(len(x_data))
    if error_reference == "ref accelerator (1st solv w/ 1st solv, 2nd w/ 2nd)":
        i_ref = [i for i in range(len(x_data) // 2)]
    elif error_reference == "ref accelerator (1st solver)":
        i_ref = [0]
    elif error_reference == "ref accelerator (2nd solver)":
        i_ref = [1]
        if len(x_data) < 4:
            logging.error(
                f"{error_reference = } not supported when only one "
                "simulation is performed."
            )

            return np.full((10, 1), np.nan), np.full((10, 1), np.nan), []
    else:
        logging.error(
            f"{error_reference = }, which is not allowed. Check "
            "allowed values in _compute_error."
        )
        return np.full((10, 1), np.nan), np.full((10, 1), np.nan), []

    i_err = [i for i in simulation_indexes if i not in i_ref]
    indexes_ref_with_err = itertools.zip_longest(
        i_ref, i_err, fillvalue=i_ref[0]
    )

    x_data_error, y_data_error = [], []
    for ref, err in indexes_ref_with_err:
        x_interp, y_ref, _, y_err = helper.resample(
            x_data[ref], y_data[ref], x_data[err], y_data[err]
        )
        error = fun_error(y_ref, y_err)

        x_data_error.append(x_interp)
        y_data_error.append(error)

    plt_kwargs = [plt_kwargs[i] for i in i_err]
    return x_data_error, y_data_error, plt_kwargs
