"""Define how :class:`.TraceWin` should be configured.

.. todo::
    Handle args such as ``hide``.

.. todo::
    Handle the toml_configuration file

"""

from pathlib import Path

from lightwin.constants import example_ini, example_machine_config
from lightwin.new_config.config_specs import KeyValConfSpec

TRACEWIN_CONFIG = (
    KeyValConfSpec(
        key="tool",
        types=(str,),
        description="Name of the tool.",
        default_value="TraceWin",
        allowed_values=("TraceWin", "tracewin"),
    ),
    KeyValConfSpec(
        key="ini_path",
        types=(str, Path),
        description="Path to the ``.ini`` TraceWin file.",
        default_value=example_ini,
        is_a_path_that_must_exists=True,
    ),
    KeyValConfSpec(
        key="hide",
        types=(bool,),
        description="Provide this flag to forbid the GUI from showing up.",
        default_value=True,
    ),
    KeyValConfSpec(
        key="machine_config_file",
        types=(str, Path),
        description="Path to a file holding the paths to TW executables",
        default_value=example_machine_config,
        is_a_path_that_must_exists=True,
    ),
    KeyValConfSpec(
        key="partran",
        types=(int, bool),
        description="To activate/deactivate patran tracking.",
        default_value=0,
        allowed_values=(0, 1, True, False),
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="simulation_type",
        types=(str,),
        description="A key in the machine_config.toml file",
        default_value="noX11_full",
    ),
    KeyValConfSpec(
        key="upgrade",
        types=(str,),
        description="To update LightWin",
        default_value="",
        is_mandatory=False,
        error_message="Upgrading TraceWin from LightWin is not recommended.",
    ),
)
