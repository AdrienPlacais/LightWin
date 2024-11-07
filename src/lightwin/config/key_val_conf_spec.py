"""Define the base objects constraining values/types of config parameters."""

import logging
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from lightwin.config.helper import find_path
from lightwin.config.toml_formatter import format_for_toml


@dataclass
class KeyValConfSpec:
    """Set specifications for a single key-value pair.

    Parameters
    ----------
    key : str
        Name of the attribute.
    types : tuple[type, ...]
        Allowed types for the value. Used to check validity of input. When
        creating a config ``.toml`` file, the first type of the tuple is used
        for proper formatting. Prefer giving a tuple of types, even if there is
        only one possible type.
    description : str
        A markdown string to describe the property. Will be displayed in the
        documentation.
    default_value : Any
        A default value for the property. Used when generating dummy
        configurations; also used if the property is not mandatory and was not
        provided.
    allowed_values : Collection[Any] | None, optional
        A set of allowed values, or range of allowed values. The default is
        None, in which case no checking is performed.
    is_mandatory : bool, optional
        If the property must be given. The default is True.
    is_a_path_that_must_exists : bool, optional
        If the property is a string/path and its existence must be checked
        before running the code.
    action : Literal["store_true", "store_false"] | None = None
        on/off flag, also check the ``argparse`` documentation. Will skip
        testing over type and allowed values.
    warning_message : str | None, optional
        If provided, using current key will print a warning with this message.
        The default is None.
    error_message : str | None, optional
        If provided, using current key will raise an IOError with this error
        message. The default is None.
    overrides_previously_defined : bool, optional
        If the current object should remove a previously defined
        :class:`KeyValConfSpec` with the same name.
    derived : bool, optional
        If the property is calculated from other properties. The default is
        False, in which case it must be set by the user. Note that derived keys
        will not appear in the ``.toml`` output strings.

    """

    key: str
    types: tuple[type, ...]
    description: str
    default_value: Any

    allowed_values: Collection[Any] | None = None
    is_mandatory: bool = True
    is_a_path_that_must_exists: bool = False
    action: Literal["store_true", "store_false"] | None = None
    warning_message: str | None = None
    error_message: str | None = None
    overrides_previously_defined: bool = False
    derived: bool = False

    def __post_init__(self) -> None:
        """Force ``self.types`` to be a tuple of types."""
        if isinstance(self.types, type):
            self.types = (self.types,)

    def validate(self, toml_value: Any, **kwargs) -> bool:
        """Check that the given ``toml`` line is valid."""
        if self.warning_message:
            logging.warning(self.warning_message)
        if self.error_message:
            logging.critical(self.error_message)
            raise IOError(self.error_message)
        if self.action is not None:
            return True

        valid = (
            self.is_valid_type(toml_value, **kwargs)
            and self.is_valid_value(toml_value, **kwargs)
            and self.path_exists(toml_value, **kwargs)
        )
        if not valid:
            logging.error(f"An error was detected while treating {self.key}")
        return valid

    def is_valid_type(self, toml_value: Any, **kwargs) -> bool:
        """Check that the value has the proper typing."""
        if isinstance(toml_value, self.types):
            return True
        logging.warning(
            f"Type error in {self.key}. {toml_value = } type not in "
            f"{self.types = }"
        )
        return False

    def is_valid_value(self, toml_value: Any, **kwargs) -> bool:
        """Check that the value is accepted."""
        if self.allowed_values is None:
            return True
        if toml_value in self.allowed_values:
            return True
        logging.error(f"{toml_value = } is not in {self.allowed_values = }")
        return False

    def path_exists(
        self, toml_value: Any, toml_folder: Path | None = None, **kwargs
    ) -> bool:
        """Check that the given path exists if necessary."""
        if not self.is_a_path_that_must_exists:
            return True
        try:
            _ = find_path(toml_folder, toml_value)
            return True
        except FileNotFoundError:
            logging.error(f"{toml_value} should exist but was not found.")
            return False

    def to_toml_string(
        self,
        toml_value: Any | None = None,
        original_toml_folder: Path | None = None,
        **kwargs,
    ) -> str:
        """Convert the value into a line that can be put in a ``.toml``.

        Parameters
        ----------
        toml_value : Any | None, optional
            The value to put in the file. If not provided, we issue a warnign
            and set at default value.
        original_toml_folder : pathlib.Path | None, optional
            Where the original ``.toml`` was; this is used to resolve paths
            relative to this location.

        Returns
        -------
        str
            The ``.toml`` line corresponding to current object.

        """
        if self.derived:
            return ""
        if toml_value is None:
            logging.error(
                f"You must provide a value for {self.key = }. Trying to "
                f"continue with {self.default_value = }..."
            )
            toml_value = self.default_value

        if Path in self.types:
            assert isinstance(toml_value, (str, Path))
            toml_value = find_path(original_toml_folder, toml_value)

        formatted = format_for_toml(
            self.key, toml_value, preferred_type=self.types[0]
        )
        return formatted

    def to_csv_line(self) -> tuple[str, str, str, str, str] | None:
        """Convert object to a line for the documentation CSV.

        Returns
        -------
        key : str
            Name of variable.
        types : str
            List of allowed types.
        description : str
            Description of the input.
        allowed_values : str
            List of allowed values if relatable.
        is_mandatory : str
            If the variable is mandatory or not.

        """
        if self.derived:
            return None

        type_names = [f"``{t.__name__}``" for t in self.types]
        fmt_types = " or ".join(type_names)

        fmt_allowed = (
            f"{self.allowed_values}" if self.allowed_values is not None else ""
        )
        fmt_mandatory = "✅" if self.is_mandatory else "❌"
        out = (
            self.key,
            fmt_types,
            self.description,
            fmt_allowed,
            fmt_mandatory,
        )
        return out
