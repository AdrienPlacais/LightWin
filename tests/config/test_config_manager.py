"""Ensure that loading and validating ``TOML`` works as expected."""

from importlib.resources.abc import Traversable
from pathlib import Path
from unittest.mock import MagicMock, call, mock_open, patch

import pytest

from lightwin.config.config_manager import (
    ConfigFileNotFoundError,
    InvalidTomlSyntaxError,
    _load_toml,
    _override_some_toml_entries,
    _process_toml,
    dict_to_toml,
)


# =============================================================================
# Mocks and fixtures
# =============================================================================
@pytest.fixture
def mock_toml_content() -> bytes:
    """Fixture to mock a valid TOML file and its data."""
    return b"""
    [proton_beam]
    key1 = "value1"
    key2 = "value2"
    """


@pytest.fixture
def mock_conf_spec() -> MagicMock:
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

    def test_file_not_found(self) -> None:
        """Test for non-existent file.

        Ensures
        -------
        Raises ConfigFileNotFoundError when the specified file does not exist.

        """
        with pytest.raises(
            ConfigFileNotFoundError,
            match="The file non_existent_file.toml does not exist.",
        ):
            _load_toml("non_existent_file.toml")

    def test_invalid_syntax(self) -> None:
        """Test for invalid TOML syntax.

        Ensures
        -------
        Raises InvalidTomlSyntaxError for invalid TOML syntax.

        """
        bad_content = b"invalid: toml::"
        with (
            patch("builtins.open", mock_open(read_data=bad_content)),
            patch("pathlib.Path.is_file", return_value=True),
        ):
            with pytest.raises(
                InvalidTomlSyntaxError,
                match="Invalid TOML syntax in file mock_path",
            ):
                _load_toml("mock_path")

    def test_valid_toml_file(self, mock_toml_content: bytes) -> None:
        """Ensure valid TOML content is correctly loaded."""
        with (
            patch("builtins.open", mock_open(read_data=mock_toml_content)),
            patch("pathlib.Path.is_file", return_value=True),
            patch(
                "tomllib.load",
                return_value={
                    "proton_beam": {"key1": "value1", "key2": "value2"}
                },
            ),
        ):
            result = _load_toml("mock_path")
            assert result == {
                "proton_beam": {"key1": "value1", "key2": "value2"}
            }

    def test_traversable_input(self, mock_toml_content: bytes):
        """Ensure Traversable inputs are correctly processed."""
        mock_traversable = MagicMock(spec=Traversable)
        mock_traversable.open.return_value = mock_open(
            read_data=mock_toml_content
        ).return_value

        with (
            patch("importlib.resources.files", return_value=mock_traversable),
            patch(
                "tomllib.load",
                return_value={
                    "proton_beam": {"key1": "value1", "key2": "value2"}
                },
            ),
        ):
            result = _load_toml(mock_traversable)
            assert result == {
                "proton_beam": {"key1": "value1", "key2": "value2"}
            }


@pytest.mark.tmp
class TestProcessToml:
    """Test the :func:`._process_toml` function."""

    def test_missing_table_key(self):
        """Test for missing table key.

        Ensures
        -------
        Raises KeyError if a required table is missing in the TOML file.

        """
        raw_toml = {"files": {"key": "value"}}
        config_keys = {"beam": "proton_beam"}
        with pytest.raises(
            KeyError, match="Expected table 'proton_beam' for key 'beam'"
        ):
            _process_toml(
                raw_toml, config_keys, warn_mismatch=False, override=None
            )

    def test_with_override(self) -> None:
        """Test for applying overrides.

        Parameters
        ----------
        mock_toml_content : bytes
            Mocked TOML content fixture.

        Ensures
        -------
        Overrides are correctly applied to the loaded TOML.

        """
        raw_toml = {"proton_beam": {"key1": "value1", "key2": "value2"}}
        override = {"beam": {"key1": "new_value"}}
        result = _process_toml(
            raw_toml,
            {"beam": "proton_beam"},
            warn_mismatch=False,
            override=override,
        )
        assert result == {"beam": {"key1": "new_value", "key2": "value2"}}

    def test_warn_mismatch(self) -> None:
        """Test for warnings on mismatched overrides.

        Parameters
        ----------
        mock_toml_content : bytes
            Mocked TOML content fixture.

        Ensures
        -------
        Logs warnings for overrides that mismatch existing keys.

        """
        raw_toml = {"proton_beam": {"key1": "value1"}}
        override = {"beam": {"nonexistent_key": "new_value"}}
        with patch("logging.warning") as mock_warning:
            result = _process_toml(
                raw_toml,
                {"beam": "proton_beam"},
                warn_mismatch=True,
                override=override,
            )
            assert result == {
                "beam": {"key1": "value1", "nonexistent_key": "new_value"}
            }
            mock_warning.assert_called_once()


@pytest.mark.smoke
@pytest.mark.tmp
class TestProcessConfig:
    """Define tests for the :func:``.process_config`` function.

    .. todo::
        Maybe a smoke test as this is part of API?

    """


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

    def test_success(self, mock_conf_spec: MagicMock, tmp_path: Path) -> None:
        """Test that dict_to_toml writes the correct TOML content to a file."""
        toml_path = tmp_path / "test.toml"
        toml_fulldict = {"beam": {"key1": "value1", "key2": "value2"}}

        with patch("builtins.open", mock_open()) as mocked_file:
            dict_to_toml(toml_fulldict, toml_path, mock_conf_spec)
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
