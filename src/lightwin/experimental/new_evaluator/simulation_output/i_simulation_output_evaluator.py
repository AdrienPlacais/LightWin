"""Define the base object for :class:`.SimulationOutput` evaluators."""

import logging
from collections.abc import Sequence
from dataclasses import dataclass
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
from lightwin.util.typing import (
    GET_ELT_ARG_T,
    GETTABLE_SIMULATION_OUTPUT_T,
    POS_T,
)


@dataclass
class GetKwargs(dict):
    """kwargs to forward to :meth:`.SimulationOutput.get`."""

    #: Element(s) at which quantities should be evaluated. Use it if evaluation
    #: takes too long. In general, we ``get`` data along the whole linac even
    #: if the test is evaluated at individual points for better plotting.
    elt: str | Element | GET_ELT_ARG_T | None = None
    #: If NaN values should be kept in the plot. Set it to True for quantities
    #: that are undefined for some elements, *eg* synchronous phase.
    keep_nan: bool = False
    #: Position in elements where quantities should be evaluated. Use it if
    #: evaluation takes too long. In general, we ``get`` data along the whole
    #: linac even if the test is evaluated at individual points for better
    #: plotting.
    pos: POS_T | None = None
    #: If value should be converted from :unit:`rad` to :unit:`def`. Should not
    #: be updated after object creation.
    to_deg: bool = False

    def __post_init__(self):
        super().update(
            elt=self.elt,
            keep_nan=self.keep_nan,
            none_to_nan=True,
            pos=self.pos,
            to_deg=self.to_deg,
            to_numpy=True,
        )


