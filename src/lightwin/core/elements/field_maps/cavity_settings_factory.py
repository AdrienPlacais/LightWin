"""Create :class:`.CavitySettings` from various contexts."""

import math
from collections.abc import Sequence

import numpy as np

from lightwin.core.elements.field_maps.cavity_settings import (
    REFERENCE_PHASES_T,
    STATUS_T,
    CavitySettings,
    CavityVars,
)
from lightwin.tracewin_utils.line import DatLine


class CavitySettingsFactory:
    """Base class to create :class:`.CavitySettings` objects."""

    def __init__(self, freq_bunch_mhz: float) -> None:
        """Instantiate factory, with attributes common to all cavities."""
        self.freq_bunch_mhz = freq_bunch_mhz

    def from_line_in_dat_file(
        self,
        line: DatLine,
        set_sync_phase: bool = False,
    ) -> CavitySettings:
        """Create the cavity settings as read in the ``DAT`` file."""
        k_e = float(line.splitted[6])
        phi_0 = math.radians(float(line.splitted[3]))
        reference = self._reference(
            bool(int(line.splitted[10])), set_sync_phase
        )
        status = "nominal"

        cavity_settings = CavitySettings(
            k_e, phi_0, reference, status, self.freq_bunch_mhz
        )
        return cavity_settings

    def from_optimisation_algorithm(
        self,
        base_settings: Sequence[CavitySettings],
        var: np.ndarray,
        reference: REFERENCE_PHASES_T,
        status: STATUS_T,
    ) -> list[CavitySettings]:
        """
        Create the cavity settings to try during/at the end of an optimization.

        Parameters
        ----------
        base_settings :
            Nominal cavity settings, serving as a "base" for creating the new
            :class:`.CavitySettings`.
        var :
            Holds amplitudes in the first half, phases in the second half.
        reference :
            Nature of the phase to use as reference for the optimization.
        status :
            Status of the cavities.

        """
        amplitudes = list(var[var.shape[0] // 2 :])
        phases = list(var[: var.shape[0] // 2])
        new_cavity_vars = (
            CavityVars(k_e, phi, status, reference)
            for k_e, phi in zip(amplitudes, phases, strict=True)
        )

        several_cavity_settings = [
            CavitySettings.copy(base, new_vars)
            for base, new_vars in zip(
                base_settings, new_cavity_vars, strict=True
            )
        ]
        return several_cavity_settings

    def _reference(
        self, absolute_phase_flag: bool, set_sync_phase: bool
    ) -> REFERENCE_PHASES_T:
        """Determine which phase will be the reference one."""
        if set_sync_phase:
            return "phi_s"
        if absolute_phase_flag:
            return "phi_0_abs"
        return "phi_0_rel"
