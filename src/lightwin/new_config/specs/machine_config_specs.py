"""Define how :file:`machine_config_file.toml` should be set."""

from pathlib import Path

from lightwin.new_config.specs_base_objects import KeyValConfSpec

MACHINE_CONFIG_CONFIG = (
    KeyValConfSpec(
        key="noX11_full",
        types=(str, Path),
        description="Path to the ``TraceWin_noX11`` executable.",
        default_value="",
        is_mandatory=False,
        is_a_path_that_must_exists=True,
    ),
    KeyValConfSpec(
        key="noX11_minimal",
        types=(str, Path),
        description="Path to the ``tracelx`` executable.",
        default_value="",
        is_mandatory=False,
        is_a_path_that_must_exists=True,
    ),
    KeyValConfSpec(
        key="X11_full",
        types=(str, Path),
        description="Path to the ``TraceWin`` executable.",
        default_value="",
        is_mandatory=False,
        is_a_path_that_must_exists=True,
    ),
    KeyValConfSpec(
        key="no_run",
        types=(str, Path),
        description="Empty string to avoid running TraceWin.",
        default_value="",
        allowed_values=("",),
        is_mandatory=False,
        warning_message="The `no_run` option is for debug purposes only.",
    ),
)
