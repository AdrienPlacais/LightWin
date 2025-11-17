"""Create some generic evaluators for :class:`.SimulationOutput.`"""

from collections.abc import Iterable, Sequence
from typing import Any, override

import numpy as np
from numpy.typing import NDArray

from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.experimental.new_evaluator.simulation_output.i_simulation_output_evaluator import (
    ISimulationOutputEvaluator,
)
from lightwin.experimental.plotter.pd_plotter import PandasPlotter
from lightwin.util.typing import GETTABLE_SIMULATION_OUTPUT_T


class LongitudinalEmittance(ISimulationOutputEvaluator):
    """Check that relative longitudinal emittance growth is acceptable."""

    _y_quantity = "eps_phiw"
    _fignum = 110
    _constant_limits = True

    def __init__(
        self,
        max_percentage_rel_increase: float,
        reference: SimulationOutput,
        plotter: PandasPlotter | None = None,
    ) -> None:
        """Instantiate with a reference simulation output."""
        super().__init__(reference, plotter)

        self._ref_ydata = self._ref_ydata[0]
        self._max_percentage_rel_increase = max_percentage_rel_increase

    @property
    @override
    def _markdown(self) -> str:
        """Give the proper markdown."""
        return r"$\Delta\epsilon_{\phi W} / \epsilon_{\phi W}$ (ref $z=0$) [%]"

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return (
            r"Relative increase of $\epsilon_{\phi W} < "
            f"{self._max_percentage_rel_increase:0.4f}$%"
        )

    @override
    def post_treat(self, ydata: NDArray[np.float64]) -> NDArray[np.float64]:
        """Compute relative diff w.r.t. reference value @ z = 0."""
        if ydata.ndim in (1, 2):
            post_treated = 1e2 * (ydata - self._ref_ydata) / self._ref_ydata
            assert isinstance(ydata, np.ndarray)
            return post_treated
        raise ValueError

    @property
    def upper_limit(self) -> float:
        return self._max_percentage_rel_increase


