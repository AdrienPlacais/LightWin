"""Gather the configurations for the different :class:`.BeamCalculator`."""

from lightwin.beam_calculation.envelope_1d.specs import (
    ENVELOPE1D_CONFIG,
    ENVELOPE1D_MONKEY_PATCHES,
)
from lightwin.beam_calculation.envelope_3d.specs import (
    ENVELOPE3D_CONFIG,
    ENVELOPE3D_MONKEY_PATCHES,
)
from lightwin.beam_calculation.tracewin.specs import (
    TRACEWIN_CONFIG,
    TRACEWIN_MONKEY_PATCHES,
)

BEAM_CALCULATORS_CONFIGS = {
    "TraceWin": TRACEWIN_CONFIG,
    "Envelope1D": ENVELOPE1D_CONFIG,
    "Envelope3D": ENVELOPE3D_CONFIG,
}
BEAM_CALCULATOR_MONKEY_PATCHES = {
    "TraceWin": TRACEWIN_MONKEY_PATCHES,
    "Envelope1D": ENVELOPE1D_MONKEY_PATCHES,
    "Envelope3D": ENVELOPE3D_MONKEY_PATCHES,
}
