"""Create some generic evaluators for :class:`.SimulationOutput.`"""

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.experimental.new_evaluator.simulation_output.i_simulation_output_evaluator import (
    GetKwargs,
    ISimulationOutputEvaluator,
)
from lightwin.experimental.plotter.pd_plotter import PandasPlotter
from lightwin.util.typing import GETTABLE_SIMULATION_OUTPUT_T


class AcceptanceEnergy(ISimulationOutputEvaluator):
    """Check that energy acceptance along linac is not too high."""

    _x_quantity = "elt_idx"
    _y_quantity = "acceptance_energy"
    _plot_kwargs = {"style": ["o", "r--", "r:"]}

    def __init__(
        self,
        max_acceptance: float,
        reference: SimulationOutput,
        fignum: int,
        plotter: PandasPlotter | None = None,
    ) -> None:
        """Instantiate with a reference simulation output."""
        get_kwargs = GetKwargs(keep_nan=True, to_deg=True)
        super().__init__(reference, fignum, plotter, get_kwargs=get_kwargs)
        self._max = max_acceptance

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return f"Along linac, {self._markdown} $< {self._max:0.2f}$"


class AcceptancePhase(AcceptanceEnergy):
    """Check that phase acceptance along linac is not too high."""

    _y_quantity = "acceptance_phi"


