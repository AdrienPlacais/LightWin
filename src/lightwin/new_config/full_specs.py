"""Gather in a single object all the parameters for LW to run."""

import logging
from collections.abc import Collection
from typing import Any

from lightwin.new_config.beam_specs import BEAM_CONFIG
from lightwin.new_config.files_specs import FILES_CONFIG
from lightwin.new_config.specifications import TableConfSpec


class FullConfSpec:
    """Define all the LightWin inputs, their types, allowed values, etc."""

    def __init__(self) -> None:
        """Define static specifications.

        In the future, may add different mandatory specs, for example if
        failures are to be fixed or not.

        """
        self.specs = {
            "beam": TableConfSpec("beam", BEAM_CONFIG),
            "files": TableConfSpec("files", FILES_CONFIG),
        }

    def _get_proper_spec(self, spec_name: str) -> TableConfSpec:
        """Get the specifications for the table named ``spec_name``."""
        spec = self.specs.get(spec_name, None)
        if spec is not None:
            return spec
        logging.error(f"There is no specs for table {spec_name}")
        raise IOError(f"There is no specs for table {spec_name}")

    def to_toml_string(self, toml_fulldict: dict[str, dict[str, Any]]) -> str:
        """Convert the given dict in string that can be put in a ``.toml``."""
        strings = []
        for key, val in toml_fulldict.items():
            spec = self._get_proper_spec(key)
            strings.append(spec.to_toml_string(val))

        return "\n".join(strings)

    def validate(
        self, toml_fulldict: dict[str, dict[str, Any]], **kwargs
    ) -> bool:
        """Check that all the tables in ``toml_fulldict`` are valid."""
        validations = [self._mandatory_keys_are_present(toml_fulldict.keys())]
        for table_name, toml_subdict in toml_fulldict.items():
            spec = self._get_proper_spec(table_name)
            validations.append(spec.validate(toml_subdict, **kwargs))

        all_is_validated = all(validations)
        if not all_is_validated:
            logging.error(
                "At least one error was raised treating configuration"
            )

        return all_is_validated

    def _mandatory_keys_are_present(
        self, toml_tables: Collection[str]
    ) -> bool:
        """Ensure that all the mandatory parameters are defined."""
        they_are_all_present = True

        for table, spec in self.specs.items():
            if not spec.is_mandatory:
                continue
            if table in toml_tables:
                continue
            they_are_all_present = False
            logging.error(
                f"The table entry {table} should be given but was not found."
            )

        return they_are_all_present
