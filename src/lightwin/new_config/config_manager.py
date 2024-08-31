"""Load, validate and post-process the configuration."""

import logging
import tomllib
from pathlib import Path
from typing import Any

from lightwin.new_config.full_specs import FullConfSpec


def process_config(
    config_path: Path,
    config_keys: dict[str, str],
    warn_mismatch: bool = False,
    override: dict[str, dict[str, Any]] | None = None,
    full_conf_specs: FullConfSpec | None = None,
) -> dict[str, dict[str, Any]]:
    """Load and test the configuration file.

    Parameters
    ----------
    config_path : Path
        Path to the configuration file. It must be a ```.toml`` file.
    config_keys : dict[str, str]
        Associate the name of LightWin's group of parameters to the entry in
        the configuration file.
    warn_mismatch : bool, optional
        Raise a warning if a key in a ``override`` sub-dict is not found.
    override : dict[str, dict[str, Any]] | None, optional
        To override entries in the ``.toml``. If not provided, we keep
        defaults.
    full_conf_specs : FullConfSpec | None, optional
        The specifications that the ``.toml`` must match to be accepted. If not
        provided, we take a default.

    Returns
    -------
    configuration : dict[str, dict[str, Any]]
        A dictonary holding all the keyword arguments that will be passed to
        LightWin objects, eg ``beam_calculator`` will be passed to
        :class:`.BeamCalculator`.

    """
    assert config_path.is_file(), f"{config_path = } does not exist."
    toml_fulldict = load_toml(
        config_path, config_keys, warn_mismatch, override
    )

    if full_conf_specs is None:
        full_conf_specs = FullConfSpec()
    full_conf_specs.validate(toml_fulldict, toml_folder=config_path.parent)
    return toml_fulldict


def load_toml(
    config_path: Path,
    config_keys: dict[str, str],
    warn_mismatch: bool,
    override: dict[str, dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    """Load the ``.toml`` and extract the dicts asked by user."""
    all_toml: dict[str, dict[str, Any]]
    with open(config_path, "rb") as f:
        all_toml = tomllib.load(f)

    toml_fulldict = {
        key: all_toml[value] for key, value in config_keys.items()
    }

    if override is None:
        return toml_fulldict

    _override_some_toml_entries(toml_fulldict, warn_mismatch, **override)
    return toml_fulldict


def _override_some_toml_entries(
    toml_fulldict: dict[str, dict[str, Any]],
    warn_mismatch: bool,
    **override: dict[str, Any],
) -> None:
    """Override some entries before testing."""
    for over_key, over_subdict in override.items():
        assert over_key in toml_fulldict, (
            f"You want to override entries in {over_key = }, which was not "
            f"found in {toml_fulldict.keys() = }"
        )
        conf_subdict = toml_fulldict[over_key]

        for key, val in over_subdict.items():
            if warn_mismatch and key not in conf_subdict:
                logging.warning(
                    f"You want to override {key = }, which was "
                    f"not found in {conf_subdict.keys() = }"
                )
            conf_subdict[key] = val


def dict_to_toml(
    toml_fulldict: dict[str, dict[str, Any]],
    toml_path: Path,
    full_conf_specs: FullConfSpec,
    allow_overwrite: bool = False,
) -> None:
    """Write the provided configuration dict to a ``.toml`` file."""
    if _indue_overwritting(toml_path, allow_overwrite):
        return

    strings = full_conf_specs.to_toml_strings(toml_fulldict)
    with open(toml_path, "w") as f:
        for dict_entry_string in strings:
            f.write(dict_entry_string)
            f.write("\n")

    logging.info(f"New ``.toml`` written in {toml_path}")
    return


def _indue_overwritting(
    toml_path: Path,
    allow_overwrite: bool = False,
) -> bool:
    """Ensure that ``.toml`` will not be overwritten if not wanted."""
    if not toml_path.exists():
        return False

    logging.info(
        f"A .toml already exists at {toml_path = } and may be overwritten."
    )
    if not allow_overwrite:
        logging.error("Overwritting not permitted. Skipping action...")
        return True

    old = toml_path.with_suffix(".toml.old")
    logging.info(f"Copying the old one to {old}, just in case...")
    shutil.copy(toml_path, old)
    return False