class Energy(ISimulationOutputEvaluator):
    """Check that beam final energy is close to that is expected."""

    _y_quantity = "w_kin"

    def __init__(
        self,
        max_percentage_rel_diff: float,
        reference: SimulationOutput,
        fignum: int,
        plotter: PandasPlotter | None = None,
    ) -> None:
        """Instantiate with a reference simulation output."""
        super().__init__(reference, fignum, plotter)
        self._max = max_percentage_rel_diff

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return f"At linac exit, {self._markdown} $< {self._max:0.2f}$%"

    @property
    def _markdown(self) -> str:
        return r"$\Delta$" + super()._markdown + " (absolute)"

    def post_treat(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Compute abs diff between energy in fix and ref linacs."""
        return (raw_df - self._ref_ydata[:, None]).abs()

    def evaluate(
        self,
        *simulation_outputs,
        nan_in_data_is_allowed: bool = False,
        **kwargs,
    ) -> tuple[list[bool], pd.DataFrame]:
        """Check that final energy difference is within limit."""
        df = self.post_treat(self._get(*simulation_outputs, **kwargs))
        last_values = df.iloc[[-1]]  # shape: (1, n_simulations)
        tests = [
            self._evaluate_single(
                last_values.iloc[:, i],
                lower_limit=self.lower_limit,
                upper_limit=self.upper_limit,
                nan_in_data_is_allowed=nan_in_data_is_allowed,
                **kwargs,
            )
            for i in range(last_values.shape[1])
        ]
        return tests, df


class EnvelopePhiW(ISimulationOutputEvaluator):
    """Check that envelope remains reasonable."""

    _y_quantity = "beta_phiw"

    def __init__(
        self,
        max_envelope: NDArray[np.float64] | float,
        reference: SimulationOutput,
        fignum: int,
        plotter: PandasPlotter | None = None,
    ) -> None:
        super().__init__(reference, fignum, plotter)
        self._max = max_envelope

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return f"Envelope {self._markdown} stays reasonable"


class LongitudinalEmittance(ISimulationOutputEvaluator):
    """Check that relative longitudinal emittance growth is acceptable."""

    _y_quantity = "eps_phiw"

    def __init__(
        self,
        max_percentage_rel_increase: float,
        reference: SimulationOutput,
        fignum: int,
        plotter: PandasPlotter | None = None,
    ) -> None:
        """Instantiate with a reference simulation output."""
        super().__init__(reference, fignum, plotter)

        self._ref_ydata = self._ref_ydata[0]  # single reference value
        self._max = max_percentage_rel_increase

    @property
    def _markdown(self) -> str:
        """Give the proper markdown."""
        return r"$\Delta\epsilon_{\phi W} / \epsilon_{\phi W}$ (ref $z=0$) [%]"

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return (
            r"Relative increase of $\epsilon_{\phi W} < "
            + f"{self._max:0.4f}$%"
        )

    def post_treat(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Compute relative diff w.r.t. reference value @ z = 0."""
        return 1e2 * (raw_df - self._ref_ydata) / self._ref_ydata


class LongitudinalMismatchFactor(ISimulationOutputEvaluator):
    """Check that mismatch factor at end is not too high."""

    _y_quantity = "mismatch_factor_zdelta"

    def __init__(
        self,
        max_mismatch: float,
        reference: SimulationOutput,
        fignum: int,
        plotter: PandasPlotter | None = None,
    ) -> None:
        """Instantiate with a reference simulation output."""
        super().__init__(reference, fignum, plotter)

        self._ref_ydata = np.array([0.0, 0.0])
        self._max = max_mismatch

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return f"At end of linac, {self._markdown} $< {self._max:0.2f}$"

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


class PowerLoss(ISimulationOutputEvaluator):
    """Check that the power loss is acceptable."""

    _y_quantity = "pow_lost"

    def __init__(
        self,
        max_percentage_increase: float,
        reference: SimulationOutput,
        fignum: int,
        plotter: PandasPlotter | None = None,
    ) -> None:
        """Instantiate with a reference simulation output."""
        super().__init__(reference, fignum, plotter)

        # First point is sometimes very high
        self._ref_ydata = self.post_treat(
            pd.DataFrame(self._ref_ydata)
        ).to_numpy()
        self._max_percentage_increase = max_percentage_increase
        self._max = 1e-2 * max_percentage_increase * np.sum(self._ref_ydata)

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return (
            self._markdown
            + f"< {self._max:.2f}W "
            + f"(+{self._max_percentage_increase:.2f}%)"
        )

    def post_treat(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Set the first point to 0 (sometimes it is inf in TW)."""
        df = raw_df.copy()
        df.iloc[0] = 0.0  # first point sometimes very high
        return df
        if raw_df.ndim == 1:
            raw_df[0] = 0.0
            return raw_df
        if raw_df.ndim == 2:
            raw_df[:, 0] = 0.0
            return raw_df
        raise ValueError(f"{raw_df = } not understood.")

    # def evaluate(
    #     self,
    #     *simulation_outputs,
    #     elts: Sequence[ListOfElements] | None = None,
    #     **kwargs,
    # ) -> tuple[list[bool], NDArray[np.float64]]:
    #     """Assert that lost power is lower than maximum."""
    #     all_post_treated = self.post_treat(
    #         self._get(*simulation_outputs, **kwargs)
    #     )
    #     tests: list[bool] = []
    #
    #     used_for_eval = np.sum(all_post_treated, axis=0)
    #     for data in used_for_eval:
    #         test = self._evaluate_single(
    #             data,
    #             lower_limit=self.lower_limit,
    #             upper_limit=self.upper_limit,
    #             **kwargs,
    #         )
    #         tests.append(test)
    #
    #     self.plot(
    #         all_post_treated,
    #         elts,
    #         lower_limits=[self.lower_limit for _ in simulation_outputs],
    #         upper_limits=[self.upper_limit for _ in simulation_outputs],
    #         **kwargs,
    #     )
    #     return tests, used_for_eval
    #


class SynchronousPhases(ISimulationOutputEvaluator):
    """Check that synchronous phases are within [-90deg, 0deg]."""

    _x_quantity = "elt_idx"
    _y_quantity = "phi_s"
    _plot_kwargs = {"style": ["o", "r--", "r:"]}

    def __init__(
        self,
        min_phi_s_deg: float,
        max_phi_s_deg: float,
        reference: SimulationOutput,
        fignum: int,
        plotter: PandasPlotter | None = None,
    ) -> None:
        """Instantiate with a reference simulation output."""
        get_kwargs = GetKwargs(keep_nan=True, to_deg=True)
        super().__init__(reference, fignum, plotter, get_kwargs=get_kwargs)
        self._min = min_phi_s_deg
        self._max = max_phi_s_deg

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return (
            f"All {self._markdown} are within [{self._min:0.2f}, "
            f"{self._max:-.2f}] (deg)"
        )


class TransverseMismatchFactor(LongitudinalMismatchFactor):
    """Check that mismatch factor at end is not too high."""

    _y_quantity = "mismatch_factor_t"

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return f"At end of linac, {self._markdown} $< " f"{self._max:0.2f}$"


SIMULATION_OUTPUT_EVALUATORS = {
    "AcceptanceEnergy": AcceptanceEnergy,
    "AcceptancePhase": AcceptancePhase,
    "Energy": Energy,
    "EnvelopePhiW": EnvelopePhiW,
    "LongitudinalEmittance": LongitudinalEmittance,
    "LongitudinalMismatchFactor": LongitudinalMismatchFactor,
    "PowerLoss": PowerLoss,
    "SynchronousPhases": SynchronousPhases,
    "TransverseMismatchFactor": TransverseMismatchFactor,
}
