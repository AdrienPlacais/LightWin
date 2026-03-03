"""Define the function to extract the data to plot.

.. todo::
   Fix the TransferMatrix plot with TraceWin solver.

"""

import logging
from collections.abc import Collection
from dataclasses import dataclass
from typing import Any, Callable, Literal, Self

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

ERROR_REFERENCE_T = Literal[
    "ref accelerator (1st solv w/ 1st solv, 2nd w/ 2nd)",
    "ref accelerator (1st solver)",
    "ref accelerator (2nd solver)",
]


@dataclass
class _SimData:
    """Bundle of parallel x/y/kwargs lists for one accelerator's simulations."""

    x: list[NDArray[np.float64]]
    y: list[NDArray[np.float64]]
    kw: list[dict[str, Any]]

    def __len__(self) -> int:
        return len(self.x)

    def __bool__(self) -> bool:
        return len(self) > 0

    def __iadd__(self, other: Self) -> Self:
        """Define ``sim_data += other_simdata`` operations."""
        self.x += other.x
        self.y += other.y
        self.kw += other.kw
        return self


def all_accelerators_data(
    x_axis: X_AXIS_T,
    y_axis: GETTABLE_SIMULATION_OUTPUT_T,
    *accelerators: Accelerator,
    error_presets: dict[str, dict[str, str | float]],
    error_reference: ERROR_REFERENCE_T,
    to_deg: bool = True,
    only_solver_id: Collection[str] | str | None = None,
    **get_kwargs,
) -> tuple[
    list[NDArray[np.float64]], list[NDArray[np.float64]], list[dict[str, Any]]
]:
    """Get x_data, y_data, kwargs from all Accelerators (<=> for 1 subplot).

    Parameters
    ----------
    x_axis :
        Data to use as x-axis.
    y_axis :
        Data to use as y-axis.
    *accelerators :
        Object holding the :class:`.SimulationOutput` to plot.
    error_presets :
        Dictionary passed to :func:`_error_calculation_function`.
    error_reference :
        Reference in errors calculations.
    to_deg :
        If ``y_axis`` data with ``"phi"`` in their name should be converted to
        degrees.
    only_solver_id :
        If set, we plot only data obtained with this solver(s). Must be
        :attr:`.BeamCalculator.id` (or, equivalently, a key(s) in
        :attr:`.Accelerator.simulation_outputs`). Typical values:
        ``"0_Envelope1D"`` or ``"1_TraceWin"``.

    Returns
    -------
    list[NDArray[np.float64]]
        ``(n,)`` list of x-arrays to plot.
    list[NDArray[np.float64]]
        ``(n,)`` list of y-arrays to plot.
    list[dict]
        ``(n,)`` list of plot ``kwargs``.

    """
    if isinstance(only_solver_id, str):
        only_solver_id = (only_solver_id,)

    error_plot = y_axis.endswith("_err")
    key = y_axis[:-4] if error_plot else y_axis

    ref_acc = accelerators[0]
    fix_accs = accelerators[1:]

    ref_acc, *fix_accs = accelerators

    ref = _single_accelerator_all_simulations_data(
        x_axis,
        key,
        ref_acc,
        only_solver_id=only_solver_id,
        to_deg=to_deg,
        **get_kwargs,
    )

    if not error_plot:
        result = _SimData(ref.x[:], ref.y[:], ref.kw[:])
        for acc in fix_accs:
            fix = _single_accelerator_all_simulations_data(
                x_axis,
                key,
                acc,
                only_solver_id=only_solver_id,
                to_deg=to_deg,
                **get_kwargs,
            )
            result += fix
        return result.x, result.y, _avoid_similar_labels(result.kw)

    fun_error = _error_calculation_function(
        y_axis, error_presets=error_presets
    )
    result = _SimData([], [], [])
    for acc in fix_accs:
        fix = _single_accelerator_all_simulations_data(
            x_axis,
            key,
            acc,
            only_solver_id=only_solver_id,
            to_deg=to_deg,
            **get_kwargs,
        )
        result += _compute_error(ref, fix, fun_error, error_reference)

    return result.x, result.y, _avoid_similar_labels(result.kw)


