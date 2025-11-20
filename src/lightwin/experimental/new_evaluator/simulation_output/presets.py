"""Create some generic evaluators for :class:`.SimulationOutput.`"""

from typing import Any

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
from lightwin.experimental.plotter.matplotlib_plotter import MatplotlibPlotter
from lightwin.util.typing import GETTABLE_SIMULATION_OUTPUT_T


class AcceptanceEnergy(ISimulationOutputEvaluator):
    """Check that energy acceptance along linac is not too high."""

    _x_quantity = "elt_idx"
    _y_quantity = "acceptance_energy"
    _plot_kwargs = {"marker": "o"}
    _nan_in_data_is_allowed = True

    def __init__(
        self,
        min_acceptance: float,
        reference: SimulationOutput,
        fignum: int,
        plotter: MatplotlibPlotter | None = None,
    ) -> None:
        """Instantiate with a reference simulation output."""
        get_kwargs = GetKwargs(keep_nan=True, to_deg=True)
        super().__init__(reference, fignum, plotter, get_kwargs=get_kwargs)
        self._min = min_acceptance

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return f"Along linac, {self.markdown} $> {self._min:0.2f}$"


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
        plotter: MatplotlibPlotter | None = None,
    ) -> None:
        """Instantiate with a reference simulation output."""
        super().__init__(reference, fignum, plotter)
        self._max = max_percentage_rel_diff

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return f"At linac exit, {self._markdown} $< {self._max:0.2f}$%"

    @property
    def _markdown(self) -> str:
        return r"$\Delta$" + super().markdown + " (absolute)"

    def post_treat(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Compute abs diff between energy in fix and ref linacs."""
        return (raw_df - self.ref_ydata[:, None]).abs()

    def evaluate(
        self,
        *simulation_outputs,
        fallback_dummy: bool = True,
        use_last_row_only=True,
        **user_overrides: Any,
    ) -> tuple[list[bool], pd.DataFrame]:
        """Check that final energy difference is within limit."""
        return super().evaluate(
            *simulation_outputs,
            fallback_dummy=fallback_dummy,
            use_last_row_only=use_last_row_only,
            **user_overrides,
        )


class EnvelopePhiW(ISimulationOutputEvaluator):
    """Check that envelope remains reasonable."""

    _y_quantity = "beta_phiw"

    def __init__(
        self,
        max_envelope: NDArray[np.float64] | float,
        reference: SimulationOutput,
        fignum: int,
        plotter: MatplotlibPlotter | None = None,
    ) -> None:
        super().__init__(reference, fignum, plotter)
        self._max = max_envelope

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return f"Envelope {self.markdown} stays reasonable"


class LongitudinalEmittance(ISimulationOutputEvaluator):
    """Check that relative longitudinal emittance growth is acceptable."""

    _y_quantity = "eps_phiw"

    def __init__(
        self,
        max_percentage_rel_increase: float,
        reference: SimulationOutput,
        fignum: int,
        plotter: MatplotlibPlotter | None = None,
    ) -> None:
        """Instantiate with a reference simulation output."""
        super().__init__(reference, fignum, plotter)
        self._max = max_percentage_rel_increase

    @property
    def ref_ydata(self) -> float:
        """Give only value at linac entrance."""
        return super().ref_ydata[0]

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
        return 1e2 * (raw_df - self.ref_ydata) / self.ref_ydata


class LongitudinalMismatchFactor(ISimulationOutputEvaluator):
    """Check that mismatch factor at end is not too high."""

    _y_quantity = "mismatch_factor_zdelta"
    _missing_reference_data_is_worrying = False
    _add_reference = False

    def __init__(
        self,
        max_mismatch: float,
        reference: SimulationOutput,
        fignum: int,
        plotter: MatplotlibPlotter | None = None,
    ) -> None:
        """Instantiate with a reference simulation output."""
        super().__init__(reference, fignum, plotter)
        self._max = max_mismatch

    @property
    def ref_ydata(self) -> NDArray[np.float64]:
        """Return null array, because there is no reference mismatch."""
        return np.zeros_like(self.ref_xdata)

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return f"At end of linac, {self.markdown} $< {self._max:0.2f}$"

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
            if simulation_output.is_reference:
                self._dump_no_numerical_data_to_plot = True
                return np.full_like(self.ref_xdata, np.nan)
            return self._default_dummy(quantity)
        return data


class PowerLoss(ISimulationOutputEvaluator):
    """Check that the power loss is acceptable."""

    _y_quantity = "pow_lost"

    def __init__(
        self,
        max_losses: float,
        reference: SimulationOutput,
        fignum: int,
        plotter: MatplotlibPlotter | None = None,
    ) -> None:
        """Instantiate with a reference simulation output."""
        super().__init__(reference, fignum, plotter)
        self._max = max_losses

    @property
    def _markdown(self) -> str:
        return f"Accumulated {super().markdown}"

    @property
    def ref_xdata(self) -> NDArray[np.float64]:
        return super().ref_xdata

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return f"{self._markdown} < {self._max:.2f}W"

    def post_treat(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Compute cumulative sum of power losses.

        Also set first point to 0W, as it is sometimes inf. in TW.

        """
        df = raw_df.copy()
        df.iloc[0] = 0.0  # first point sometimes very high
        return df.cumsum()


class SynchronousPhases(ISimulationOutputEvaluator):
    """Check that synchronous phases are within [-90deg, 0deg]."""

    _x_quantity = "elt_idx"
    _y_quantity = "phi_s"
    _plot_kwargs = {"marker": "o"}
    _nan_in_data_is_allowed = True

    def __init__(
        self,
        min_phi_s_deg: float,
        max_phi_s_deg: float,
        reference: SimulationOutput,
        fignum: int,
        plotter: MatplotlibPlotter | None = None,
    ) -> None:
        """Instantiate with a reference simulation output."""
        get_kwargs = GetKwargs(keep_nan=True, to_deg=True)
        super().__init__(reference, fignum, plotter, get_kwargs=get_kwargs)
        self._min = min_phi_s_deg
        self._max = max_phi_s_deg

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return (
            f"All {self.markdown} are within [{self._min:0.2f}, "
            f"{self._max:-.2f}] (deg)"
        )


class TransverseMismatchFactor(LongitudinalMismatchFactor):
    """Check that mismatch factor at end is not too high."""

    _y_quantity = "mismatch_factor_t"

    def __repr__(self) -> str:
        """Give a short description of what this class does."""
        return f"At end of linac, {self.markdown} $< " f"{self._max:0.2f}$"


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
