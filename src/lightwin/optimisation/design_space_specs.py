"""Define how the design space should be configured."""

from pathlib import Path
from typing import Any

from lightwin.config.key_val_conf_spec import KeyValConfSpec
from lightwin.config.table_spec import TableConfSpec
from lightwin.constants import example_constraints, example_variables
from lightwin.util.typing import DESIGN_SPACES

_DESIGN_SPACE_BASE = (
    KeyValConfSpec(
        key="design_space_preset",
        types=(str,),
        description="What are the variables and constraints.",
        allowed_values=DESIGN_SPACES,
        default_value="SyncPhaseAmplitude",
        is_mandatory=True,
    ),
    KeyValConfSpec(
        key="variable_names",
        types=(list, tuple),
        description="""What to use as variables if ``design_space_preset`` is
set to ``"UserDefined"``. In this case, this key is mandatory.""",
        default_value=("k_e", "phi_s"),
        is_mandatory=False,
        warning_message="""variable_names was given but is ignored as
design_space_preset is not 'UserDefined'.""",
    ),
    KeyValConfSpec(
        key="constraint_names",
        types=(list, tuple),
        description="""What to use as constraints if ``design_space_preset`` is
set to ``"UserDefined"``.""",
        default_value=(),
        is_mandatory=False,
        warning_message="""constraint_names was given but is ignored as
design_space_preset is not 'UserDefined'.""",
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
            "Path to the `CSV` holding constraints. Mandatory if `from_file` is `True`."
        ),
        default_value=example_constraints,
        is_mandatory=False,
        is_a_path_that_must_exists=True,
    ),
    KeyValConfSpec(
        key="variables_filepath",
        types=(str, Path),
        description=(
            "Path to the `CSV` holding variables. Mandatory if `from_file` is `True`."
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


class DesignSpaceConfSpec(TableConfSpec):
    """Set specifications for the design space."""

    def _pre_treat(self, toml_table: dict[str, Any], **kwargs) -> None:
        super()._pre_treat(toml_table, **kwargs)
        self._adapt_to_user_defined(toml_table)

    def _adapt_to_user_defined(self, toml_table: dict[str, Any]) -> None:
        """Update keys for user-defined design space preset.

        - Remove their default warnings.
        - Declate ``variable_names`` as mandatory.

        """
        design_space_preset = toml_table.get("design_space_preset")
        if design_space_preset is None:
            return
        if design_space_preset not in {"UserDefined", "user_defined"}:
            return

        keyval = self._get_proper_spec("design_space_preset")
        assert keyval is not None
        keyval.error_message = (
            "UserDefined design spaces are under implementation. Behavior may "
            "be undefined."
        )

        warning_to_remove = {"variable_names", "constraint_names"}
        now_mandatory = {"variable_names"}

        for name in warning_to_remove:
            keyval = self._get_proper_spec(name)
            if keyval is None:
                continue
            keyval.warning_message = None
            if name in now_mandatory:
                keyval.is_mandatory = True
