"""Define how :class:`.Envelope3D` should be configured."""

from typing import Any

from lightwin.beam_calculation.beam_calculator_base_specs import (
    BEAM_CALCULATOR_BASE_CONFIG,
)
from lightwin.beam_calculation.deprecated_specs import (
    apply_deprecated_flag_phi_abs,
)
from lightwin.beam_calculation.envelope_3d.util import ENVELOPE3D_METHODS
from lightwin.config.key_val_conf_spec import KeyValConfSpec
from lightwin.config.table_spec import TableConfSpec

ENVELOPE3D_CONFIG = BEAM_CALCULATOR_BASE_CONFIG + (
    KeyValConfSpec(
        key="flag_cython",
        types=(bool,),
        description=(
            "Not implemented yet. If we should use the Cython implementation "
            "(faster)."
        ),
        default_value=False,
        is_mandatory=False,
        allowed_values=(False,),
        warning_message="Not implemented yet, will ignore this key.",
    ),
    KeyValConfSpec(
        key="method",
        types=(str,),
        description="Integration method.",
        default_value="RK4",
        allowed_values=ENVELOPE3D_METHODS,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="n_steps_per_cell",
        types=(int,),
        description=(
            "Number of integrating steps per cavity cell. Recommended value "
            "is 40."
        ),
        default_value=40,
        is_mandatory=False,
    ),
)


def envelope_3d_pre_treat(
    self: TableConfSpec, toml_table: dict[str, Any], **kwargs
) -> None:
    self._insert_defaults(toml_table, **kwargs)
    apply_deprecated_flag_phi_abs(self, toml_table, **kwargs)


ENVELOPE3D_MONKEY_PATCHES = {"_pre_treat": envelope_3d_pre_treat}
