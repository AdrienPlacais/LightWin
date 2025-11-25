"""Define configuration entries that are common to all :class:`.BeamCalculator`."""

from types import NoneType

from lightwin.config.key_val_conf_spec import KeyValConfSpec
from lightwin.util.typing import EXPORT_PHASES, REFERENCE_PHASE_POLICY

#: Configuration entries common to all beam calculators.
BEAM_CALCULATOR_BASE_CONFIG = (
    KeyValConfSpec(
        key="export_phase",
        types=(str,),
        description=(
            "The type of phases that should be exported in the final `DAT` "
            "file. Note that `'as_in_original_dat'` is not implemented "
            "yet, but `'as_in_settings'` should behave the same way, "
            "provided that you alter no FieldMap.CavitySettings.reference "
            "attribute."
        ),
        default_value="as_in_settings",
        allowed_values=EXPORT_PHASES,
        is_mandatory=True,
    ),
    KeyValConfSpec(
        key="reference_phase_policy",
        types=(str,),
        description=(
            "Controls cavities reference phase. More details in :ref:"
            "`dedicated notebook<notebooks-cavities-reference-phase>`. With "
            "TraceWin solver, prefer sticking with `'phi_0_rel'`."
        ),
        default_value="phi_0_rel",
        allowed_values=REFERENCE_PHASE_POLICY,
        is_mandatory=True,
    ),
    KeyValConfSpec(
        key="flag_phi_abs",
        types=(bool, NoneType),
        description=(
            "DEPRECATED, prefer use of `reference_phase_policy`. "
            "If the field maps phases should be absolute (no implicit "
            "rephasing after a failure)."
        ),
        default_value=None,
        is_mandatory=False,
        warning_message=(
            "The ``flag_phi_abs`` option is deprecated, prefer using the "
            "``reference_phase_policy``.\nflag_phi_abs=False -> "
            "reference_phase_policy='phi_0_rel'\nflag_phi_abs=True -> "
            "reference_phase_policy='phi_0_abs'"
        ),
    ),
    KeyValConfSpec(
        key="tool",
        types=(str,),
        description="Name of the tool.",
        default_value="Envelope1D",
        allowed_values=(
            "Envelope1D",
            "Envelope3D",
            "Envelope_1D",
            "Envelope_3D",
            "TraceWin",
            "envelope1d",
            "envelope3d",
            "envelope_1d",
            "envelope_3d",
            "tracewin",
        ),
    ),
)
