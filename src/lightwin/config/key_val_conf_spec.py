"""Define the base objects constraining values/types of config parameters."""

import logging
import textwrap
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from lightwin.config.helper import find_path
from lightwin.config.toml_formatter import format_for_toml

CSV_HEADER = ["Entry", "Type", "Description", "Mandatory?", "Allowed values"]


@dataclass
class KeyValConfSpec:
    """Set specifications for a single key-value pair.

    Parameters
    ----------
    key :
        Name of the attribute.
    types :
        Allowed types for the value. Used to check validity of input. When
        creating a config ``TOML`` file, the first type of the tuple is used
        for proper formatting. Prefer giving a tuple of types, even if there is
        only one possible type.
    description :
        A markdown string to describe the property. Will be displayed in the
        documentation.
    default_value :
        A default value for the property. Used when generating dummy
        configurations; also used if the property is not mandatory and was not
        provided.
    allowed_values :
        A set of allowed values, or range of allowed values. The default is
        None, in which case no checking is performed.
    is_mandatory :
        If the property must be given. The default is True.
    is_a_path_that_must_exists :
        If the property is a string/path and its existence must be checked
        before running the code.
    action :
        on/off flag, also check the ``argparse`` documentation. Will skip
        testing over type and allowed values.
    warning_message :
        If provided, using current key will print a warning with this message.
        The default is None.
    error_message :
        If provided, using current key will raise an IOError with this error
        message. The default is None.
    overrides_previously_defined :
        If the current object should remove a previously defined
        :class:`KeyValConfSpec` with the same name.
    derived :
        If the property is calculated from other properties. The default is
        False, in which case it must be set by the user. Note that derived keys
        will not appear in the ``TOML`` output strings.

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
            raise OSError(self.error_message)
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
        logging.error(
            f"{self.key}: {toml_value = } is not in {self.allowed_values = }"
        )
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
        """Convert the value into a line that can be put in a ``TOML``.

        Parameters
        ----------
        toml_value :
            The value to put in the file. If not provided, we issue a warnign
            and set at default value.
        original_toml_folder :
            Where the original ``TOML`` was; this is used to resolve paths
            relative to this location.

        Returns
        -------
            The ``TOML`` line corresponding to current object.

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
        """Convert object to a line for the documentation ``CSV``.

        .. todo::
           Handle units (avoid premature line skip).
           Automatic detection of backticks format
           Better display of allowed values

        Returns
        -------
        key :
            Name of variable.
        types :
            List of allowed types.
        description :
            Description of the input.
        allowed_values :
            List of allowed values if relatable.
        is_mandatory :
            If the variable is mandatory or not.

        """
        if self.derived:
            return None

        type_names = [f"``{t.__name__}``" for t in self.types]
        fmt_types = " or ".join(type_names)

        fmt_mandatory = "✅" if self.is_mandatory else "❌"
        fmt_allowed = (
            f"{self.allowed_values}" if self.allowed_values is not None else ""
        )
        long = (
            f"`{self.key}`",
            fmt_types,
            self.description,
            fmt_mandatory,
            fmt_allowed,
        )
        widths = (20, 10, 30, 1000, 1000)
        codelikes = (True, False, False, False, False)
        shortened = [
            format_long_columns(text, width, codelike)
            for text, width, codelike in zip(long, widths, codelikes)
        ]
        return shortened


def format_long_columns(
    long: str, max_width: int, codelike: bool = False
) -> str:
    """Format cell content to fit within ``max_width``.

    A cell spanning over several lines should start and end by a single ``"``
    character. Two line skips should be inserted where the line breaks.

    """
    if len(long) < max_width:
        return long
    chunker = chunk_with_hyphen
    if codelike:
        chunker = chunk_backtick_string
    chunks = chunker(long, max_width)
    joined = "\n\n".join(chunks)
    return joined


def chunk(long: str, max_width: int) -> list[str]:
    """Slice string in chunks of max ``max_width``."""
    return [long[i : i + max_width] for i in range(0, len(long), max_width)]


def chunk_with_hyphen(text: str, max_width: int) -> list[str]:
    """Split text into chunks at spaces.

    Words longer than max_width are hyphenated.

    """
    wrapped = []
    for word in text.split():
        while len(word) > max_width:
            wrapped.append(word[: max_width - 1] + "-")  # add hyphen
            word = word[max_width - 1 :]
        wrapped.append(word)

    # Now merge words into lines of max_width
    lines = []
    current_line = ""
    for word in wrapped:
        if (
            len(current_line) + len(word) + (1 if current_line else 0)
            <= max_width
        ):
            current_line += (" " if current_line else "") + word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    return lines


def chunk_backtick_string(text: str, max_width: int) -> list[str]:
    """
    Slice a string enclosed in backticks into chunks of max_width.
    Prefer splitting at underscores. No hyphenation is used.
    """
    if not (text.startswith("`") and text.endswith("`")):
        raise ValueError("String must be enclosed in backticks")

    content = text[1:-1]  # remove backticks
    parts = content.split("_")

    chunks = []
    current = ""
    for part in parts:
        if current:
            candidate = current + "_" + part
        else:
            candidate = part

        if len(candidate) + 2 <= max_width:  # +2 for backticks
            current = candidate
        else:
            if current:
                chunks.append(f"`{current}`")
            current = part

    if current:
        chunks.append(f"`{current}`")

    return chunks
