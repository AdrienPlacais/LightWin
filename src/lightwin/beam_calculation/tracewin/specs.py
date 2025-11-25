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

from lightwin.beam_calculation.beam_calculator_base_specs import (
    BEAM_CALCULATOR_BASE_CONFIG,
)
from lightwin.beam_calculation.deprecated_specs import (
    apply_deprecated_flag_phi_abs,
)
from lightwin.config.helper import find_file
from lightwin.config.key_val_conf_spec import KeyValConfSpec
from lightwin.config.table_spec import TableConfSpec
from lightwin.constants import example_ini, example_machine_config
from lightwin.util.typing import EXPORT_PHASES

_PURE_TRACEWIN_CONFIG = (
    KeyValConfSpec(
        key="algo",
        types=(int,),
        description=(
            "Optimization using algorithm (0: Owner, 1: Simplex, 2: Diff. "
            "evo.)"
        ),
        default_value=0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="alpx1",
        types=(float,),
        description="Input twiss parameter alpXX’ of main beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="alpx2",
        types=(float,),
        description="Input twiss parameter alpXX’ of second beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="alpy1",
        types=(float,),
        description="Input twiss parameter alpYY’ of main beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="alpy2",
        types=(float,),
        description="Input twiss parameter alpYY’ of second beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="alpz1",
        types=(float,),
        description="Input twiss parameter alpZZ’ of main beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="alpz2",
        types=(float,),
        description="Input twiss parameter alpZZ’ of second beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="betx1",
        types=(float,),
        description="Input twiss parameter betXX’ of main beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="betx2",
        types=(float,),
        description="Input twiss parameter betXX’ of second beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="bety1",
        types=(float,),
        description="Input twiss parameter betYY’ of main beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="bety2",
        types=(float,),
        description="Input twiss parameter betYY’ of second beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="betz1",
        types=(float,),
        description="Input twiss parameter betZZ’ of main beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="betz2",
        types=(float,),
        description="Input twiss parameter betZZ’ of second beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="cancel_matching",
        types=(bool,),
        description="Cancel all matching procedure (Envelope)",
        default_value=False,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="cancel_matchingP",
        types=(bool,),
        description="Cancel all matching procedure (Tracking)",
        default_value=False,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="charge1",
        types=(float,),
        description="Input particle charge state of main beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="charge2",
        types=(float,),
        description="Input particle charge state of second beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="current1",
        types=(float,),
        description="Input beam current (mA) of main beam",
        default_value=0.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="current2",
        types=(float,),
        description="Input beam current (mA) of second beam",
        default_value=0.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="dst_file1",
        types=(str, Path),
        description="Full name Input dst of main beam (*)",
        default_value="",
        is_mandatory=False,
        is_a_path_that_must_exists=True,
    ),
    KeyValConfSpec(
        key="dst_file2",
        types=(str, Path),
        description="Full name Input dst of second beam (*)",
        default_value="",
        is_mandatory=False,
        is_a_path_that_must_exists=True,
    ),
    KeyValConfSpec(
        key="duty1",
        types=(float,),
        description="Duty cycle of main beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="duty2",
        types=(float,),
        description="Duty cycle of second beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="dw1",
        types=(float,),
        description="Input Dw of main beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="dw2",
        types=(float,),
        description="Input Dw of second beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="eln1",
        types=(float,),
        description="Input ZZ’ emittance (mm.mrad) of main beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="eln2",
        types=(float,),
        description="Input ZZ’ emittance (mm.mrad) of second beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="emit_e_limit",
        types=(float,),
        description=r"Particle is excluded form emit. calculation if \|W-Ws\|/ Ws > emit_e_limit",
        default_value=0.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="emit_p_limit",
        types=(float,),
        description=r"Particle is excluded form emit. calculation if \|Ф- Ф s\| > emit_p_limit",
        default_value=0.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="energy1",
        types=(float,),
        description="Input kinetic energy (MeV) of main beam",
        default_value=100.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="energy2",
        types=(float,),
        description="Input kinetic energy (MeV) of second beam",
        default_value=100.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="etnx1",
        types=(float,),
        description="Input XX’ emittance (mm.mrad) of main beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="etnx2",
        types=(float,),
        description="Input XX’ emittance (mm.mrad) of second beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="etny1",
        types=(float,),
        description="Input YY’ emittance (mm.mrad) of main beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="etny2",
        types=(float,),
        description="Input YY’ emittance (mm.mrad) of second beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="freq1",
        types=(float,),
        description="Input beam frequency (MHz) of main beam",
        default_value=100.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="freq2",
        types=(float,),
        description="Input beam frequency (MHz) of second beam",
        default_value=100.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="hide",
        types=(bool,),
        description="Hide the GUI, or cancel console output (no parameter).",
        default_value=True,
    ),
    KeyValConfSpec(
        key="input_dist_type",
        types=(int,),
        description="Input distribution type from 1 to 5, see GUI menu",
        default_value=1,
        allowed_values=range(1, 6),
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="long_dist_mask",
        types=(int,),
        description="Mask of the longitudinal input distribution from 1 to 7, see GUI menu",
        default_value=1,
        allowed_values=range(1, 8),
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="lost_e_limit",
        types=(float,),
        description=r"Particle is lost if \|W-Ws\| > lost_e_limit",
        default_value=0.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="lost_p_limit",
        types=(float,),
        description=r"Particle is lost if \|Ф- Ф s\| > lost_p_limit",
        default_value=0.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="mass1",
        types=(float,),
        description="Input beam mass (eV) of main beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="mass2",
        types=(float,),
        description="Input beam mass (eV) of second beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="nbr_part1",
        types=(int,),
        description="Number of particle of main beam",
        default_value=100,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="nbr_part2",
        types=(int,),
        description="Number of particle of second beam",
        default_value=100,
        is_mandatory=False,
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
        description="To activate/deactivate partran tracking.",
        default_value=0,
        allowed_values=(0, 1, True, False),
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="part_step",
        types=(int,),
        description=(
            "Partran calculation step per meter (per beta.lambda if < 0)"
        ),
        default_value=20,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="picnic_2d",
        types=(bool,),
        description="Space-charge routine is defined as picnic2D",
        default_value=False,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="picnic_3d",
        types=(bool,),
        description="Space-charge routine is defined as picnic3D",
        default_value=False,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="picnic_r_mesh",
        types=(float,),
        description="R mesh of picnic 2D",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="picnic_xy_mesh",
        types=(float,),
        description="X&Y mesh of picnic 3D",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="picnic_z_mesh",
        types=(float,),
        description="Z mesh of picnic 3D",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="picnir_z_mesh",
        types=(float,),
        description="Z mesh of picnir 2D",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="random_seed",
        types=(int,),
        description="Set the random seed",
        default_value=0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="spreadw1",
        types=(float,),
        description="Input spread energy for CW beam of main beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="spreadw2",
        types=(float,),
        description="Input spread energy for CW beam of second beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="synoptic_file",
        types=(str, Path),
        description=(
            "Save the geometric layout at (entance (=1), middle (=2), exit "
            "(=3) of elements. (See “Synoptic” tools for file name)."
        ),
        default_value=example_ini.with_stem(".syn"),
        is_a_path_that_must_exists=False,
        is_mandatory=False,
        warning_message="Not sure of this argument meaning.",
    ),
    KeyValConfSpec(
        key="tab_file",
        types=(str, Path),
        description=(
            "Save to file the data sheet at the end of calcul (by default in "
            "calculation directory)."
        ),
        default_value=example_ini.with_stem(".tab"),
        is_a_path_that_must_exists=False,
        is_mandatory=False,
        warning_message="Not sure of this argument meaning.",
    ),
    KeyValConfSpec(
        key="toutatis",
        types=(float, bool),
        description="Force or avoid Toutatis simulation (1 / 0)",
        default_value=0,
        allowed_values=(0, 1, True, False),
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="trans_dist_mask",
        types=(int,),
        description="Mask of the transverse input distribution from 1 to 7, see GUI menu",
        default_value=1,
        allowed_values=range(1, 8),
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="upgrade",
        types=(str,),
        description="To update LightWin",
        default_value="",
        is_mandatory=False,
        error_message="Upgrading TraceWin from LightWin is a bad idea.",
    ),
    KeyValConfSpec(
        key="use_dst_file",
        types=(bool,),
        description="dst file is used as input beam distribution",
        default_value=True,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="vfac",
        types=(float,),
        description="Change RFQ Ucav (ex : “vfac 0.5”, half reduce of Ucav)",
        default_value=0.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="x1",
        types=(float,),
        description="Input X position of main beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="x2",
        types=(float,),
        description="Input X position of second beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="xp1",
        types=(float,),
        description="Input X angle of main beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="xp2",
        types=(float,),
        description="Input X angle of second beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="y1",
        types=(float,),
        description="Input Y position of main beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="y2",
        types=(float,),
        description="Input Y position of second beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="yp1",
        types=(float,),
        description="Input Y angle of main beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="yp2",
        types=(float,),
        description="Input Y angle of second beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="z1",
        types=(float,),
        description="Input Z position of main beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="z2",
        types=(float,),
        description="Input Z position of second beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="zp1",
        types=(float,),
        description="Input Z angle of main beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="zp2",
        types=(float,),
        description="Input Z angle of second beam",
        default_value=-1.0,
        is_mandatory=False,
    ),
)

