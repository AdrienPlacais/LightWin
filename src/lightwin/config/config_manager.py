"""Load, validate and post-process the configuration.

.. todo::
    Method to generate the .csv files of documentation from the tables, i.e.
    docs/manual/configuration_entries

"""

import logging
import shutil
import tomllib
from pathlib import Path
from typing import Any

from lightwin.config.full_specs import ConfSpec


def process_config(
    toml_path: Path,
    config_keys: dict[str, str],
    warn_mismatch: bool = False,
    override: dict[str, dict[str, Any]] | None = None,
    conf_specs_t: type[ConfSpec] = ConfSpec,
) -> dict[str, dict[str, Any]]:
    """Load and test the configuration file.

    Parameters
    ----------
    toml_path : pathlib.Path
        Path to the configuration file. It must be a ``TOML`` file.
    config_keys : dict[str, str]
        Associate the name of LightWin's group of parameters to the entry in
        the configuration file.
    warn_mismatch : bool, optional
        Raise a warning if a key in a ``override`` sub-dict is not found.
    override : dict[str, dict[str, Any]] | None, optional
        To override entries in the ``TOML``. If not provided, we keep
        defaults.
    conf_specs_t : type[ConfSpec], optional
        The specifications that the ``TOML`` must match to be accepted. If not
        provided, we take a default.

    Returns
    -------
    toml_fulldict : dict[str, dict[str, Any]]
        A dictionary holding all the keyword arguments that will be passed to
        LightWin objects, eg ``beam_calculator`` will be passed to
        :class:`.BeamCalculator`.

    """
    assert toml_path.is_file(), f"{toml_path = } does not exist."
    toml_fulldict = _load_toml(
        toml_path, config_keys, warn_mismatch=warn_mismatch, override=override
    )

    conf_specs = conf_specs_t(**config_keys)
    conf_specs.prepare(toml_fulldict, toml_folder=toml_path.parent)
    return toml_fulldict


def _load_toml(
    config_path: Path | str,
    config_keys: dict[str, str],
    warn_mismatch: bool,
    override: dict[str, dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    """Load the ``TOML`` and extract the dicts asked by user.

    Parameters
    ----------
    config_path : pathlib.Path | str
        Path to the configuration file.
    config_keys : dict[str, str]
        Keys will be the keys of the output. Values are the name of the tables
        in the configuration file. If ``config_keys = {"beam": "proton_beam"}``
        , the output will look like ``{"beam": {<content of [proton_beam]>}}``.
    warn_mismatch : bool
        Check if there are discrepancies between ``override`` and the keys or
        dicts to override in ``config_keys``.
    override : dict[str, dict[str, Any]] | None
        To override some entries of the output dictionary, before even testing
        it.

    Returns
    -------
    toml_fulldict : dict[str, dict[str, Any]]
        A dictionary which keys are the keys of ``config_keys``, and the values
        are dictionaries holding corresponding table entries from the
        configuration file.

    """
    try:
        with open(config_path, "rb") as f:
            all_toml = tomllib.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"The file {config_path} does not exist.")
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"Error decoding TOML file {config_path}: {e}")

    toml_fulldict = {}
    for key, value in config_keys.items():
        if value not in all_toml:
            raise KeyError(
                f"Expected table '{value}' for key '{key}' not found in the "
                "TOML file."
            )
        toml_fulldict[key] = all_toml[value]

    if override:
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
                    f"You want to override {key = }, which was not found in "
                    f"{conf_subdict.keys() = }. Setting it anyway..."
                )
            conf_subdict[key] = val


def dict_to_toml(
    toml_fulldict: dict[str, dict[str, Any]],
    toml_path: Path,
    conf_specs: ConfSpec,
    allow_overwrite: bool = False,
    original_toml_folder: Path | None = None,
    **kwargs,
) -> None:
    """Write the provided configuration dict to a ``TOML`` file.

    Parameters
    ----------
    toml_fulldict : dict[str, dict[str, Any]]
        The configuration as a nested dictionary. The keys will be used as
        table entries.
    toml_path : pathlib.Path
        Where to save the ``TOML``.
    conf_specs : ConfSpec
        Holds the template to be respected. In particular, the type of the
        values in the different tables.
    allow_overwrite : bool, optional
        If a pre-existing ``TOML`` can be overwritten. The default is False,
        in which case an error will be raised.
    original_toml_folder : pathlib.Path | None, optional
        Where the original ``TOML`` was; this is used to resolve paths
        relative to this location.

    """
    if _indue_overwritting(toml_path, allow_overwrite):
        return

    strings = conf_specs.to_toml_strings(
        toml_fulldict, original_toml_folder=original_toml_folder, **kwargs
    )
    with open(toml_path, "w") as f:
        for dict_entry_string in strings:
            f.write(dict_entry_string)
            f.write("\n")

    logging.info(f"New ``TOML`` written in {toml_path}")
    return


def _indue_overwritting(
    toml_path: Path,
    allow_overwrite: bool = False,
) -> bool:
    """Ensure that ``TOML`` will not be overwritten if not wanted."""
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
