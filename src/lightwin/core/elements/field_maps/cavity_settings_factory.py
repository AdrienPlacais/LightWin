"""Create |CS| from various contexts."""

import math
from collections.abc import Sequence

from lightwin.core.elements.field_maps.cavity_settings import (
    CavitySettings,
    CavityVars,
)
from lightwin.tracewin_utils.line import DatLine
from lightwin.util.typing import REFERENCE_PHASES_T


class CavitySettingsFactory:
    """Base class to create |CS| objects."""

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
            k_e, phi_0, reference, status, self.freq_bunch_mhz, info="DAT"
        )
        return cavity_settings

    def for_optimisation_algorithm(
        self,
        base_settings: Sequence[CavitySettings],
        amplitudes: Sequence[float],
        phases: Sequence[float],
        reference: REFERENCE_PHASES_T,
    ) -> list[CavitySettings]:
        """Create the cavity settings to try during an optimization.

        Parameters
        ----------
        base_settings :
            Nominal cavity settings, serving as a "base" for creating the new
            |CS|.
        amplitudes :
            ``(n,)`` array of field amplitudes.
        phases :
            ``(n,)`` array of field phases.
        reference :
            Nature of the phase to use as reference for the optimization.

        """
        as_cavity_vars = (
            CavityVars(k_e, phi, "compensate (in progress)", reference)
            for k_e, phi in zip(amplitudes, phases, strict=True)
        )
        return [
            CavitySettings.copy(base, vars, info="optim algo")
            for base, vars in zip(base_settings, as_cavity_vars, strict=True)
        ]

    def _reference(
        self, absolute_phase_flag: bool, set_sync_phase: bool
    ) -> REFERENCE_PHASES_T:
        """Determine which phase will be the reference one."""
        if set_sync_phase:
            return "phi_s"
        if absolute_phase_flag:
            return "phi_0_abs"
        return "phi_0_rel"
