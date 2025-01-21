"""Ensure that loading and validating ``TOML`` works as expected."""

from typing import Any
from unittest.mock import mock_open, patch

import pytest

from lightwin.config.config_manager import (
    _load_toml,
    dict_to_toml,
    process_config,
)
from lightwin.config.full_specs import SimplestConfSpec
from lightwin.constants import (
    example_config,
    example_dat,
    example_folder,
    example_ini,
    example_machine_config,
)

CONFIG_KEYS = {
    "beam": "beam",
    "files": "files",
    "beam_calculator": "generic_tracewin",
}


@pytest.fixture(scope="class")
def conf_specs() -> SimplestConfSpec:
    """Give the specifications to validate.

    Putting this in a fixture does not make much sense for now, but I may have
    different :class:`.SimplestConfSpec` in the future and parametrization will
    then be easier.

    """
    return SimplestConfSpec(
        beam="beam",
        files="files",
        beam_calculator="generic_tracewin",
    )


@pytest.fixture(scope="class")
def toml_fulldict_unaltered() -> dict[str, dict[str, Any]]:
    """Load the configuration file without editing or testing it."""
    toml_fulldict = _load_toml(
        example_config, CONFIG_KEYS, warn_mismatch=True, override=None
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
    dummy_files = {"dat_file": example_dat}
    return dummy_files


@pytest.fixture(scope="class")
def dummy_beam_calculator_tracewin() -> dict[str, Any]:
    """Generate a default dummy :class:`.TraceWin` conf dict."""
    dummy_tracewin = {
        "tool": "TraceWin",
        "ini_path": example_ini,
        "machine_config_file": example_machine_config,
        "partran": 0,
        "simulation_type": "noX11_full",
        "hide": True,
    }
    return dummy_tracewin


@pytest.fixture(scope="class")
def dummy_toml_dict(
    dummy_beam: dict[str, Any],
    dummy_files: dict[str, Any],
    dummy_beam_calculator_tracewin: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Generate a dummy config dict that should work."""
    dummy_conf = {
        "beam": dummy_beam,
        "files": dummy_files,
        "beam_calculator": dummy_beam_calculator_tracewin,
    }
    return dummy_conf


@pytest.fixture(scope="class")
def generated_toml_dict(
    conf_specs: SimplestConfSpec,
) -> dict[str, dict[str, Any]]:
    """Generate a configuration dict with default values."""
    return conf_specs.generate_dummy_dict()


class TestLoadToml:
    """Test the ``_load_toml`` function."""

    def test_load_toml_success(self) -> None:
        """Check that ``_load_toml`` successfully loads and maps sections."""
        mock_toml_data = b"""
        [proton_beam]
        key1 = "value1"
        key2 = "value2"

        [files]
        file1 = "path/to/file"
        """
        config_keys = {"beam": "proton_beam", "files": "files"}

        # Mock the `open` function used to open `config_path`
        with patch("builtins.open", mock_open(read_data=mock_toml_data)):
            # Mock the `tomllib.load` function imported in the config_manager
            with patch(
                "lightwin.config.config_manager.tomllib.load"
            ) as mock_load:
                mock_load.return_value = {
                    "proton_beam": {"key1": "value1", "key2": "value2"},
                    "files": {"file1": "path/to/file"},
                }

                result = _load_toml(
                    "mock_path",
                    config_keys,
                    warn_mismatch=False,
                    override=None,
                )
                assert result == {
                    "beam": {"key1": "value1", "key2": "value2"},
                    "files": {"file1": "path/to/file"},
                }

    def test_load_toml_missing_section(self):
        """Test ``_load_toml`` raises KeyError for missing sections."""
        mock_toml_data = b"""
        [other_section]
        key1 = "value1"
        """
        config_keys = {"beam": "proton_beam"}

        with patch("builtins.open", mock_open(read_data=mock_toml_data)):
            with patch(
                "lightwin.config.config_manager.tomllib.load"
            ) as mock_load:
                mock_load.return_value = {"other_section": {"key1": "value1"}}

                with pytest.raises(KeyError):
                    _load_toml(
                        "mock_path",
                        config_keys,
                        warn_mismatch=False,
                        override=None,
                    )

    def test_load_toml_with_override(self):
        """Test ``_load_toml`` applies override logic."""
        mock_toml_data = b"""
        [proton_beam]
        key1 = "value1"
        key2 = "value2"
        """
        config_keys = {"beam": "proton_beam"}
        override = {"beam": {"key1": "new_value1"}}

        with patch("builtins.open", mock_open(read_data=mock_toml_data)):
            with patch(
                "lightwin.config.config_manager.tomllib.load"
            ) as mock_load:
                mock_load.return_value = {
                    "proton_beam": {"key1": "value1", "key2": "value2"}
                }

                result = _load_toml(
                    "mock_path",
                    config_keys,
                    warn_mismatch=False,
                    override=override,
                )
                assert result == {
                    "beam": {"key1": "new_value1", "key2": "value2"},
                }

    @pytest.mark.smoke
    def test_load_toml(self) -> None:
        """Check if ``TOML`` loading does not throw errors.

        This is not a "deep" test, but a high-level test ensuring that the
        function will work for the user.

        """
        toml_fulldict = _load_toml(
            example_config, CONFIG_KEYS, warn_mismatch=True, override=None
        )
        assert isinstance(
            toml_fulldict, dict
        ), f"Error loading {example_config}"


@pytest.mark.smoke
@pytest.mark.implementation
class TestConfigManager:
    """Test that configuration file ``TOML`` correctly handled."""

    def test_validate(
        self,
        conf_specs: SimplestConfSpec,
        dummy_toml_dict: dict[str, dict[str, Any]],
    ) -> None:
        """Check if loaded toml is valid."""
        assert conf_specs.prepare(
            dummy_toml_dict,
            id_type="configured_object",
            toml_folder=example_folder,
        ), f"Error validating {example_config}"

    def test_generate_works(
        self, generated_toml_dict: dict[str, dict[str, Any]]
    ) -> None:
        """Check that generating a default toml leads to a valid dict."""
        assert isinstance(
            generated_toml_dict, dict
        ), "Error generating default configuration dict."

    def test_generate_is_valid(
        self,
        conf_specs: SimplestConfSpec,
        generated_toml_dict: dict[str, dict[str, Any]],
    ) -> None:
        """Check that generating a default toml leads to a valid dict."""
        assert conf_specs.prepare(
            generated_toml_dict, id_type="table_entry"
        ), "Error validating default configuration dict."

    def test_config_can_be_saved_to_file(
        self,
        conf_specs: SimplestConfSpec,
        dummy_toml_dict: dict[str, dict[str, Any]],
        tmp_path_factory: pytest.TempPathFactory,
    ):
        """Check if saving the given conf dict as toml works."""
        toml_path = tmp_path_factory.mktemp("test_toml") / "test.toml"
        dict_to_toml(dummy_toml_dict, toml_path, conf_specs)
        process_config(toml_path, CONFIG_KEYS, conf_specs_t=SimplestConfSpec)
        assert True
