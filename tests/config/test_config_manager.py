"""Ensure that loading and validating ``TOML`` works as expected."""

from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock, call, mock_open, patch

import pytest

from lightwin.config.config_manager import (
    _load_toml,
    _override_some_toml_entries,
    dict_to_toml,
    process_config,
)
from lightwin.config.full_specs import ConfSpec
from lightwin.constants import example_config

CONFIG_KEYS = {
    "beam": "beam",
    "files": "files",
    "beam_calculator": "generic_tracewin",
}


# =============================================================================
# Mocks and fixtures
# =============================================================================
@pytest.fixture
def mock_conf_spec() -> tuple[MagicMock, MagicMock]:
    """Mock the :class:`.ConfSpec` class."""
    conf_specs_t = MagicMock(spec=type(ConfSpec))
    conf_specs = MagicMock(spec=ConfSpec)
    conf_specs_t.return_value = conf_specs
    return conf_specs_t, conf_specs


@pytest.fixture
def common_setup(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, dict[str, str]]:
    """Fixture to set up common test components."""
    toml_content = b"""
    [proton_beam]
    key1 = "value1"
    key2 = "value2"
    """
    toml_path = tmp_path_factory.mktemp("config") / "config.toml"
    toml_path.write_bytes(toml_content)

    config_keys = {"beam": "proton_beam"}
    return toml_path, config_keys


def mock_load_toml(mock_return_value: dict[str, dict[str, Any]]):
    """Mock :func:`._load_toml` with a given return value."""
    return patch(
        "lightwin.config.config_manager._load_toml",
        return_value=mock_return_value,
    )


@pytest.fixture
def mock_conf_spec_for_dict_to_toml() -> MagicMock:
    """Mock the ConfSpec class for dict_to_toml tests."""
    mock = MagicMock()
    mock.to_toml_strings.return_value = [
        "[beam]",
        "key1 = 'value1'",
        "key2 = 'value2'",
    ]
    return mock


# =============================================================================
# Tests for every function of the config_manager_module
# =============================================================================
@pytest.mark.tmp
class TestLoadToml:
    """Test the :func:`._load_toml` function."""

    def test_success(self) -> None:
        """Check :func:`_load_toml` successfully loads and maps sections."""
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

    @pytest.mark.smoke
    def test_general_behavior(self) -> None:
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
@pytest.mark.tmp
class TestProcessConfig:
    """Define tests for the :func:``.process_config`` function."""

    def test_process_config_valid(
        self,
        mock_conf_spec: tuple[MagicMock, MagicMock],
        common_setup: tuple[Path, dict[str, str]],
    ) -> None:
        """Test process_config with valid inputs."""
        conf_specs_t, conf_specs = mock_conf_spec
        conf_specs_t_cast = cast(type[ConfSpec], conf_specs_t)  # for linter
        toml_path, config_keys = common_setup

        config_keys = {"beam": "proton_beam"}

        with mock_load_toml(
            {"beam": {"key1": "value1", "key2": "value2"}}
        ) as mock_load:
            result = process_config(
                toml_path=toml_path,
                config_keys=config_keys,
                conf_specs_t=conf_specs_t_cast,
            )

            assert result == {"beam": {"key1": "value1", "key2": "value2"}}
            mock_load.assert_called_once_with(
                toml_path, config_keys, warn_mismatch=False, override=None
            )
            conf_specs_t.assert_called_once_with(**config_keys)
            conf_specs.prepare.assert_called_once_with(
                result, toml_folder=toml_path.parent
            )

    def test_process_config_invalid_toml_path(
        self, mock_conf_spec: tuple[MagicMock, MagicMock]
    ) -> None:
        """Test process_config raises an error for an invalid ``TOML`` path."""
        conf_specs_t, _ = mock_conf_spec
        conf_specs_t_cast = cast(type[ConfSpec], conf_specs_t)  # for linter
        toml_path = Path("non_existent_file.toml")
        config_keys = {"beam": "proton_beam"}

        with pytest.raises(AssertionError, match="does not exist"):
            process_config(
                toml_path=toml_path,
                config_keys=config_keys,
                conf_specs_t=conf_specs_t_cast,
            )

    def test_process_config_with_override(
        self,
        mock_conf_spec: tuple[MagicMock, MagicMock],
        common_setup: tuple[Path, dict[str, str]],
    ) -> None:
        """Test process_config applies overrides correctly."""
        conf_specs_t, conf_specs = mock_conf_spec
        conf_specs_t_cast = cast(type[ConfSpec], conf_specs_t)  # for linter

        toml_path, config_keys = common_setup
        override = {"beam": {"key1": "new_value"}}

        with mock_load_toml(
            {"beam": {"key1": "value1", "key2": "value2"}}
        ) as mock_load:
            result = process_config(
                toml_path=toml_path,
                config_keys=config_keys,
                override=override,
                conf_specs_t=conf_specs_t_cast,
            )

            mock_load.assert_called_once_with(
                toml_path, config_keys, warn_mismatch=False, override=override
            )
            # Note the key1: value1; not key1: new_value! This is because we
            # mocked _load_toml and the override logic happens in this function
            assert result == {"beam": {"key1": "value1", "key2": "value2"}}
            conf_specs_t.assert_called_once_with(**config_keys)
            conf_specs.prepare.assert_called_once_with(
                result, toml_folder=toml_path.parent
            )