TRACEWIN_CONFIG = (
    BEAM_CALCULATOR_BASE_CONFIG
    + _PURE_TRACEWIN_CONFIG
    + (
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
            key="ini_path",
            types=(str, Path),
            description="Path to the `INI` TraceWin file.",
            default_value=example_ini,
            is_a_path_that_must_exists=True,
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
                "`machine_config_file`. By default, do not provide it and let "
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
    )
)  #: Arguments for :class:`.TraceWin` object configuration


def tracewin_pre_treat(
    self: TableConfSpec, toml_table: dict[str, Any], **kwargs
) -> None:
    """Set the TW executable."""
    self._insert_defaults(toml_table, **kwargs)
    apply_deprecated_flag_phi_abs(self, toml_table, **kwargs)
    if "executable" in toml_table:
        declare = getattr(
            self, "_declare_that_machine_config_is_not_mandatory_anymore"
        )
        declare()
        return

    toml_table["executable"] = _get_tracewin_executable(**toml_table, **kwargs)


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
    self._make_paths_absolute(toml_subdict, **kwargs)

    new_toml_subdict = {"base_kwargs": {}}  # TraceWin arguments

    entries_to_remove = (
        "simulation_type",
        "machine_config_file",
        "machine_name",
    )
    entries_to_put_in_base_kwargs = [
        keyval.key for keyval in _PURE_TRACEWIN_CONFIG
    ]

    for key, value in toml_subdict.items():
        if key in entries_to_remove:
            continue

        if key not in entries_to_put_in_base_kwargs:
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
