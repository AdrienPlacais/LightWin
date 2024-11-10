"""Define a library to produce all these nice plots.

.. todo::
    better detection of what is a multiparticle simulation and what is not.
    Currently looking for "'partran': 0" in the name of the solver, making the
    assumption that multipart is the default. But it depends on the .ini...
    update: just use .is_a_multiparticle_simulation

.. todo::
    Fix when there is only one accelerator to plot.

.. todo::
    Different plot according to dimension of FieldMap, or according to if it
    accelerates or not (ex when quadrupole defined by a field map)

"""

import itertools
import logging
from collections.abc import Collection
from pathlib import Path
from typing import Any, Callable, Sequence

import matplotlib.pyplot as plt
import numpy as np
from cycler import cycler
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.typing import ColorType
from palettable.colorbrewer.qualitative import Dark2_8  # type: ignore

import lightwin.util.dicts_output as dic
from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.optimisation.objective.helper import by_element
from lightwin.optimisation.objective.objective import Objective
from lightwin.util import helper
from lightwin.visualization import structure
from lightwin.visualization.helper import (
    X_AXIS_T,
    create_fig_if_not_exists,
    savefig,
)

font = {"family": "serif"}  # , 'size': 25}
plt.rc("font", **font)
plt.rcParams["axes.prop_cycle"] = cycler(color=Dark2_8.mpl_colors)

FALLBACK_PRESETS = {
    "x_axis": "z_abs",
    "plot_section": True,
    "clean_fig": False,
    "sharex": True,
}
PLOT_PRESETS = {
    "energy": {
        "x_axis": "z_abs",
        "all_y_axis": ["w_kin", "w_kin_err", "struct"],
        "num": 21,
    },
    "phase": {
        "x_axis": "z_abs",
        "all_y_axis": ["phi_abs", "phi_abs_err", "struct"],
        "num": 22,
    },
    "cav": {
        "x_axis": "elt_idx",
        "all_y_axis": ["v_cav_mv", "phi_s", "struct"],
        "num": 23,
    },
    "emittance": {
        "x_axis": "z_abs",
        "all_y_axis": ["eps_phiw", "struct"],
        "num": 24,
    },
    "twiss": {
        "x_axis": "z_abs",
        "all_y_axis": ["alpha_phiw", "beta_phiw", "gamma_phiw"],
        "num": 25,
    },
    "envelopes": {
        "x_axis": "z_abs",
        "all_y_axis": [
            "envelope_pos_phiw",
            "envelope_energy_zdelta",
            "struct",
        ],
        "num": 26,
        "to_deg": False,
        "symetric_plot": True,
    },
    "mismatch_factor": {
        "x_axis": "z_abs",
        "all_y_axis": ["mismatch_factor_zdelta", "struct"],
        "num": 27,
    },
}
ERROR_PRESETS = {
    "w_kin_err": {"scale": 1.0, "diff": "simple"},
    "phi_abs_err": {"scale": 1.0, "diff": "simple"},
}

# The one you generally want
ERROR_REFERENCE = "ref accelerator (1st solv w/ 1st solv, 2nd w/ 2nd)"

# These two are mostly useful when you want to study the differences between
# two solvers
# ERROR_REFERENCE = "ref accelerator (1st solver)"
# ERROR_REFERENCE = "ref accelerator (2nd solver)"


# =============================================================================
# Front end
# =============================================================================
def factory(
    accelerators: Sequence[Accelerator],
    plots: dict[str, bool],
    **kwargs,
) -> list[Figure]:
    """Create all the desired plots."""
    if (
        kwargs["clean_fig"]
        and not kwargs["save_fig"]
        and len(accelerators) > 2
    ):
        logging.warning(
            "You will only see the plots of the last accelerators,"
            " previous will be erased without saving."
        )

    ref_acc = accelerators[0]
    # Dirty patch to force plot even when only one accelerator
    if len(accelerators) == 1:
        accelerators = (ref_acc, ref_acc)
    figs = [
        _plot_preset(
            preset, *(ref_acc, fix_acc), **_proper_kwargs(preset, kwargs)
        )
        for fix_acc in accelerators[1:]
        for preset, plot_me in plots.items()
        if plot_me
    ]
    return figs