class LongitudinalMismatchFactor(ISimulationOutputEvaluator):
    """Check that mismatch factor at end is not too high."""

    _y_quantity = "mismatch_factor_zdelta"
    _fignum = 112
    _constant_limits = True

    def __init__(
        self,
        max_mismatch: float,
        reference: SimulationOutput,
        plotter: PandasPlotter | None = None,
    ) -> None:
        """Instantiate with a reference simulation output."""
        super().__init__(reference, plotter)

        self._ref_ydata = [0.0, 0.0]
        self._max = max_mismatch

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return f"At end of linac, {self._markdown} $< {self._max:0.2f}$"

    @override
    def _get_single(
        self,
        simulation_output: SimulationOutput,
        quantity: GETTABLE_SIMULATION_OUTPUT_T,
        fallback_dummy: bool = True,
    ) -> NDArray[np.float64]:
        """Call the ``get`` method with proper kwarguments.

        Also skip calculation with reference accelerator, as mismatch will not
        be defined.

        """
        data = super()._get_single(
            simulation_output, quantity, fallback_dummy=False
        )
        if fallback_dummy and (data.ndim == 0 or data is None):
            if simulation_output.out_path.parent.stem == "000000_ref":
                self._dump_no_numerical_data_to_plot = True
                return np.full_like(self._ref_xdata, np.nan)
            return self._default_dummy(quantity)
        return data

    def evaluate(
        self,
        *simulation_outputs,
        elts: Sequence[ListOfElements] | None = None,
        plot_kwargs: dict[str, Any] | None = None,
        **kwargs,
    ) -> tuple[list[bool], NDArray[np.float64]]:
        """Assert that longitudinal emittance does not grow too much."""
        all_post_treated = self.post_treat(
            self.get(*simulation_outputs, **kwargs)
        )
        tests: list[bool] = []

        used_for_eval = all_post_treated[-1, :]
        for data in used_for_eval:
            test = self._evaluate_single(
                data,
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
        return tests, used_for_eval


class AcceptancePhase(ISimulationOutputEvaluator):
    """Check that phase acceptance along linac is not too high."""

    _y_quantity = "acceptance_phase"
    _fignum = 112
    _constant_limits = True

    def __init__(
        self,
        max_acceptance: float,
        reference: SimulationOutput,
        plotter: PandasPlotter | None = None,
    ) -> None:
        """Instantiate with a reference simulation output."""
        super().__init__(reference, plotter)
        self._max = max_acceptance

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return f"Along linac, {self._markdown} $< {self._max:0.2f}$"


class AcceptanceEnergy(ISimulationOutputEvaluator):
    """Check that energy acceptance along linac is not too high."""

    _y_quantity = "acceptance_energy"
    _fignum = 112
    _constant_limits = True

    def __init__(
        self,
        max_acceptance: float,
        reference: SimulationOutput,
        plotter: PandasPlotter | None = None,
    ) -> None:
        """Instantiate with a reference simulation output."""
        super().__init__(reference, plotter)
        self._max = max_acceptance

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return f"Along linac, {self._markdown} $< {self._max:0.2f}$"


class Energy(ISimulationOutputEvaluator):
    """Check that beam final energy is close to that is expected."""

    _y_quantity = "w_kin"
    _fignum = 112
    _constant_limits = True

    def __init__(
        self,
        max_percentage_rel_diff: float,
        reference: SimulationOutput,
        plotter: PandasPlotter | None = None,
    ) -> None:
        """Instantiate with a reference simulation output."""
        super().__init__(reference, plotter)
        self._max = max_percentage_rel_diff

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return f"At linac exit, {self._markdown} $< {self._max:0.2f}$"

    @property
    def _markdown(self) -> str:
        return r"\Delta" + super()._markdown

    def post_treat(self, ydata: NDArray[np.float64]) -> NDArray[np.float64]:
        """Compute abs diff between energy in fix and ref linacs."""
        return np.abs(ydata - self._ref_ydata)

    def evaluate(
        self,
        *simulation_outputs,
        elts: Sequence[ListOfElements] | None = None,
        plot_kwargs: dict[str, Any] | None = None,
        nan_in_data_is_allowed: bool = False,
        **kwargs,
    ) -> tuple[list[bool], NDArray[np.float64]]:
        return super().evaluate(
            *simulation_outputs,
            elts=elts,
            plot_kwargs=plot_kwargs,
            nan_in_data_is_allowed=nan_in_data_is_allowed,
            elt="last",
            **kwargs,
        )


class PowerLoss(ISimulationOutputEvaluator):
    """Check that the power loss is acceptable."""

    _y_quantity = "pow_lost"
    _fignum = 101
    _constant_limits = True

    def __init__(
        self,
        max_percentage_increase: float,
        reference: SimulationOutput,
        plotter: PandasPlotter | None = None,
    ) -> None:
        """Instantiate with a reference simulation output."""
        super().__init__(reference, plotter)

        # First point is sometimes very high
        self._ref_ydata = self.post_treat(self._ref_ydata)

        self._max_percentage_increase = max_percentage_increase
        self._max = 1e-2 * max_percentage_increase * np.sum(self._ref_ydata)

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return (
            self._markdown
            + f"< {self._max:.2f}W "
            + f"(+{self._max_percentage_increase:.2f}%)"
        )

    @override
    def post_treat(self, ydata: Iterable[float]) -> NDArray[np.float64]:
        """Set the first point to 0 (sometimes it is inf in TW)."""
        assert isinstance(ydata, np.ndarray)
        if ydata.ndim == 1:
            ydata[0] = 0.0
            return ydata
        if ydata.ndim == 2:
            ydata[:, 0] = 0.0
            return ydata
        raise ValueError(f"{ydata = } not understood.")

    def evaluate(
        self,
        *simulation_outputs,
        elts: Sequence[ListOfElements] | None = None,
        plot_kwargs: dict[str, Any] | None = None,
        **kwargs,
    ) -> tuple[list[bool], NDArray[np.float64]]:
        """Assert that lost power is lower than maximum."""
        all_post_treated = self.post_treat(
            self.get(*simulation_outputs, **kwargs)
        )
        tests: list[bool] = []

        used_for_eval = np.sum(all_post_treated, axis=0)
        for data in used_for_eval:
            test = self._evaluate_single(
                data,
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
        return tests, used_for_eval


class SynchronousPhases(ISimulationOutputEvaluator):
    """Check that synchronous phases are within [-90deg, 0deg]."""

    _x_quantity = "elt_idx"
    _y_quantity = "phi_s"
    _to_deg = True
    _fignum = 120
    _constant_limits = True

    def __init__(
        self,
        min_phi_s_deg: float,
        max_phi_s_deg: float,
        reference: SimulationOutput,
        plotter: PandasPlotter | None = None,
    ) -> None:
        """Instantiate with a reference simulation output."""
        super().__init__(reference, plotter)

        self._min = min_phi_s_deg
        self._max = max_phi_s_deg

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return (
            f"All {self._markdown} are within [{self._min:0.2f}, "
            f"{self._max:-.2f}] (deg)"
        )

    def evaluate(
        self,
        *simulation_outputs,
        elts: Sequence[ListOfElements] | None = None,
        plot_kwargs: dict[str, Any] | None = None,
        **kwargs,
    ) -> tuple[list[bool], NDArray[np.float64]]:
        """Assert that longitudinal emittance does not grow too much."""
        plot_kwargs = {
            "keep_nan": True,
            "style": ["o", "r--", "r:"],
            "x_axis": self._x_quantity,
        }.update(plot_kwargs or {})

        tests, _ = super().evaluate(
            *simulation_outputs,
            elts=elts,
            plot_kwargs=plot_kwargs,
            nan_in_data_is_allowed=True,
            **kwargs,
        )

        return tests, np.array([np.nan for _ in simulation_outputs])


class TransverseMismatchFactor(ISimulationOutputEvaluator):
    """Check that mismatch factor at end is not too high."""

    _y_quantity = "mismatch_factor_t"
    _fignum = 111
    _constant_limits = True

    def __init__(
        self,
        max_mismatch: float,
        reference: SimulationOutput,
        plotter: PandasPlotter | None = None,
    ) -> None:
        """Instantiate with a reference simulation output."""
        super().__init__(reference, plotter)

        self._ref_ydata = [0.0, 0.0]
        self._max = max_mismatch

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return f"At end of linac, {self._markdown} $< " f"{self._max:0.2f}$"

    @override
    def _get_single(
        self,
        simulation_output: SimulationOutput,
        quantity: GETTABLE_SIMULATION_OUTPUT_T,
        fallback_dummy: bool = True,
    ) -> NDArray[np.float64]:
        """Call the ``get`` method with proper kwarguments.

        Also skip calculation with reference accelerator, as mismatch will not
        be defined.

        """
        data = super()._get_single(
            simulation_output, quantity, fallback_dummy=False
        )
        if fallback_dummy and (data.ndim == 0 or data is None):
            if simulation_output.out_path.parent.stem == "000000_ref":
                self._dump_no_numerical_data_to_plot = True
                return np.full_like(self._ref_xdata, np.nan)
            return self._default_dummy(quantity)
        return data

    def evaluate(
        self,
        *simulation_outputs,
        elts: Sequence[ListOfElements] | None = None,
        plot_kwargs: dict[str, Any] | None = None,
        **kwargs,
    ) -> tuple[list[bool], NDArray[np.float64]]:
        """Assert that longitudinal emittance does not grow too much."""
        all_post_treated = self.post_treat(
            self.get(*simulation_outputs, **kwargs)
        )
        tests: list[bool] = []

        used_for_eval = all_post_treated[-1, :]
        for data in used_for_eval:
            test = self._evaluate_single(
                data,
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
        return tests, used_for_eval


SIMULATION_OUTPUT_EVALUATORS = {
    "LongitudinalEmittance": LongitudinalEmittance,
    "LongitudinalMismatchFactor": LongitudinalMismatchFactor,
    "PowerLoss": PowerLoss,
    "SynchronousPhases": SynchronousPhases,
    "TransverseMismatchFactor": TransverseMismatchFactor,
}
