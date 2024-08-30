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

    Returns
    -------
    configuration : dict[str, dict[str, Any]]
        A dictonary holding all the keyword arguments that will be passed to
        LightWin objects, eg ``beam_calculator`` will be passed to
        :class:`.BeamCalculator`.

    """
    assert config_path.is_file(), f"{config_path = } does not exist."
    toml_fulldict = _load_toml(
        config_path, config_keys, warn_mismatch, override
    )

    full_conf_specs = FullConfSpec()
    full_conf_specs.validate(toml_fulldict, toml_folder=config_path.parent)
    return toml_fulldict


def _load_toml(
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
