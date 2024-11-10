"""Define helper functions to visualize elements."""

from typing import Literal

import matplotlib.patches as pat
import numpy as np
from matplotlib.axes import Axes

from lightwin.core.elements.aperture import Aperture
from lightwin.core.elements.bend import Bend
from lightwin.core.elements.drift import Drift
from lightwin.core.elements.edge import Edge
from lightwin.core.elements.element import Element
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.elements.field_maps.field_map_100 import FieldMap100
from lightwin.core.elements.field_maps.field_map_1100 import FieldMap1100
from lightwin.core.elements.field_maps.field_map_7700 import FieldMap7700
from lightwin.core.elements.quad import Quad
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.visualization.helper import X_AXIS_T


def patch_kwargs(
    elt: Element, x_axis: X_AXIS_T, idx: int | None = None
) -> dict:
    """Give kwargs for the patch function."""
    if idx is None:
        idx = elt.idx["dat_idx"]

    kwargs = {"x_0": idx, "width": 1, "elt": elt}
    if x_axis == "z_abs":
        kwargs["x_0"] = elt.get("abs_mesh")[0]
        kwargs["width"] = elt.length_m
    return kwargs


def _limits(elts: ListOfElements, x_axis: X_AXIS_T) -> tuple[float, float]:
    """Give the limits of the plot."""
    x_limits = (0, len(elts))
    if x_axis == "z_abs":
        x_limits = (elts[0].get("abs_mesh")[0], elts[-1].get("abs_mesh")[-1])
    return x_limits


def plot_structure(
    elts: ListOfElements, ax: Axes, x_axis: X_AXIS_T = "z_abs"
) -> None:
    """Plot structure of the linac under study."""
    for i, elt in enumerate(elts):
        patcher = PLOTTABLE_ELEMENTS.get(type(elt), _plot_drift)
        kwargs = patch_kwargs(elt, x_axis, i)
        ax.add_patch(patcher(**kwargs))

    ax.set(
        xlim=_limits(elts, x_axis),
        yticklabels=(),
        yticks=(),
        ylim=(-0.55, 0.55),
    )


def _plot_aperture(x_0: float, width: float, **kwargs) -> pat.Rectangle:
    """Add a thin line to show an aperture."""
    height = 1.0
    y_0 = -height * 0.5
    patch = pat.Rectangle((x_0, y_0), width, height, fill=False, lw=0.5)
    return patch


def _plot_bend(x_0: float, width: float, **kwargs) -> pat.Rectangle:
    """Add a greyed rectangle to show a bend."""
    height = 0.7
    y_0 = -height * 0.5
    patch = pat.Rectangle(
        (x_0, y_0), width, height, fill=True, fc="gray", lw=0.5
    )
    return patch


def _plot_drift(x_0: float, width: float, **kwargs) -> pat.Rectangle:
    """Add a little rectangle to show a drift."""
    height = 0.4
    y_0 = -height * 0.5
    patch = pat.Rectangle((x_0, y_0), width, height, fill=False, lw=0.5)
    return patch


def _plot_field_map(
    x_0: float, width: float, field_map: FieldMap, **kwargs
) -> pat.Ellipse:
    """Add an ellipse to show a field_map."""
    height = 1.0
    y_0 = 0.0
    colors = {
        "nominal": "green",
        "rephased (in progress)": "olive",
        "rephased (ok)": "olive",
        "failed": "red",
        "compensate (in progress)": "green",
        "compensate (ok)": "orange",
        "compensate (not ok)": "orange",
    }
    color = colors[field_map.get("status", to_numpy=False)]
    patch = pat.Ellipse(
        (x_0 + 0.5 * width, y_0),
        width,
        height,
        fill=True,
        lw=0.5,
        fc=color,
        ec="k",
    )
    return patch


def _plot_edge(x_0: float, width: float, **kwargs) -> pat.Rectangle:
    """Add a thin line to show an edge."""
    height = 1.0
    y_0 = -height * 0.5
    patch = pat.Rectangle((x_0, y_0), width, height, fill=False, lw=0.5)
    return patch


def _plot_quad(x_0: float, width: float, **kwargs) -> pat.Polygon:
    """Add a crossed large rectangle to show a quad."""
    height = 1.0
    y_0 = -height * 0.5
    path = np.array(
        (
            [x_0, y_0],
            [x_0 + width, y_0],
            [x_0 + width, y_0 + height],
            [x_0, y_0 + height],
            [x_0, y_0],
            [x_0 + width, y_0 + height],
            [np.nan, np.nan],
            [x_0, y_0 + height],
            [x_0 + width, y_0],
        )
    )
    patch = pat.Polygon(path, closed=False, fill=False, lw=0.5)
    return patch


def outline_sections(
    elts: ListOfElements,
    ax: Axes,
    x_axis: X_AXIS_T | Literal["last_elt_of_sec"] = "z_abs",
) -> None:
    """Add light grey rectangles behind the plot to show the sections."""
    dict_x_axis = {
        "last_elt_of_sec": lambda sec: sec[-1][-1],
        "z_abs": lambda elt: elts.get("z_abs", elt=elt, pos="out"),
        "elt_idx": lambda elt: elt.get("elt_idx") + 1,
    }
    x_ax = [0]
    sorted = elts.by_section_and_lattice
    assert sorted is not None

    for i, section in enumerate(sorted):
        elt = dict_x_axis["last_elt_of_sec"](section)
        x_ax.append(dict_x_axis[x_axis](elt))

    for i in range(len(x_ax) - 1):
        if i % 2 == 1:
            ax.axvspan(
                x_ax[i],
                x_ax[i + 1],
                ymin=-1e8,
                ymax=1e8,
                fill=True,
                alpha=0.1,
                fc="k",
            )


PLOTTABLE_ELEMENTS = {
    Aperture: _plot_aperture,
    Bend: _plot_bend,
    Drift: _plot_drift,
    Edge: _plot_edge,
    FieldMap: _plot_field_map,
    FieldMap100: _plot_field_map,
    FieldMap1100: _plot_field_map,
    FieldMap7700: _plot_field_map,
    Quad: _plot_quad,
}
