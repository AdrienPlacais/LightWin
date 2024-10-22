"""Gather the configurations for the different :class:`.BeamCalculator`."""

from lightwin.new_config.specs.beam_calculator_envelope1d_specs import (
    ENVELOPE1D_CONFIG,
    ENVELOPE1D_MONKEY_PATCHES,
)
from lightwin.new_config.specs.beam_calculator_envelope3d_specs import (
    ENVELOPE3D_CONFIG,
    ENVELOPE3D_MONKEY_PATCHES,
)
from lightwin.new_config.specs.beam_calculator_tracewin_specs import (
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