# =============================================================================
# Used in factory
# =============================================================================
# Main func
def _plot_preset(
    str_preset: str,
    *args: Accelerator,
    x_axis: X_AXIS_T = "z_abs",
    all_y_axis: list[str] | None = None,
    save_fig: bool = True,
    **kwargs,
) -> Figure:
    """Plot a preset.

    Parameters
    ----------
    str_preset : str
        Key of PLOT_PRESETS.
    *args : Accelerator
        Accelerators to plot. In typical usage, args = (Working, Fixed)
        (previously: (Working, Broken, Fixed). Useful to reimplement?)
    x_axis : str, optional
        Name of the x axis. The default is 'z_abs'.
    all_y_axis : list[str] | None, optional
        Name of all the y axis. The default is None.
    save_fig : bool, optional
        To save Figures or not. The default is True.
    **kwargs :
        Holds all complementary data on the plots.

    """
    fig, axx = create_fig_if_not_exists(len(all_y_axis), **kwargs)

    colors = None
    for i, (axe, y_axis) in enumerate(zip(axx, all_y_axis)):
        _make_a_subplot(axe, x_axis, y_axis, colors, *args, **kwargs)
        if i == 0:
            colors = _keep_colors(axe)
    axx[0].legend()
    axx[-1].set_xlabel(dic.markdown[x_axis])

    if save_fig:
        file = Path(args[-1].get("accelerator_path"), f"{str_preset}.png")
        savefig(fig, file)

    return fig


# Plot style
def _proper_kwargs(preset: str, kwargs: dict[str, bool]) -> dict:
    """Merge dicts, priority kwargs > PLOT_PRESETS > FALLBACK_PRESETS."""
    return FALLBACK_PRESETS | PLOT_PRESETS[preset] | kwargs


def _keep_colors(axe: Axes) -> dict[object, ColorType]:
    """Keep track of the color associated with each SimulationOutput."""
    lines = axe.get_lines()
    colors = {line.get_label(): line.get_color() for line in lines}
    return colors


def _y_label(y_axis: str) -> str:
    """Set the proper y axis label."""
    if "_err" in y_axis:
        key = ERROR_PRESETS[y_axis]["diff"]
        y_label = dic.markdown["err_" + key]
        return y_label
    y_label = dic.markdown[y_axis]
    return y_label


# Data getters
def _single_simulation_data(
    axis: str, simulation_output: SimulationOutput
) -> list[float] | None:
    """lightwin.Get single data array from single SimulationOutput."""
    kwargs: dict[str, Any]
    kwargs = {"to_numpy": False, "to_deg": True}

    # patch to avoid envelopes being converted again to degrees
    if "envelope_pos" in axis:
        kwargs["to_deg"] = False
    data = simulation_output.get(axis, **kwargs)
    return data


