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
from lightwin.experimental.plotter.matplotlib_plotter import MatplotlibPlotter
from lightwin.util.typing import (
    GET_ELT_ARG_T,
    GETTABLE_SIMULATION_OUTPUT_T,
    NEEDS_3D,
    NEEDS_MULTIPART,
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
    #: Whether a NaN in the data array systematically makes the test fail.
    _nan_in_data_is_allowed: bool = False
    #: Whether we should worry if the reference data is not found. Set it to
    #: False for mismatch factor, which is defined for altered linacs only.
    _missing_reference_data_is_worrying: bool = True
    #: Whether reference data should be tested and plotted.
    _add_reference: bool = True

    def __init__(
        self,
        reference: SimulationOutput,
        fignum: int,
        plotter: MatplotlibPlotter | None = None,
        get_kwargs: GetKwargs | None = None,
        **kwargs,
    ) -> None:
        """``get`` reference data and compute limits."""
        super().__init__(fignum, plotter)
        self._dump_no_numerical_data_to_plot: bool = False

        self._ref = reference
        self._get_kwargs = get_kwargs if get_kwargs else GetKwargs()

        #: Reference ``x`` data. If necessary, ``y`` data will interpolated on
        #: this array.
        self._ref_xdata = self._get_single(reference, self._x_quantity)
        self._n_points = len(self._ref_xdata)

        #: Reference ``y`` data. Not post-treated.
        self._ref_ydata = self._get_single(
            reference,
            self._y_quantity,
            fallback_dummy=not self._missing_reference_data_is_worrying,
        )
        if np.isnan(self._ref_ydata).any():
            logging.error(
                f"No valid {self._y_quantity} was found in reference "
                f"simulation output, obtained with {reference.beam_calculator}"
                " solver. This will cause interpolation errors."
            )
        self._min: float | NDArray[np.float64] | None = None
        self._max: float | NDArray[np.float64] | None = None

    @final
    def _default_dummy(
        self, quantity: GETTABLE_SIMULATION_OUTPUT_T, warn: bool = True
    ) -> NDArray[np.float64]:
        """Give dummy ydata, with expected shape if possible.

        Also, set ``_dump_no_numerical_data_to_plot`` to avoid future pandas
        plotter errors.

        """
        self._dump_no_numerical_data_to_plot = True
        if hasattr(self, "_ref_ydata"):
            if warn:
                logging.error(
                    f"{quantity = } was not found in the simulation output. "
                    "Maybe the simulation was interrupted? Returning dummy data."
                )
            return np.full_like(self._ref_ydata, np.nan)
        if hasattr(self, "_ref_xdata"):
            if warn:
                logging.error(
                    f"Reference {quantity = } was not found in the simulation"
                    " output. Maybe the simulation parameters are invalid, or "
                    "the BeamCalculator does not produce this data? Returning "
                    "dummy data."
                )
            return np.full_like(self._ref_xdata, np.nan)
        if warn:
            logging.critical(
                f"Reference {quantity = } data was not found and I could not "
                f"find fallback array ({self._x_quantity}). Returning a dummy "
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

        if fallback_dummy and (data is None or data.ndim == 0):
            warn = True
            if (quantity in NEEDS_3D and not simulation_output.is_3d) or (
                quantity in NEEDS_MULTIPART
                and not simulation_output.is_multiparticle
            ):
                warn = False
            return self._default_dummy(quantity, warn=warn)
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
            sim_out.beam_calculator: self._get_interpolated(
                sim_out, fallback_dummy=fallback_dummy
            )
            for sim_out in simulation_outputs
        }
        return pd.DataFrame(data, index=self._ref_xdata)

    @final
    def plot(
        self,
        post_treated: pd.DataFrame,
        elts: Sequence[ListOfElements] | None = None,
        png_folder: Path | None = None,
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
        if not self._get_kwargs["keep_nan"]:
            post_treated = post_treated.dropna(axis=1)

        axes = self._plot_single(
            post_treated,
            elts=elts[-1] if elts else None,
            dump_no_numerical_data_to_plot=self._dump_no_numerical_data_to_plot,
            x_axis=self._x_quantity,
            **kwargs,
        )

        n_rows = len(post_treated)
        lower_limits = lower_limits or [self.lower_limit] * n_rows
        upper_limits = upper_limits or [self.upper_limit] * n_rows
        limits = pd.DataFrame(
            {"Lower limit": lower_limits, "Upper limits": upper_limits},
            index=post_treated.index,
        )

        limits = limits.mask(limits.isna(), np.nan)
        limits = limits.astype(float)
        axes = self._plot_limits(limits, x_axis=self._x_quantity, axes=axes)
        if png_folder is not None:
            self._plotter.save_figure(
                axes, png_folder / f"{self._y_quantity}.png"
            )
        return axes

    def _evaluate_single(
        self,
        post_treated: pd.Series,
        lower_limit: NDArray[np.float64] | float | None = None,
        upper_limit: NDArray[np.float64] | float | None = None,
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

        Returns
        -------
            If the data is always within the given limits.

        """
        lower_limit = np.nan if lower_limit is None else lower_limit
        upper_limit = np.nan if upper_limit is None else upper_limit
        data = post_treated.to_numpy()

        is_under_upper = np.full_like(data, True, dtype=bool)
        mask = ~np.isnan(upper_limit)
        if self._nan_in_data_is_allowed:
            mask &= ~np.isnan(data)
        np.less_equal(data, upper_limit, where=mask, out=is_under_upper)

        is_above_lower = np.full_like(data, True, dtype=bool)
        mask = ~np.isnan(lower_limit)
        if self._nan_in_data_is_allowed:
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
        self, *simulation_outputs, **kwargs
    ) -> tuple[list[bool], pd.DataFrame]:
        """Check, for every ``simulation_output``, if test was passed.

        Parameters
        ----------
        simulation_outputs :
            All the objects to test.

        Returns
        -------
        list[bool]
            Wether the tests was passed, for every given :class:
            `.SimulationOutput`.
        pd.DataFrame
            Holds data used for the testing.

        """
        df = self.post_treat(self._get(*simulation_outputs, **kwargs))

        if self._add_reference:
            ref_post_treated = self.post_treat(self._get(self._ref))
            col = ref_post_treated.columns[0]
            df.insert(0, col + ", ref", ref_post_treated[col])

        tests = [
            self._evaluate_single(
                df[col],
                lower_limit=self.lower_limit,
                upper_limit=self.upper_limit,
                **kwargs,
            )
            for col in df.columns
        ]
        new_names = {
            col: f"{col} (ok)" if test else f"{col} (fail)"
            for col, test in zip(df.columns, tests)
        }
        df.rename(columns=new_names, inplace=True)
        if not self._add_reference:
            tests.insert(0, True)
        return tests, df
