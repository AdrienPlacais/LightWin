"""Define the base object for :class:`.SimulationOutput` evaluators."""

import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any, final

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.elements.element import Element
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.experimental.new_evaluator.i_evaluator import IEvaluator
from lightwin.experimental.plotter.pd_plotter import PandasPlotter
from lightwin.util.typing import GETTABLE_SIMULATION_OUTPUT_T, POS_T


class ISimulationOutputEvaluator(IEvaluator):
    """Base class for :class:`.SimulationOutput` evaluations."""

    _x_quantity: GETTABLE_SIMULATION_OUTPUT_T = "z_abs"
    #: If value should be converted from :unit:`rad` to :unit:`def`. Should not
    #: be updated after object creation.
    _to_deg: bool = False
    #: Element(s) at which quantities should be evaluated. Should not be
    #: updated after object creation.
    _elt: str | Element | None = None
    #: Position in elements where quantities should be evaluated. Should not be
    #: updated after object creation.
    _pos: POS_T | None = None
    _get_kwargs: dict[str, Any]
    _constant_limits: bool
    _dump_no_numerical_data_to_plot: bool = False

    _min: float | NDArray[np.float64] | None = None
    _max: float | NDArray[np.float64] | None = None

    def __init__(
        self,
        reference: SimulationOutput,
        plotter: PandasPlotter | None = None,
        get_kwargs: dict[str, Any] | None = None,
    ) -> None:
        """Instantiate with a reference simulation output."""
        super().__init__(plotter)

        self._get_kwargs = {
            "to_deg": self._to_deg,
            "to_numpy": True,
            "none_to_nan": True,
            "pos": self._pos,
            "elt": self._elt,
        }
        if get_kwargs:
            self._get_kwargs.update(get_kwargs)
        self._ref_xdata = self._get_single(reference, self._x_quantity)
        self._n_points = len(self._ref_xdata)
        self._ref_ydata = self._get_single(reference, self._y_quantity)

    @final
    def _default_dummy(
        self, quantity: GETTABLE_SIMULATION_OUTPUT_T
    ) -> NDArray[np.float64]:
        """Give dummy ydata, with expected shape if possible.

        Also, set ``_dump_no_numerical_data_to_plot`` to avoid future pandas
        plotter errors.

        """
        self._dump_no_numerical_data_to_plot = True
        if hasattr(self, "_ref_ydata"):
            logging.error(
                f"{quantity = } was not found in the simulation output. "
                "Maybe the simulation was interrupted? Returning dummy data."
            )
            return np.full_like(self._ref_ydata, np.nan)
        if hasattr(self, "_ref_xdata"):
            logging.error(
                f"Reference {quantity = } was not found in the simulation"
                " output. Maybe the simulation parameters are invalid, or "
                "the BeamCalculator does not produce this data? Returning "
                "dummy data."
            )
            return np.full_like(self._ref_xdata, np.nan)
        logging.critical(
            f"Reference {quantity = } data was not found and I could not "
            "find fallback array ({self._x_quantity}). Returning a very dummy "
            "array."
        )
        return np.full((10,), np.nan)

    def _get_single(
        self,
        simulation_output: SimulationOutput,
        quantity: GETTABLE_SIMULATION_OUTPUT_T,
        fallback_dummy: bool = True,
    ) -> NDArray[np.float64]:
        """Call the ``get`` and handle default return value."""
        data = simulation_output.get(quantity, **self._get_kwargs)
        if fallback_dummy and (data.ndim == 0 or data is None):
            return self._default_dummy(quantity)
        return data

    def _get_interpolated(
        self,
        simulation_output: SimulationOutput,
        interp: bool = True,
        **kwargs,
    ) -> NDArray[np.float64]:
        """Give ydata from one simulation, with proper number of points."""
        ydata = self._get_single(simulation_output, self._y_quantity)
        if not interp or len(ydata) == self._n_points:
            return ydata

        xdata = self._get_single(simulation_output, self._x_quantity)
        return np.interp(self._ref_xdata, xdata, ydata)

    def get(
        self, *simulation_outputs: SimulationOutput, **kwargs
    ) -> NDArray[np.float64]:
        """Get the data from the simulation outputs."""
        y_data = [
            self._get_interpolated(x, **kwargs) for x in simulation_outputs
        ]
        return np.column_stack(y_data)

    def plot(
        self,
        post_treated: NDArray[np.float64],
        elts: Sequence[ListOfElements] | None = None,
        png_folders: Sequence[Path] | None = None,
        lower_limits: (
            Sequence[NDArray[np.float64] | float | None] | None
        ) = None,
        upper_limits: (
            Sequence[NDArray[np.float64] | float | None] | None
        ) = None,
        keep_nan: bool = False,
        style: Sequence[str] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Plot all the post treated data using ``plotter``.

        Parameters
        ----------
        lower_limits :
            List of lower limits, one per column in ``post_treated``.
            Individual lower limits can be ``float`` (constant) or arrays.
        upper_limits :
            List of upper limits, one per column in ``post_treated``.
            Individual upper limits can be ``float`` (constant) or arrays.

        """
        if style is None:
            style = ["-", "r--", "r:"]

        to_plot = post_treated.T

        if not lower_limits:
            lower_limits = [None for _ in to_plot]
        if not upper_limits:
            upper_limits = [None for _ in to_plot]

        for i, data in enumerate(to_plot):
            elements = elts[i] if elts is not None else None
            lower_val = lower_limits[i] if lower_limits[i] else np.nan
            upper_val = upper_limits[i] if upper_limits[i] else np.nan

            data_as_dict = {
                "Data": data,
                "Lower limit": lower_val,
                "Upper limit": upper_val,
            }
            data_as_pd = pd.DataFrame(data_as_dict, index=self._ref_xdata)
            if not keep_nan:
                data_as_pd = data_as_pd.dropna(axis=1)
            axes = self._plot_single(
                data_as_pd,
                elements,
                style=style,
                dump_no_numerical_data_to_plot=self._dump_no_numerical_data_to_plot,
                **kwargs,
            )
            if png_folders is not None:
                self._plotter.save_figure(
                    axes, png_folders[i] / self.png_filename
                )

    @final
    def _evaluate_single(
        self,
        post_treated: NDArray[np.float64],
        lower_limit: NDArray[np.float64] | float | None = None,
        upper_limit: NDArray[np.float64] | float | None = None,
        nan_in_data_is_allowed: bool = False,
        **kwargs,
    ) -> bool:
        """Check that ``post_treated`` is within limits.

        Parameters
        ----------
        post_treated :
            Data, already post-treated. If there is ``np.nan`` in this array,
            we consider that the test if failed.
        lower_limit, upper_limit :
            Min/max value for data. Where it is ``np.nan``, the test is passed.
        nan_in_data_is_allowed :
            If the test is valid where ``post_treated`` is NaN. Use for example
            with synchronous phases, which is Nan when not in a cavity.

        Returns
        -------
            If the data is always within the given limits.

        """
        lower_limit = np.nan if lower_limit is None else lower_limit
        upper_limit = np.nan if upper_limit is None else upper_limit
        is_under_upper = np.full_like(post_treated, True, dtype=bool)
        where = ~np.isnan(upper_limit)
        if nan_in_data_is_allowed:
            where = where & ~np.isnan(post_treated)
        np.less_equal(
            post_treated,
            upper_limit,
            where=where,
            out=is_under_upper,
        )

        is_above_lower = np.full_like(post_treated, True, dtype=bool)
        where = ~np.isnan(lower_limit)
        if nan_in_data_is_allowed:
            where = where & ~np.isnan(post_treated)
        np.greater_equal(
            post_treated,
            lower_limit,
            where=where,
            out=is_above_lower,
        )
        test = np.all(is_above_lower & is_under_upper, axis=0)
        return bool(test)

    @property
    def png_filename(self) -> str:
        """Give a filename for consistent saving of figures."""
        return f"{self._y_quantity}.png"

    @property
    def lower_limit(self) -> float | NDArray[np.float64] | None:
        """Give lower limit to be plotted."""
        return self._min

    @property
    def upper_limit(self) -> float | NDArray[np.float64] | None:
        """Give lower limit to be plotted."""
        return self._max

    def evaluate(
        self,
        *simulation_outputs,
        elts: Sequence[ListOfElements] | None = None,
        plot_kwargs: dict[str, Any] | None = None,
        nan_in_data_is_allowed: bool = False,
        **kwargs,
    ) -> tuple[list[bool], NDArray[np.float64]]:
        """Check and plot."""
        all_post_treated = self.post_treat(
            self.get(*simulation_outputs, **kwargs)
        )
        tests: list[bool] = []

        for post_treated in all_post_treated.T:
            test = self._evaluate_single(
                post_treated,
                lower_limit=self.lower_limit,
                upper_limit=self.upper_limit,
                **kwargs,
            )
            tests.append(test)

        self.plot(
            all_post_treated,
            elts,
            lower_limits=[self.lower_limit for _ in simulation_outputs],
            upper_limits=[self.upper_limit for _ in simulation_outputs],
            **(plot_kwargs or {}),
            **kwargs,
        )
        return tests, all_post_treated[-1, :]
