"""Define how :class:`.TraceWin` should be configured.

.. todo::
    Handle args such as ``hide``.

.. todo::
    Handle the toml_configuration file

- Could implement directly providing ``executable`` to override the
  ``machine_config_file`` settings.


"""

from pathlib import Path

from lightwin.constants import example_ini, example_machine_config
from lightwin.new_config.key_val_conf_spec import KeyValConfSpec

TRACEWIN_CONFIG = (
    # ======================== pure TraceWin ==================================
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
        description="Hide the GUI, or cancel console output (no parameter).",
        default_value=True,
    ),
    KeyValConfSpec(
        key="nbr_thread",
        types=(int,),
        description="Set the max. number of core/thread used",
        default_value=8,
        is_mandatory=False,
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
        key="synoptic_file",
        types=(str, Path),
        description="Save the geometric layout at (entance (=1), middle (=2), exit (=3) of elements. (See “Synoptic” tools for file name).",
        default_value=example_ini.with_stem(".syn"),
        is_a_path_that_must_exists=False,
        is_mandatory=False,
        warning_message="Not sure of this argument meaning.",
    ),
    KeyValConfSpec(
        key="tab_file",
        types=(str, Path),
        description="Save to file the data sheet at the end of calcul (by default in calculation directory).",
        default_value=example_ini.with_stem(".tab"),
        is_a_path_that_must_exists=False,
        is_mandatory=False,
        warning_message="Not sure of this argument meaning.",
    ),
    KeyValConfSpec(
        key="upgrade",
        types=(str,),
        description="To update LightWin",
        default_value="",
        is_mandatory=False,
        error_message="Upgrading TraceWin from LightWin is a bad idea.",
    ),
    # ======================== LightWin =======================================
    KeyValConfSpec(
        key="machine_config_file",
        types=(str, Path),
        description="Path to a file holding the paths to TW executables",
        default_value=example_machine_config,
        is_a_path_that_must_exists=True,
    ),
    KeyValConfSpec(
        key="machine_name",
        types=(str,),
        description=(
            "Name of current machine. Must be a table name in "
            "``machine_config_file``. By default, do not provide it and let "
            "LightWin handle this part."
        ),
        default_value=None,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="simulation_type",
        types=(str,),
        description="A key in the machine_config.toml file",
        default_value="noX11_full",
    ),
    KeyValConfSpec(
        key="tool",
        types=(str,),
        description="Name of the tool.",
        default_value="TraceWin",
        allowed_values=("TraceWin", "tracewin"),
    ),
)
