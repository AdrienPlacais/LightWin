"""Gather the configurations for the different :class:`.BeamCalculator`."""

from lightwin.new_config.specs.beam_calculator_envelope1d_specs import (
    ENVELOPE1D_CONFIG,
)
from lightwin.new_config.specs.beam_calculator_tracewin_specs import (
    TRACEWIN_CONFIG,
)

BEAM_CALCULATORS_CONFIGS = {
    "TraceWin": TRACEWIN_CONFIG,
    "Envelope1D": ENVELOPE1D_CONFIG,
    # "Envelope3D": ENVELOPE3D_CONFIG,
}
