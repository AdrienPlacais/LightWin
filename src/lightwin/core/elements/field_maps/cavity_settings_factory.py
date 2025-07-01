"""Create :class:`.CavitySettings` from various contexts."""

import math
from collections.abc import Sequence

import numpy as np

from lightwin.core.elements.field_maps.cavity_settings import (
    REFERENCE_PHASES_T,
    STATUS_T,
    CavitySettings,
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
        """Create the cavity settings as read in the ``.dat`` file."""
        k_e = float(line.splitted[6])
        phi_0 = math.radians(float(line.splitted[3]))
        reference = self._reference(
            bool(int(line.splitted[10])), set_sync_phase
        )
        status = "nominal"

        cavity_settings = CavitySettings(
            k_e,
            phi_0,
            reference,
            status,
            self.freq_bunch_mhz,
            # length_m = 1e-3 * float(line.splitted[1])
        )
        return cavity_settings

    def from_optimisation_algorithm(
        self,
        base_settings: Sequence[CavitySettings],
        var: np.ndarray,
        reference: REFERENCE_PHASES_T,
        status: STATUS_T,
    ) -> list[CavitySettings]:
        """Create the cavity settings to try during an optimisation."""
        amplitudes = list(var[var.shape[0] // 2 :])
        phases = list(var[: var.shape[0] // 2])
        variables = zip(base_settings, amplitudes, phases, strict=True)

        several_cavity_settings = [
            CavitySettings.from_optimisation_algorithm(
                base, k_e, phi, status, reference
            )
            for base, k_e, phi in variables
        ]
        return several_cavity_settings

    def from_other_cavity_settings(
        self,
        cavity_settings: Sequence[CavitySettings],
        reference: REFERENCE_PHASES_T | None = None,
    ) -> list[CavitySettings]:
        """Create a copy of ``cavity_settings``, reference can be updated.

        Not used for the moment.

        """
        new_cavity_settings = [
            CavitySettings.from_other_cavity_settings(other, reference)
            for other in cavity_settings
        ]
        return new_cavity_settings

    def _reference(
        self,
        absolute_phase_flag: bool,
        set_sync_phase: bool,
    ) -> REFERENCE_PHASES_T:
        """Determine which phase will be the reference one."""
        if set_sync_phase:
            return "phi_s"
        if absolute_phase_flag:
            return "phi_0_abs"
        return "phi_0_rel"
