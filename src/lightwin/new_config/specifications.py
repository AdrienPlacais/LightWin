"""Define the base objects constraining values/types of config parameters."""

import logging
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lightwin.config.helper import find_file


@dataclass
class KeyValConfSpec:
    """Set specifications for a single key-value pair.

    Attributes
    ----------
    key : str
        Name of the attribute.
    types : tuple[type, ...]
        Allowed types for the value. Used to check validity of input, but also
        for proper formatting when creating a config ``.toml`` file. Prefer
        giving a tuple of types, even if there is only one possible type.
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

    """

    key: str
    types: tuple[type, ...]
    description: str
    default_value: Any
    allowed_values: Collection[Any] | None = None
    is_mandatory: bool = True
    is_a_path_that_must_exists: bool = False

    def __post_init__(self) -> None:
        """Force ``self.types`` to be a tuple of types."""
        if isinstance(self.types, type):
            self.types = (self.types,)

    def validate(self, toml_value: Any, **kwargs) -> bool:
        """Check that the given ``toml`` line is valid."""
        valid = (
            self.is_valid_type(toml_value, **kwargs)
            and self.is_valid_value(toml_value, **kwargs)
            and self.path_exists(toml_value, **kwargs)
        )
        if not valid:
            logging.error("An error was detected while treating {self.key}")
        return valid

    def is_valid_type(self, toml_value: Any, **kwargs) -> bool:
        """Check that the value has the proper typing."""
        if isinstance(toml_value, self.types):
            return True
        logging.error(f"{toml_value = } type not in {self.types = }")
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
        """Check that the given path exists."""
        if not self.is_a_path_that_must_exists:
            return True
        _ = find_file(toml_folder, toml_value)
        return True

    def to_toml_string(self, value: Any | None = None) -> str:
        """Convert the value into a line that can be put in a ``.toml``."""
        if value is None:
            assert (
                self.default_value is not None
            ), f"Provide a value for the {self.key}"
            value = self.default_value

        formatted = value
        if str in self.types:
            if isinstance(formatted, Path):
                formatted = str(formatted)
            formatted = '"' + formatted + '"'

        return f"{self.key} = {formatted}"


class TableConfSpec:
    """Set specifications for a table, which holds several key-value pairs."""

    def __init__(
        self,
        name: str,
        specs: Collection[KeyValConfSpec],
        is_mandatory: bool = True,
        can_have_untested_keys: bool = False,
    ) -> None:
        """Set a table of properties. Correspond to a [table] in the ``.toml``.

        Parameters
        ----------
        name : str
            Name of the table.
        specs : Collection[KeyValConfSpec]
            The :class:`KeyValConfSpec` in the current table.
        is_mandatory : bool, optional
            If the current table must be provided. The default is True.
        can_have_untested_keys : bool, optional
            If LightWin should remain calm when some keys are provided in the
            ``.toml`` but do not correspond to any :class:`KeyValConfSpec`. The
            default is False.

        """
        self.name = name
        self.specs = {spec.key: spec for spec in specs}
        self.is_mandatory = is_mandatory
        self.can_have_untested_keys = can_have_untested_keys

    def _get_proper_spec(self, spec_name: str) -> KeyValConfSpec | None:
        """Get the specification for the property named ``spec_name``."""
        spec = self.specs.get(spec_name, None)
        if spec is not None:
            return spec
        if self.can_have_untested_keys:
            return
        logging.error(
            f"The table {self.name} has no specs for property {spec_name}"
        )
        raise IOError(
            f"The table {self.name} has no specs for property {spec_name}"
        )

    def to_toml_strings(self, toml_subdict: dict[str, Any]) -> list[str]:
        """Convert the given dict in string that can be put in a ``.toml``."""
        strings = [f"[{self.name}]"]
        for key, val in toml_subdict.items():
            spec = self._get_proper_spec(key)
            if spec is None:
                continue
            strings.append(spec.to_toml_string(val))

        return strings

    def validate(self, toml_subdict: dict[str, Any], **kwargs) -> bool:
        """Check that all the key-values in ``toml_subdict`` are valid."""
        validations = [self._mandatory_keys_are_present(toml_subdict.keys())]
        for key, val in toml_subdict.items():
            spec = self._get_proper_spec(key)
            if spec is None:
                continue
            validations.append(spec.validate(val, **kwargs))

        all_is_validated = all(validations)
        if not all_is_validated:
            logging.error(
                "At least one error was raised treating {self.table}"
            )

        return all_is_validated

    def _mandatory_keys_are_present(self, toml_keys: Collection[str]) -> bool:
        """Ensure that all the mandatory parameters are defined."""
        they_are_all_present = True

        for key, spec in self.specs.items():
            if not spec.is_mandatory:
                continue
            if key in toml_keys:
                continue
            they_are_all_present = False
            logging.error(f"The key {key} should be given but was not found.")

        return they_are_all_present

    def generate_dummy_dict(
        self, only_mandatory: bool = True
    ) -> dict[str, Any]:
        """Generate a default dummy dict that should let LightWin work."""
        dummy_conf = {
            spec.key: spec.default_value
            for spec in self.specs.values()
            if spec.is_mandatory or not only_mandatory
        }
        return dummy_conf
