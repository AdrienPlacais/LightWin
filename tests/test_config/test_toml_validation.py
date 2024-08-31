"""Ensure that loading and validating ``.toml`` works as expected."""

from pathlib import Path
from typing import Any

import pytest

from lightwin.new_config.config_manager import load_toml
from lightwin.new_config.full_specs import FullConfSpec

DATA_DIR = Path("data", "example")
CONFIG_PATH = DATA_DIR / "lightwin.toml"
DAT_PATH = DATA_DIR / "example.dat"
CONFIG_KEYS = {"beam": "beam", "files": "files"}


@pytest.fixture(scope="class")
def toml_fulldict_unaltered() -> dict[str, dict[str, Any]]:
    """Load the configuration file without editing or testing it."""
    toml_fulldict = load_toml(
        CONFIG_PATH, CONFIG_KEYS, warn_mismatch=True, override=None
    )
    return toml_fulldict


@pytest.fixture(scope="class")
def dummy_toml_dict() -> dict[str, dict[str, Any]]:
    """Generate a dummy config dict that should work."""
    dummy_beam = {
        "e_rest_mev": 0.0,
        "q_adim": 1.0,
        "e_mev": 1.0,
        "f_bunch_mhz": 100.0,
        "i_milli_a": 0.0,
        "sigma": [[0.0 for _ in range(6)] for _ in range(6)],
    }
    dummy_files = {"dat_file": DAT_PATH}
    dummy_conf = {"beam": dummy_beam, "files": dummy_files}
    return dummy_conf


@pytest.mark.smoke
@pytest.mark.implementation
class TestConfigManager:
    """Test that configuration file ``.toml`` correctly handled."""

    def test_load(self) -> None:
        """Check if toml loading does not throw errors."""
        toml_fulldict = load_toml(
            CONFIG_PATH, CONFIG_KEYS, warn_mismatch=True, override=None
        )
        assert isinstance(toml_fulldict, dict), f"Error loading {CONFIG_PATH}"

    def test_validate(
        self, dummy_toml_dict: dict[str, dict[str, Any]]
    ) -> None:
        """Check if loaded toml is valid."""
        full_conf_specs = FullConfSpec()
        assert full_conf_specs.validate(
            dummy_toml_dict, toml_folder=DATA_DIR
        ), f"Error validating {CONFIG_PATH}"