class ISimulationOutputEvaluator(IEvaluator):
    """Base class for :class:`.SimulationOutput` evaluations."""

    _x_quantity: GETTABLE_SIMULATION_OUTPUT_T = "z_abs"
    #: kwargs used for plotting. Note that the first line will be the data, the
    #: second will be the lower limit, and the last line to be plotted will be
    #: the upper limit.
    _plot_kwargs = {"style": ["-", "r--", "r:"]}
    _constant_limits: bool = True
    _dump_no_numerical_data_to_plot: bool = False

    def __init__(
        self,
        reference: SimulationOutput,
        fignum: int,
        plotter: PandasPlotter | None = None,
        get_kwargs: GetKwargs | None = None,
        **kwargs,
    ) -> None:
        """``get`` reference data and compute limits."""
        super().__init__(fignum, plotter)

        self._get_kwargs = get_kwargs if get_kwargs else GetKwargs()

        self._plot_kwargs["x_axis"] = self._x_quantity

        self._ref_xdata = self._get_single(reference, self._x_quantity)
        self._n_points = len(self._ref_xdata)
        self._ref_ydata = self._get_single(reference, self._y_quantity)

        self._min: float | NDArray[np.float64] | None = None
        self._max: float | NDArray[np.float64] | None = None

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
        """Call the ``get``  on a single object, handle default return value.

        You may want to override this method, for example with the
        ``mismatch_factor`` which is only defined for a non-reference linac.

        """
        data = simulation_output.get(quantity, **self._get_kwargs)
        if fallback_dummy and (data.ndim == 0 or data is None):
            return self._default_dummy(quantity)
        return data

    @final
    def _get_interpolated(
        self,
        simulation_output: SimulationOutput,
        fallback_dummy: bool = True,
    ) -> NDArray[np.float64]:
        """Give ydata from one simulation, with proper number of points."""
        ydata = self._get_single(
            simulation_output, self._y_quantity, fallback_dummy=fallback_dummy
        )
        if len(ydata) == self._n_points:
            return ydata
        xdata = self._get_single(
            simulation_output, self._x_quantity, fallback_dummy=fallback_dummy
        )
        return np.interp(self._ref_xdata, xdata, ydata)

    @final
    def _get(
        self,
        *simulation_outputs: SimulationOutput,
        fallback_dummy: bool = True,
    ) -> pd.DataFrame:
        """Get the data from the simulation outputs."""
        data = {
            f"sim_{i}": self._get_interpolated(
                sim_out, fallback_dummy=fallback_dummy
            )
            for i, sim_out in enumerate(simulation_outputs)
        }
        return pd.DataFrame(data, index=self._ref_xdata)

    @final
    def plot(
        self,
        post_treated: pd.DataFrame,
        elts: Sequence[ListOfElements] | None = None,
        png_folders: Sequence[Path] | None = None,
        lower_limits: (
            Sequence[NDArray[np.float64] | float | None] | None
        ) = None,
        upper_limits: (
            Sequence[NDArray[np.float64] | float | None] | None
        ) = None,
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
        n_cols = len(post_treated.columns)
        lower_limits = lower_limits or [self.lower_limit] * n_cols
        upper_limits = upper_limits or [self.upper_limit] * n_cols

        # lower_limits = (
        #     lower_limits if lower_limits else [None for _ in to_plot]
        # )
        # upper_limits = (
        #     upper_limits if upper_limits else [None for _ in to_plot]
        # )

        for i, col in enumerate(post_treated.columns):
            # elements = elts[i] if elts is not None else None
            # lower_val = (
            #     lower_limits[i] if lower_limits[i] is not None else np.nan
            # )
            # upper_val = (
            #     upper_limits[i] if upper_limits[i] is not None else np.nan
            # )

            data_as_pd = pd.DataFrame(
                {
                    "Data": post_treated[col],
                    "Lower limit": (
                        lower_limits[i]
                        if lower_limits[i] is not None
                        else np.nan
                    ),
                    "Upper limit": (
                        upper_limits[i]
                        if upper_limits[i] is not None
                        else np.nan
                    ),
                },
                index=post_treated.index,
            )
            if not self._get_kwargs["keep_nan"]:
                data_as_pd = data_as_pd.dropna(axis=1)

            axes = self._plot_single(
                data_as_pd,
                elts=elts[i] if elts else None,
                dump_no_numerical_data_to_plot=self._dump_no_numerical_data_to_plot,
                **kwargs,
            )
            if png_folders is not None:
                self._plotter.save_figure(
                    axes, png_folders[i] / f"{self._y_quantity}.png"
                )

    @final
    def _evaluate_single(
        self,
        post_treated: pd.Series,
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
        data = post_treated.to_numpy()

        is_under_upper = np.full_like(data, True, dtype=bool)
        mask = ~np.isnan(upper_limit)
        if nan_in_data_is_allowed:
            mask &= ~np.isnan(data)
        np.less_equal(data, upper_limit, where=mask, out=is_under_upper)

        is_above_lower = np.full_like(data, True, dtype=bool)
        mask = ~np.isnan(lower_limit)
        if nan_in_data_is_allowed:
            mask &= ~np.isnan(data)
        np.greater_equal(data, lower_limit, where=mask, out=is_above_lower)

        test = np.all(is_above_lower & is_under_upper, axis=0)
        return bool(test)

    @property
    def lower_limit(self) -> float | NDArray[np.float64] | None:
        """Give lower limit to be plotted.

        Override this method if you need more complex/specific limits.

        """
        return self._min

    @property
    def upper_limit(self) -> float | NDArray[np.float64] | None:
        """Give lower limit to be plotted.

        Override this method if you need more complex/specific limits.

        """
        return self._max

    def evaluate(
        self,
        *simulation_outputs,
        nan_in_data_is_allowed: bool = False,
        **kwargs,
    ) -> tuple[list[bool], pd.DataFrame]:
        """Check, for every ``simulation_output``, if test was passed.

        Parameters
        ----------
        simulation_outputs :
            All the objects to test.
        nan_in_data_is_allowed :
            If the test is valid where post-treated data is ``NaN``. Use for
            example with synchronous phases, which is ``NaN`` when not in a
            cavity.

        Returns
        -------
        list[bool]
            Wether the tests was passed, for every given :class:
            `.SimulationOutput`.
        pd.DataFrame
            Holds data used for the testing.

        """
        df = self.post_treat(self._get(*simulation_outputs, **kwargs))
        tests = [
            self._evaluate_single(
                df[col],
                lower_limit=self.lower_limit,
                upper_limit=self.upper_limit,
                nan_in_data_is_allowed=nan_in_data_is_allowed,
                **kwargs,
            )
            for col in df.columns
        ]
        return tests, df

        # self.plot(
        #     df,
        #     elts,
        #     lower_limits=[self.lower_limit for _ in simulation_outputs],
        #     upper_limits=[self.upper_limit for _ in simulation_outputs],
        #     **kwargs,
        # )
        # return tests, df[-1, :]