@pytest.mark.tmp
class TestOverrideSomeTomlEntries:
    """Provide methods to validate :func:`._override_some_toml_entries.`"""

    def test_success(self) -> None:
        """Test that overrides are correctly applied."""
        toml_fulldict = {
            "beam": {"key1": "value1", "key2": "value2"},
            "files": {"file1": "path/to/file"},
        }
        override = {"beam": {"key1": "new_value1", "key2": "new_value2"}}

        _override_some_toml_entries(
            toml_fulldict, warn_mismatch=False, **override
        )

        assert toml_fulldict == {
            "beam": {"key1": "new_value1", "key2": "new_value2"},
            "files": {"file1": "path/to/file"},
        }

    def test_missing_key(self) -> None:
        """Test that an AssertionError is raised when keys miss."""
        toml_fulldict = {"beam": {"key1": "value1", "key2": "value2"}}
        override = {"nonexistent_key": {"key1": "new_value"}}

        with pytest.raises(
            AssertionError, match="You want to override entries in .*"
        ):
            _override_some_toml_entries(
                toml_fulldict, warn_mismatch=False, **override
            )

    def test_warn_mismatch(self) -> None:
        """Test that warnings are logged for missing keys."""
        toml_fulldict = {"beam": {"key1": "value1"}}
        override = {"beam": {"nonexistent_key": "new_value"}}

        with patch("logging.warning") as mock_warning:
            _override_some_toml_entries(
                toml_fulldict, warn_mismatch=True, **override
            )

            mock_warning.assert_called_once_with(
                "You want to override key = 'nonexistent_key', which was not "
                "found in conf_subdict.keys() = dict_keys(['key1']). Setting "
                "it anyway..."
            )
            assert toml_fulldict == {
                "beam": {"key1": "value1", "nonexistent_key": "new_value"}
            }


@pytest.mark.tmp
class TestDictToToml:
    """Test suite for the dict_to_toml function."""

    def test_success(
        self, mock_conf_spec_for_dict_to_toml: MagicMock, tmp_path: Path
    ) -> None:
        """Test that dict_to_toml writes the correct TOML content to a file."""
        toml_path = tmp_path / "test.toml"
        toml_fulldict = {"beam": {"key1": "value1", "key2": "value2"}}

        with patch("builtins.open", mock_open()) as mocked_file:
            dict_to_toml(
                toml_fulldict, toml_path, mock_conf_spec_for_dict_to_toml
            )
            mocked_file().write.assert_has_calls(
                [
                    call("[beam]"),
                    call("\n"),
                    call("key1 = 'value1'"),
                    call("\n"),
                    call("key2 = 'value2'"),
                    call("\n"),
                ]
            )

    def test_no_overwrite(
        self, mock_conf_spec_for_dict_to_toml: MagicMock, tmp_path: Path
    ) -> None:
        """Test that dict_to_toml does not overwrite an existing file by default."""
        toml_path = tmp_path / "test.toml"
        toml_path.touch()  # Create the file to simulate pre-existence
        toml_fulldict = {"beam": {"key1": "value1"}}

        with patch("logging.error") as mock_error:
            dict_to_toml(
                toml_fulldict, toml_path, mock_conf_spec_for_dict_to_toml
            )

            # Ensure an error is logged
            mock_error.assert_called_once_with(
                "Overwritting not permitted. Skipping action..."
            )

    def test_allow_overwrite(
        self, mock_conf_spec_for_dict_to_toml: MagicMock, tmp_path: Path
    ) -> None:
        """Test that file is overwritten when allow_overwrite is True."""
        toml_path = tmp_path / "test.toml"
        toml_path.write_text("[old_content]\nkey = 'old_value'")
        toml_fulldict = {"beam": {"key1": "value1"}}

        with (
            patch("builtins.open", mock_open()) as mocked_file,
            patch("shutil.copy") as mock_copy,
        ):
            dict_to_toml(
                toml_fulldict,
                toml_path,
                mock_conf_spec_for_dict_to_toml,
                allow_overwrite=True,
            )

            mock_copy.assert_called_once_with(
                toml_path, toml_path.with_suffix(".toml.old")
            )

            mocked_file.assert_called_once_with(toml_path, "w")
            mocked_file().write.assert_has_calls(
                [
                    call("[beam]"),
                    call("\n"),
                    call("key1 = 'value1'"),
                    call("\n"),
                ]
            )

    def test_calls_to_toml_strings(
        self, mock_conf_spec_for_dict_to_toml: MagicMock, tmp_path: Path
    ) -> None:
        """Test that dict_to_toml calls ConfSpec.to_toml_strings with the correct arguments."""
        toml_path = tmp_path / "test.toml"
        toml_fulldict = {"beam": {"key1": "value1"}}

        dict_to_toml(toml_fulldict, toml_path, mock_conf_spec_for_dict_to_toml)

        mock_conf_spec_for_dict_to_toml.to_toml_strings.assert_called_once_with(
            toml_fulldict, original_toml_folder=None
        )
