"""Define how :class:`.Envelope1D` should be configured."""

from lightwin.beam_calculation.envelope_1d.util import ENVELOPE1D_METHODS
from lightwin.config.key_val_conf_spec import KeyValConfSpec
from lightwin.util.typing import EXPORT_PHASES

ENVELOPE1D_CONFIG = (
    KeyValConfSpec(
        key="export_phase",
        types=(str,),
        description=(
            "The type of phases that should be exported in the final DAT "
            "file. Note that `'as_in_original_dat'` is not implemented "
            "yet, but `'as_in_settings'` should behave the same way, "
            "provided that you alter no FieldMap.CavitySettings.reference "
            "attribute."
        ),
        default_value="as_in_settings",
        allowed_values=EXPORT_PHASES,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="flag_cython",
        types=(bool,),
        description="If we should use the Cython implementation (faster).",
        default_value=False,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="flag_phi_abs",
        types=(bool,),
        description=(
            "If the field maps phases should be absolute (no implicit "
            "rephasing after a failure)."
        ),
        default_value=True,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="method",
        types=(str,),
        description="Integration method.",
        default_value="RK4",
        allowed_values=ENVELOPE1D_METHODS,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="n_steps_per_cell",
        types=(int,),
        description=(
            "Number of integrating steps per cavity cell. Recommended values "
            "are 40 for RK4 and 20 for leapfrog."
        ),
        default_value=40,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="tool",
        types=(str,),
        description="Name of the tool.",
        default_value="Envelope1D",
        allowed_values=(
            "Envelope1D",
            "envelope1d",
            "Envelope_1D",
            "envelope_1d",
        ),
    ),
)

ENVELOPE1D_MONKEY_PATCHES = {}
