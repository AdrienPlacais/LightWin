"""Define how LightWin should be configured.

.. todo::
    Make giving a default value mandatory. Define ``generate`` methods to
    create the specifications from nothing.

"""

import logging
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lightwin.config.helper import find_file

CONFIGURATION_SPECIFICATIONS = {}


@dataclass
class KeyValConfSpec:
    """Set specifications for a single key-value pair."""

    key: str
    types: tuple[type, ...]
    description: str = ""
    allowed_values: Collection[Any] | None = None
    default_value: Any | None = None
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
        assert toml_folder is not None
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
            formatted = '"' + value + '"'

        return f"{self.key} = {formatted}"


class TableConfSpec:
    """Set specifications for a table, which holds several key-value pairs."""

    def __init__(
        self,
        name: str,
        specs: Collection[KeyValConfSpec],
        is_mandatory: bool = True,
    ) -> None:
        """Set the thing."""
        self.name = name
        self.specs = {spec.key: spec for spec in specs}
        self.is_mandatory = is_mandatory

    def _get_proper_spec(self, spec_name: str) -> KeyValConfSpec:
        """Get the specification for the property named ``spec_name``."""
        spec = self.specs.get(spec_name, None)
        if spec is not None:
            return spec
        logging.error(
            f"The table {self.name} has no specs for property {spec_name}"
        )
        raise IOError(
            f"The table {self.name} has no specs for property {spec_name}"
        )

    def to_toml_string(self, toml_subdict: dict[str, Any]) -> str:
        """Convert the given dict in string that can be put in a ``.toml``."""
        strings = [f"[self.name]"]
        for key, val in toml_subdict.items():
            spec = self._get_proper_spec(key)
            strings.append(spec.to_toml_string(val))

        return "\n".join(strings)

    def validate(self, toml_subdict: dict[str, Any], **kwargs) -> bool:
        """Check that all the key-values in ``toml_subdict`` are valid."""
        validations = [self._mandatory_keys_are_present(toml_subdict.keys())]
        for key, val in toml_subdict.items():
            spec = self._get_proper_spec(key)
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
