"""Ensure that loading and validating ``.toml`` works as expected."""

import logging
from pathlib import Path
from typing import Any

import pytest

from lightwin.new_config.config_manager import (
    dict_to_toml,
    load_toml,
    process_config,
)
from lightwin.new_config.full_specs import FullConfSpec

DATA_DIR = Path("data", "example")
CONFIG_PATH = DATA_DIR / "lightwin.toml"
DAT_PATH = DATA_DIR / "example.dat"
CONFIG_KEYS = {"beam": "beam", "files": "files"}


@pytest.fixture(scope="class")
def full_conf_specs() -> FullConfSpec:
    """Give the specifications to validate.

    Putting this in a fixture does not make much sense for now, but I may have
    different :class:`.FullConfSpec` in the future and parametrization will
    then be easier.

    """
    return FullConfSpec()


@pytest.fixture(scope="class")
def toml_fulldict_unaltered() -> dict[str, dict[str, Any]]:
    """Load the configuration file without editing or testing it."""
    toml_fulldict = load_toml(
        CONFIG_PATH, CONFIG_KEYS, warn_mismatch=True, override=None
    )
    return toml_fulldict


@pytest.fixture(scope="class")
def dummy_beam() -> dict[str, Any]:
    """Generate a default dummy beam conf dict."""
    dummy_beam = {
        "e_rest_mev": 0.0,
        "q_adim": 1.0,
        "e_mev": 1.0,
        "f_bunch_mhz": 100.0,
        "i_milli_a": 0.0,
        "sigma": [[0.0 for _ in range(6)] for _ in range(6)],
    }
    return dummy_beam


@pytest.fixture(scope="class")
def dummy_files() -> dict[str, Any]:
    """Generate a default dummy files conf dict."""
    dummy_files = {"dat_file": DAT_PATH}
    return dummy_files


@pytest.fixture(scope="class")
def dummy_toml_dict(
    dummy_beam: dict[str, Any], dummy_files: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Generate a dummy config dict that should work."""
    dummy_conf = {"beam": dummy_beam, "files": dummy_files}
    return dummy_conf


@pytest.fixture(scope="class")
def generated_toml_dict(
    full_conf_specs: FullConfSpec,
) -> dict[str, dict[str, Any]]:
    """Generate a configuration dict with default values."""
    return full_conf_specs.generate_dummy_dict()


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
        self,
        full_conf_specs: FullConfSpec,
        dummy_toml_dict: dict[str, dict[str, Any]],
    ) -> None:
        """Check if loaded toml is valid."""
        assert full_conf_specs.validate(
            dummy_toml_dict, toml_folder=DATA_DIR
        ), f"Error validating {CONFIG_PATH}"

    def test_generate_works(
        self, generated_toml_dict: dict[str, dict[str, Any]]
    ) -> None:
        """Check that generating a default toml leads to a valid dict."""
        assert isinstance(
            generated_toml_dict, dict
        ), "Error generating default configuration dict."

    def test_generate_is_valid(
        self,
        full_conf_specs: FullConfSpec,
        generated_toml_dict: dict[str, dict[str, Any]],
    ) -> None:
        """Check that generating a default toml leads to a valid dict."""
        assert full_conf_specs.validate(
            generated_toml_dict,
        ), "Error validating default configuration dict."

    def test_config_can_be_saved_to_file(
        self,
        full_conf_specs: FullConfSpec,
        dummy_toml_dict: dict[str, dict[str, Any]],
        tmp_path_factory: pytest.TempPathFactory,
    ):
        """Check if saving the given conf dict as toml works."""
        toml_path = tmp_path_factory.mktemp("test_toml") / "test.toml"
        dict_to_toml(dummy_toml_dict, toml_path, full_conf_specs)
        process_config(toml_path, CONFIG_KEYS, full_conf_specs=full_conf_specs)
        assert True
