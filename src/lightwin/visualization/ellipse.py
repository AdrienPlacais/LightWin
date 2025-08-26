"""Define specific functions to plot emittance ellipses.

.. todo::
    Isometric view of emittance along the linac.
    Possibility to visualize a single particle trajectory along the emittance.
    Visualization of the acceptance.

"""

from typing import TypedDict

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes

from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.core.beam_parameters.phase_space.i_phase_space_beam_parameters import (
    PHASE_SPACE_T,
)


class EllipseEqParams(TypedDict):
    """Holds all the parameters to compute an emittance ellipse.

    ..math::

        Ax**2 + Bxy + Cy**2 + Dx + Ey + F = 0

    """

    A: float
    B: float
    C: float
    D: float
    E: float
    F: float


class EllipseParams(TypedDict):
    """Hold the parameters to plot an ellipse."""

    a: float
    b: float
    x0: float
    y0: float
    theta: float


def _compute_ellipse_parameters(ell_eq: EllipseEqParams):
    """Compute the ellipse parameters so as to plot the ellipse.

    Parameters
    ----------
    ell_eq :
        Holds ellipe equations parameters.

    Returns
    -------
        Holds semi axis, center of ellipse, angle.

    """
    delta = ell_eq["B"] ** 2 - 4.0 * ell_eq["A"] * ell_eq["C"]
    tmp1 = (
        ell_eq["A"] * ell_eq["E"] ** 2
        - ell_eq["C"] * ell_eq["D"] ** 2
        - ell_eq["B"] * ell_eq["D"] * ell_eq["E"]
        + delta * ell_eq["F"]
    )
    tmp2 = np.sqrt((ell_eq["A"] - ell_eq["C"]) ** 2 + ell_eq["B"] ** 2)

    if np.abs(ell_eq["B"]) < 1e-8:
        if ell_eq["A"] < ell_eq["C"]:
            theta = 0.0
        else:
            theta = np.pi / 2.0
    else:
        theta = np.arctan((ell_eq["C"] - ell_eq["A"] - tmp2) / ell_eq["B"])

    ell_param: EllipseParams = {
        "a": -np.sqrt(2.0 * tmp1 * (ell_eq["A"] + ell_eq["C"] + tmp2)) / delta,
        "b": -np.sqrt(2.0 * tmp1 * (ell_eq["A"] + ell_eq["C"] - tmp2)) / delta,
        "x0": (2.0 * ell_eq["C"] * ell_eq["D"] - ell_eq["B"] * ell_eq["E"])
        / delta,
        "y0": (2.0 * ell_eq["A"] * ell_eq["E"] - ell_eq["B"] * ell_eq["D"])
        / delta,
        "theta": theta,
    }
    return ell_param


def plot_ellipse(ax: Axes, ell_eq: EllipseEqParams, **plot_kwargs):
    """Plot the ellipse defined by ``ell_eq`` on ``ax``."""
    ell_param = _compute_ellipse_parameters(ell_eq)
    n_points = 10001
    var = np.linspace(0.0, 2.0 * np.pi, n_points)
    ellipse = np.array(
        [ell_param["a"] * np.cos(var), ell_param["b"] * np.sin(var)]
    )
    rotation = np.array(
        [
            [np.cos(ell_param["theta"]), -np.sin(ell_param["theta"])],
            [np.sin(ell_param["theta"]), np.cos(ell_param["theta"])],
        ]
    )
    ellipse_rot = np.empty((2, n_points))

    for i in range(n_points):
        ellipse_rot[:, i] = np.dot(rotation, ellipse[:, i])

    ax.plot(
        ell_param["x0"] + ellipse_rot[0, :],
        ell_param["y0"] + ellipse_rot[1, :],
        lw=0.0,
        marker="o",
        ms=0.5,
        **plot_kwargs,
    )


def plot_ellipse_emittance(
    ax: Axes, accelerator: Accelerator, idx: int, phase_space: PHASE_SPACE_T
):
    """Plot the emittance ellipse and highlight interesting data."""
    twiss = accelerator.get("twiss", phase_space=phase_space)[idx]
    eps = accelerator.get("eps", phase_space=phase_space)[idx]
    ell_eq: EllipseEqParams = {
        "A": twiss[2],
        "B": 2.0 * twiss[0],
        "C": twiss[1],
        "D": 0.0,
        "E": 0.0,
        "F": -eps,
    }

    colors = {"Working": "k", "Broken": "r", "Fixed": "g"}
    color = colors[accelerator.name.split(" ")[0]]
    plot_kwargs = {"c": color}
    plot_ellipse(ax, ell_eq, **plot_kwargs)

    xlabel, ylabel = ELLIPSE_LABELS.get(phase_space, ("default", "default"))
    ax.set(xlabel=xlabel, ylabel=ylabel)

    form = "{:.3g}"
    # Max phase
    maxi_phi = np.sqrt(eps * twiss[1])
    line = ax.axvline(maxi_phi, c="b")
    ax.axhline(-twiss[0] * np.sqrt(eps / twiss[1]), c=line.get_color())
    ax.get_xticklabels().append(
        plt.text(
            1.005 * maxi_phi,
            0.05,
            form.format(maxi_phi),
            va="bottom",
            rotation=90.0,
            transform=ax.get_xaxis_transform(),
            c=line.get_color(),
        )
    )

    # Max energy
    maxi_w = np.sqrt(eps * twiss[2])
    line = ax.axhline(maxi_w)
    ax.axvline(-twiss[0] * np.sqrt(eps / twiss[2]), c=line.get_color())
    ax.get_yticklabels().append(
        plt.text(
            0.005,
            0.95 * maxi_w,
            form.format(maxi_w),
            va="top",
            rotation=0.0,
            transform=ax.get_yaxis_transform(),
            c=line.get_color(),
        )
    )

    ax.grid(True)


ELLIPSE_LABELS = {
    "z": (r"Position $z$ [mm]", r"Speed $z'$ [%]"),
    "zdelta": (r"Position $z$ [mm]", r"Speed $\delta p/p$ [mrad]"),
    "phiw": (r"Phase $\phi$ [deg]", r"Energy $W$ [MeV]"),
}
