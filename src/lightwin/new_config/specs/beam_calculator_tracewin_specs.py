"""Define how :class:`.TraceWin` should be configured.

.. todo::
    Handle args such as ``hide``.

.. note::
    In this module we also define ``MONKEY_PATCHES``. They are used to modify
    the ``_pre_treat``, ``validate`` and ``_post_treat`` methods from
    :class:`.TableConfSpec`.

"""

import socket
import tomllib
from pathlib import Path
from typing import Any

from lightwin.config.helper import find_file
from lightwin.constants import example_ini, example_machine_config
from lightwin.new_config.key_val_conf_spec import KeyValConfSpec
from lightwin.new_config.table_spec import TableConfSpec

_PURE_TRACEWIN_CONFIG = (
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
)  #: Arguments that can be passed to TraceWin CLI

TRACEWIN_CONFIG = _PURE_TRACEWIN_CONFIG + (
    KeyValConfSpec(
        key="base_kwargs",
        types=(dict,),
        description=(
            "Keyword arguments passed to TraceWin CLI. Internal use of "
            "LightWin onnly."
        ),
        default_value={},
        is_mandatory=False,
        warning_message=("Providing `base_kwargs` is not recommended."),
        derived=True,
    ),
    KeyValConfSpec(
        key="executable",
        types=(str, Path),
        description=(
            "Direct path to the TraceWin executable. If given, will override "
            "the definition in the machine_config_file."
        ),
        default_value="",
        is_a_path_that_must_exists=True,
        is_mandatory=False,
        warning_message=(
            "Providing `executable` will override `machine_config_file` "
            "settings."
        ),
    ),
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
)  #: Arguments for :class:`.TraceWin` object configuration


def tracewin_pre_treat(
    self: TableConfSpec, toml_subdict: dict[str, Any], **kwargs
) -> None:
    """Set the TW executable."""
    if "executable" in toml_subdict:
        declare = getattr(
            self, "_declare_that_machine_config_is_not_mandatory_anymore"
        )
        declare()
        return

    toml_subdict["executable"] = _get_tracewin_executable(
        **toml_subdict, **kwargs
    )


def tracewin_declare_that_machine_config_is_not_mandatory_anymore(
    self: TableConfSpec,
) -> None:
    """Update configuration to avoid checking some entries."""
    not_mandatory_anymore = ("machine_config_file", "simulation_type")
    for name in not_mandatory_anymore:
        keyval = self._get_proper_spec(name)
        if keyval is None:
            continue
        keyval.is_mandatory = False
        keyval.is_a_path_that_must_exists = False

    keyval = self._get_proper_spec("executable")
    if keyval is None:
        return
    keyval.overrides_previously_defined = True


def tracewin_post_treat(
    self: TableConfSpec, toml_subdict: dict[str, Any], **kwargs
) -> None:
    """Separate TraceWin/LightWin arguments."""
    new_toml_subdict = {"base_kwargs": {}}  # TraceWin arguments

    entries_to_remove = (
        "simulation_type",
        "machine_config_file",
        "machine_name",
    )
    lightwin_entries = ("tool",)

    for key, value in toml_subdict.items():
        if key in entries_to_remove:
            continue

        if key in lightwin_entries:
            new_toml_subdict[key] = value
            continue

        new_toml_subdict["base_kwargs"][key] = value

    toml_subdict.clear()
    for key, value in new_toml_subdict.items():
        toml_subdict[key] = value


TRACEWIN_MONKEY_PATCHES = {
    "_pre_treat": tracewin_pre_treat,
    "_declare_that_machine_config_is_not_mandatory_anymore": tracewin_declare_that_machine_config_is_not_mandatory_anymore,
    "_post_treat": tracewin_post_treat,
}


def _get_tracewin_executable(
    toml_folder: Path,
    machine_config_file: str | Path,
    simulation_type: str | Path,
    machine_name: str | Path = "",
    **toml_subdict,
) -> Path:
    """Check that the machine config file is valid."""
    machine_config_file = find_file(toml_folder, machine_config_file)
    with open(machine_config_file, "rb") as file:
        config = tomllib.load(file)

    if not machine_name:
        machine_name = socket.gethostname()

    assert (
        machine_name in config
    ), f"{machine_name = } should be in {config.keys() = }"
    this_machine_config = config[machine_name]

    assert (
        simulation_type in this_machine_config
    ), f"{simulation_type = } was not found in {this_machine_config = }"
    executable = Path(this_machine_config[simulation_type])
    assert executable.is_file, f"{executable = } was not found"
    return executable
