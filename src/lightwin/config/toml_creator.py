"""Define functions to create the ``.toml`` required by LightWin."""

import logging
import shutil
from pathlib import Path
from typing import Any, Literal

_DUMMIES = {
    "files": {"dat_file": "data/example/example.dat"},
    "beam": {
        "e_mev": 0.0,
        "e_rest_mev": 0.0,
        "f_bunch_mhz": 0.0,
        "i_milli_a": 0.0,
        "q_adim": 1.0,
        "sigma": [[0.0 for _ in range(6)] for _ in range(6)],
    },
}


def dict_to_toml(
    config: dict[str, dict[str, Any]],
    toml_path: Path,
    allow_overwrite: bool = False,
) -> None:
    """Write the provided configuration dict to a ``.toml`` file."""
    if _indue_overwritting(toml_path, allow_overwrite):
        return

    strings = (
        _dict_to_toml_string(sub_config, sub_config_name)
        for sub_config_name, sub_config in config.items()
    )
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


def _dict_to_toml_string(
    sub_config: dict[str, Any], sub_config_name: str
) -> str:
    """Convert the configuration dict to string."""
    content = [f"[{sub_config_name}]"]
    content += [f'{key} = "{value}"' for key, value in sub_config.items()]
    return "\n".join(content)


def dummy_config(
    name: Literal[
        "beam", "wtf", "beam_calculator", "files", "plots", "evaluators"
    ],
    override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Provide a dummy configuration entry."""
    if name not in _DUMMIES:
        logging.error(f"Dummy dict for {name} not implemented.")
        return {}
    sub_config = _DUMMIES[name]
    if override is None:
        return sub_config

    for key, val in override.items():
        sub_config[key] = val
    return sub_config