def _single_accelerator_all_simulations_data(
    x_axis: X_AXIS_T,
    y_axis: GETTABLE_SIMULATION_OUTPUT_T,
    accelerator: Accelerator,
    only_solver_id: Collection[str] | None = None,
    **get_kwargs,
) -> _SimData:
    """Get x_data, y_data, kwargs from all SimulationOutputs of Accelerator."""
    result = _SimData([], [], [])
    ls = "-"

    for solver_id, simulation_output in accelerator.simulation_outputs.items():
        if only_solver_id is not None and solver_id not in only_solver_id:
            continue

        label = solver_id
        if simulation_output.is_multiparticle:
            label += " (multipart)"
        label = f"{accelerator.name} {label}"

        x_dat, y_dat, plt_kw = _single_simulation_all_data(
            x_axis, y_axis, simulation_output, label=label, **get_kwargs
        )
        plt_kw["label"] = label
        plt_kw["ls"] = ls
        ls = "--"

        result.x.append(x_dat)
        result.y.append(y_dat)
        result.kw.append(plt_kw)

    return result


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
        dummy = np.full((10,), np.nan)
        return dummy, dummy, {}

    if x_data.shape != y_data.shape:
        logging.error(
            f"Shape mismatch in {label}: {x_axis} has shape {x_data.shape} "
            f"while {y_axis} has shape {y_data.shape}. If this is a "
            "TransferMatrix plot with TraceWin solver, it is because TraceWin "
            "exports one transfer matrix per element while LightWin exports "
            "one per thin-lense (FIXME). Also happens with acceptance_phi and "
            f"TraceWin. Skipping this plot. Complete SimulationOutput "
            f"is:\n{simulation_output}"
        )
        return x_data, np.full_like(x_data, np.nan), {}

    return x_data, y_data, dic.plot_kwargs[y_axis].copy()


def _single_simulation_data(
    axis: GETTABLE_SIMULATION_OUTPUT_T,
    simulation_output: SimulationOutput,
    to_deg: bool = True,
    to_numpy=True,
    none_to_nan=True,
    warn_structure_dependent=False,
    **get_kwargs,
) -> NDArray[np.float64] | None:
    """Get single data array from single SimulationOutput."""
    # Patch to avoid envelopes being converted again to degrees
    if "envelope_pos" in axis:
        to_deg = False
    data = simulation_output.get(
        axis,
        to_deg=to_deg,
        to_numpy=to_numpy,
        none_to_nan=none_to_nan,
        warn_structure_dependent=warn_structure_dependent,
        **get_kwargs,
    )
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
) -> tuple[
    Callable[[NDArray[np.float64], NDArray[np.float64]], NDArray[np.float64]],
    str,
]:
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
    ref: _SimData,
    fix: _SimData,
    fun_error: Callable[
        [NDArray[np.float64], NDArray[np.float64]], NDArray[np.float64]
    ],
    error_reference: ERROR_REFERENCE_T,
) -> _SimData:
    """Compute error between one reference and one fix accelerator.

    Parameters
    ----------
    ref :
        Data from the reference accelerator (one entry per solver).
    fix :
        Data from a single fix accelerator (one entry per solver).
    fun_error :
        Function ``(y_ref, y_fix) -> error``.
    error_reference :
        Which reference solver(s) to pair with fix solvers.

    Returns
    -------
        Error data, one entry per (ref, fix) solver pair.

    """
    if not ref or not fix:
        logging.error("Empty data passed to _compute_error, returning empty.")
        return _SimData([], [], [])

    pairs = _build_solver_pairs(len(ref), len(fix), error_reference)
    if pairs is None:
        return _SimData([], [], [])

    x_out, y_out, kw_out = [], [], []
    for i_ref, i_fix in pairs:
        x_interp, y_ref, _, y_fix = helper.resample(
            ref.x[i_ref], ref.y[i_ref], fix.x[i_fix], fix.y[i_fix]
        )
        x_out.append(x_interp)
        y_out.append(fun_error(y_ref, y_fix))
        kw_out.append(fix.kw[i_fix])

    return _SimData(x_out, y_out, kw_out)


def _build_solver_pairs(
    n_ref: int, n_fix: int, error_reference: ERROR_REFERENCE_T
) -> list[tuple[int, int]] | None:
    """Return (i_ref, i_fix) index pairs, or None on error.

    Parameters
    ----------
    n_ref :
        Number of solvers in the reference accelerator.
    n_fix :
        Number of solvers in the fix accelerator.
    error_reference :
        Pairing strategy.

    Returns
    -------
        List of ``(i_ref, i_fix)`` pairs, or ``None`` if the strategy is
        unsupported given the available solver counts.

    """
    if error_reference == "ref accelerator (1st solv w/ 1st solv, 2nd w/ 2nd)":
        return [(min(i, n_ref - 1), i) for i in range(n_fix)]
    if error_reference == "ref accelerator (1st solver)":
        return [(0, i) for i in range(n_fix)]
    if error_reference == "ref accelerator (2nd solver)":
        if n_ref < 2:
            logging.error(
                f"{error_reference = } not supported: reference has only "
                f"{n_ref} simulation output(s)."
            )
            return None
        return [(1, i) for i in range(n_fix)]
    logging.error(
        f"{error_reference = } is not allowed. Check allowed values."
    )
    return None