def _single_simulation_all_data(
    x_axis: X_AXIS_T, y_axis: str, simulation_output: SimulationOutput
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Get x data, y data, kwargs from a SimulationOutput."""
    x_data = _single_simulation_data(x_axis, simulation_output)
    y_data = _single_simulation_data(y_axis, simulation_output)

    if None in (x_data, y_data):
        x_data = np.full((10, 1), np.nan)
        y_data = np.full((10, 1), np.nan)
        logging.warning(
            f"{x_axis} or {y_axis} not found in {simulation_output}"
        )
        return x_data, y_data, {}

    x_data = np.array(x_data)
    y_data = np.array(y_data)
    plt_kwargs = dic.plot_kwargs[y_axis].copy()
    return x_data, y_data, plt_kwargs


def _single_accelerator_all_simulations_data(
    x_axis: X_AXIS_T, y_axis: str, accelerator: Accelerator
) -> tuple[list[np.ndarray], list[np.ndarray], list[dict[str, Any]]]:
    """Get x_data, y_data, kwargs from all SimulationOutputs of Accelerator."""
    x_data, y_data, plt_kwargs = [], [], []
    ls = "-"
    for solver, simulation_output in accelerator.simulation_outputs.items():
        x_dat, y_dat, plt_kw = _single_simulation_all_data(
            x_axis, y_axis, simulation_output
        )
        short_solver = solver.split("(")[0]
        if simulation_output.is_multiparticle:
            short_solver += " (multipart)"

        plt_kw["label"] = " ".join([accelerator.name, short_solver])
        plt_kw["ls"] = ls
        ls = "--"

        x_data.append(x_dat)
        y_data.append(y_dat)
        plt_kwargs.append(plt_kw)

    return x_data, y_data, plt_kwargs


def _all_accelerators_data(
    x_axis: X_AXIS_T, y_axis: str, *accelerators: Accelerator
) -> tuple[list[np.ndarray], list[np.ndarray], list[dict[str, Any]]]:
    """Get x_data, y_data, kwargs from all Accelerators (<=> for 1 subplot)."""
    x_data, y_data, plt_kwargs = [], [], []

    key = y_axis
    error_plot = y_axis[-4:] == "_err"
    if error_plot:
        key = y_axis[:-4]

    for accelerator in accelerators:
        x_dat, y_dat, plt_kw = _single_accelerator_all_simulations_data(
            x_axis, key, accelerator
        )
        x_data += x_dat
        y_data += y_dat
        plt_kwargs += plt_kw

    if error_plot:
        fun_error = _error_calculation_function(y_axis)
        x_data, y_data, plt_kwargs = _compute_error(
            x_data, y_data, plt_kwargs, fun_error
        )

    plt_kwargs = _avoid_similar_labels(plt_kwargs)

    return x_data, y_data, plt_kwargs


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
) -> tuple[Callable[[np.ndarray, np.ndarray], np.ndarray], str]:
    """Set the function called to compute error."""
    scale = ERROR_PRESETS[y_axis]["scale"]
    error_computers = {
        "simple": lambda y_ref, y_lin: scale * (y_ref - y_lin),
        "abs": lambda y_ref, y_lin: scale * np.abs(y_ref - y_lin),
        "rel": lambda y_ref, y_lin: scale * (y_ref - y_lin) / y_ref,
        "log": lambda y_ref, y_lin: scale * np.log10(np.abs(y_lin / y_ref)),
    }
    key = ERROR_PRESETS[y_axis]["diff"]
    fun_error = error_computers[key]
    return fun_error


def _compute_error(
    x_data: list[np.ndarray],
    y_data: list[np.ndarray],
    plt_kwargs: dict[str, Any],
    fun_error: Callable[[np.ndarray, np.ndarray], np.ndarray],
) -> tuple[list[np.ndarray], list[np.ndarray]]:
    """Compute error with proper reference and proper function."""
    simulation_indexes = range(len(x_data))
    if ERROR_REFERENCE == "ref accelerator (1st solv w/ 1st solv, 2nd w/ 2nd)":
        i_ref = [i for i in range(len(x_data) // 2)]
    elif ERROR_REFERENCE == "ref accelerator (1st solver)":
        i_ref = [0]
    elif ERROR_REFERENCE == "ref accelerator (2nd solver)":
        i_ref = [1]
        if len(x_data) < 4:
            logging.error(
                f"{ERROR_REFERENCE = } not supported when only one "
                "simulation is performed."
            )

            return np.full((10, 1), np.nan), np.full((10, 1), np.nan)
    else:
        logging.error(
            f"{ERROR_REFERENCE = }, which is not allowed. Check "
            "allowed values in _compute_error."
        )
        return np.full((10, 1), np.nan), np.full((10, 1), np.nan)

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


# Actual interface with matplotlib
def _make_a_subplot(
    axe: Axes,
    x_axis: X_AXIS_T,
    y_axis: str,
    colors: dict[str, str] | None,
    *accelerators: Accelerator,
    plot_section: bool = True,
    symetric_plot: bool = False,
    **kwargs,
) -> None:
    """Get proper data and plot it on an Axe."""
    if plot_section:
        structure.outline_sections(accelerators[0].elts, axe, x_axis=x_axis)

    if y_axis == "struct":
        return structure.plot_structure(
            accelerators[-1].elts, axe, x_axis=x_axis
        )

    all_my_data = _all_accelerators_data(x_axis, y_axis, *accelerators)

    # Alternate markers for the "cav" preset
    markers = ("o", "^")
    marker_index = 0

    for x_data, y_data, plt_kwargs in zip(
        all_my_data[0], all_my_data[1], all_my_data[2]
    ):
        # Check if we are in the "cav" preset and assign markers alternately
        if y_axis in ("v_cav_mv", "phi_s"):
            plt_kwargs["marker"] = markers[marker_index]
            marker_index = (marker_index + 1) % len(markers)

        if colors is not None and plt_kwargs["label"] in colors:
            plt_kwargs["color"] = colors[plt_kwargs["label"]]

        (line,) = axe.plot(x_data, y_data, **plt_kwargs)

        if symetric_plot:
            symetric_kwargs = plt_kwargs | {
                "color": line.get_color(),
                "label": None,
            }
            axe.plot(x_data, -y_data, **symetric_kwargs)

    axe.grid(True)
    axe.set_ylabel(_y_label(y_axis))


# =============================================================================
# General plots
# =============================================================================
def plot_pty_with_data_tags(ax, x, y, idx_list, tags=True):
    """Plot y vs x.

    Data at idx_list are magnified with bigger points and data tags.

    """
    (line,) = ax.plot(x, y)
    ax.scatter(x[idx_list], y[idx_list], color=line.get_color())

    if tags:
        n = len(idx_list)
        for i in range(n):
            txt = (
                str(np.round(x[idx_list][i], 4))
                + ","
                + str(np.round(y[idx_list][i], 4))
            )
            ax.annotate(txt, (x[idx_list][i], y[idx_list[i]]), size=8)


# =============================================================================
# Optimization related
# =============================================================================
def _mark_objective_position(
    axis: Axes,
    objectives: Collection[Objective],
    x_axis: X_AXIS_T = "z_abs",
) -> None:
    """Show where objectives are evaluated."""
    objectives_by_element = by_element(objectives)


# =============================================================================
# Specific plots: emittance ellipse
# =============================================================================
def _compute_ellipse_parameters(d_eq):
    """
    Compute the ellipse parameters so as to plot the ellipse.

    Parameters
    ----------
    d_eq : dict
        Holds ellipe equations parameters, defined as:
            Ax**2 + Bxy + Cy**2 + Dx + Ey + F = 0

    Return
    ------
    d_plot : dict
        Holds semi axis, center of ellipse, angle.
    """
    delta = d_eq["B"] ** 2 - 4.0 * d_eq["A"] * d_eq["C"]
    tmp1 = (
        d_eq["A"] * d_eq["E"] ** 2
        - d_eq["C"] * d_eq["D"] ** 2
        - d_eq["B"] * d_eq["D"] * d_eq["E"]
        + delta * d_eq["F"]
    )
    tmp2 = np.sqrt((d_eq["A"] - d_eq["C"]) ** 2 + d_eq["B"] ** 2)

    if np.abs(d_eq["B"]) < 1e-8:
        if d_eq["A"] < d_eq["C"]:
            theta = 0.0
        else:
            theta = np.pi / 2.0
    else:
        theta = np.arctan((d_eq["C"] - d_eq["A"] - tmp2) / d_eq["B"])

    d_plot = {
        "a": -np.sqrt(2.0 * tmp1 * (d_eq["A"] + d_eq["C"] + tmp2)) / delta,
        "b": -np.sqrt(2.0 * tmp1 * (d_eq["A"] + d_eq["C"] - tmp2)) / delta,
        "x0": (2.0 * d_eq["C"] * d_eq["D"] - d_eq["B"] * d_eq["E"]) / delta,
        "y0": (2.0 * d_eq["A"] * d_eq["E"] - d_eq["B"] * d_eq["D"]) / delta,
        "theta": theta,
    }
    return d_plot


def plot_ellipse(axx, d_eq, **plot_kwargs):
    """Perform the proper ellipse plotting."""
    d_plot = _compute_ellipse_parameters(d_eq)
    n_points = 10001
    var = np.linspace(0.0, 2.0 * np.pi, n_points)
    ellipse = np.array([d_plot["a"] * np.cos(var), d_plot["b"] * np.sin(var)])
    rotation = np.array(
        [
            [np.cos(d_plot["theta"]), -np.sin(d_plot["theta"])],
            [np.sin(d_plot["theta"]), np.cos(d_plot["theta"])],
        ]
    )
    ellipse_rot = np.empty((2, n_points))

    for i in range(n_points):
        ellipse_rot[:, i] = np.dot(rotation, ellipse[:, i])

    axx.plot(
        d_plot["x0"] + ellipse_rot[0, :],
        d_plot["y0"] + ellipse_rot[1, :],
        lw=0.0,
        marker="o",
        ms=0.5,
        **plot_kwargs,
    )


# TODO: move dicts into the function dedicated to dicts creation
def plot_ellipse_emittance(axx, accelerator, idx, phase_space="w"):
    """Plot the emittance ellipse and highlight interesting data."""
    # Extract Twiss and emittance at the index idx
    twi = accelerator.get("twiss_" + phase_space)[idx]
    eps = accelerator.get("eps_ " + phase_space)[idx]

    # Compute ellipse dimensions; ellipse equation:
    # Ax**2 + Bxy + Cy**2 + Dx + Ey + F = 0
    d_eq = {
        "A": twi[2],
        "B": 2.0 * twi[0],
        "C": twi[1],
        "D": 0.0,
        "E": 0.0,
        "F": -eps,
    }

    # Plot ellipse
    colors = {"Working": "k", "Broken": "r", "Fixed": "g"}
    color = colors[accelerator.name.split(" ")[0]]
    plot_kwargs = {"c": color}
    plot_ellipse(axx, d_eq, **plot_kwargs)

    # Set proper labels
    d_xlabel = {
        "z": r"Position $z$ [mm]",
        "zdelta": r"Position $z$ [mm]",
        "w": r"Phase $\phi$ [deg]",
    }
    axx.set_xlabel(d_xlabel[phase_space])

    d_ylabel = {
        "z": r"Speed $z'$ [%]",
        "zdelta": r"Speed $\delta p/p$ [mrad]",
        "w": r"Energy $W$ [MeV]",
    }
    axx.set_ylabel(d_ylabel[phase_space])

    form = "{:.3g}"
    # Max phase
    maxi_phi = np.sqrt(eps * twi[1])
    line = axx.axvline(maxi_phi, c="b")
    axx.axhline(-twi[0] * np.sqrt(eps / twi[1]), c=line.get_color())
    axx.get_xticklabels().append(
        plt.text(
            1.005 * maxi_phi,
            0.05,
            form.format(maxi_phi),
            va="bottom",
            rotation=90.0,
            transform=axx.get_xaxis_transform(),
            c=line.get_color(),
        )
    )

    # Max energy
    maxi_w = np.sqrt(eps * twi[2])
    line = axx.axhline(maxi_w)
    axx.axvline(-twi[0] * np.sqrt(eps / twi[2]), c=line.get_color())
    axx.get_yticklabels().append(
        plt.text(
            0.005,
            0.95 * maxi_w,
            form.format(maxi_w),
            va="top",
            rotation=0.0,
            transform=axx.get_yaxis_transform(),
            c=line.get_color(),
        )
    )

    axx.grid(True)


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
