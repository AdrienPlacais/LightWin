"""Define how the design space should be configured."""

from pathlib import Path

from lightwin.constants import example_constraints, example_variables
from lightwin.new_config.key_val_conf_spec import KeyValConfSpec
from lightwin.optimisation.design_space.factory import (
    DESIGN_SPACE_FACTORY_PRESETS,
)

_DESIGN_SPACE_BASE = (
    KeyValConfSpec(
        key="design_space_preset",
        types=(str,),
        description="What are the variables and constraints.",
        allowed_values=tuple(DESIGN_SPACE_FACTORY_PRESETS.keys()),
        default_value="SyncPhaseAmplitude",
        is_mandatory=True,
    ),
    KeyValConfSpec(
        key="from_file",
        types=(bool,),
        description=(
            "If variable limits/constraints should be taken from a file."
        ),
        default_value=False,
        is_mandatory=True,
    ),
)

DESIGN_SPACE_CALCULATED = _DESIGN_SPACE_BASE + (
    KeyValConfSpec(
        key="max_increase_sync_phase_in_percent",
        types=(float,),
        description=(
            r"Max relative increase of :math:`\phi_s` wrt nominal in "
            r":unit:`\\%`"
        ),
        default_value=40.0,
        is_mandatory=True,
    ),
    KeyValConfSpec(
        key="max_absolute_sync_phase_in_deg",
        types=(float,),
        description=r"Max absolute :math:`\phi_s` in :unit:`deg`",
        default_value=0.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="min_absolute_sync_phase_in_deg",
        types=(float,),
        description=(r"Min absolute :math:`\phi_s` in :unit:`deg`"),
        default_value=-90.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="max_decrease_k_e_in_percent",
        types=(float,),
        description=r"Max decrease of :math:`k_e` wrt nominal in :unit:`\\%`",
        default_value=30.0,
        is_mandatory=True,
    ),
    KeyValConfSpec(
        key="max_increase_k_e_in_percent",
        types=(float,),
        description=r"Max increase of :math:`k_e` wrt nominal in :unit:`\\%`",
        default_value=30.0,
        is_mandatory=True,
    ),
    KeyValConfSpec(
        key="maximum_k_e_is_calculated_wrt_maximum_k_e_of_section",
        types=(bool,),
        description=(
            r"If max :math:`k_e` should be the same for all the cavities of "
            "the section"
        ),
        default_value=False,
        is_mandatory=False,
    ),
)

DESIGN_SPACE_FROM_FILE = _DESIGN_SPACE_BASE + (
    KeyValConfSpec(
        key="constraints_filepath",
        types=(str, Path),
        description=(
            "Path to the ``.csv`` holding constraints. Mandatory if "
            "``from_file`` is ``True``."
        ),
        default_value=example_constraints,
        is_mandatory=False,
        is_a_path_that_must_exists=True,
    ),
    KeyValConfSpec(
        key="variables_filepath",
        types=(str, Path),
        description=(
            "Path to the ``.csv`` holding variables. Mandatory if "
            "``from_file`` is ``True``."
        ),
        default_value=example_variables,
        is_mandatory=True,
        is_a_path_that_must_exists=True,
    ),
)

DESIGN_SPACE_CONFIGS = {
    False: DESIGN_SPACE_CALCULATED,
    True: DESIGN_SPACE_FROM_FILE,
}
