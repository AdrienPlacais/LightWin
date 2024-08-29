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


BEAM_CONFIG = (
    KeyValConfSpec(
        key="e_rest_mev",
        types=(float,),
        description=r"Rest energy of particle in :math:`\mathrm{MeV}`",
        default_value=0.0,
    ),
    KeyValConfSpec(
        key="q_adim",
        types=(float,),
        description="Adimensioned charge of particle",
        default_value=1.0,
    ),
    KeyValConfSpec(
        key="e_mev",
        types=(float,),
        description=r"Energy of particle at entrance in :math:`\mathrm{MeV}",
        default_value=1.0,
    ),
    KeyValConfSpec(
        key="f_bunch_mev",
        types=(float,),
        description=r"Beam bunch frequency in :math:\mathrm{MHz}`",
        default_value=100.0,
    ),
    KeyValConfSpec(
        key="i_milli_a",
        types=(float,),
        description=r"Beam current in :math:`\mathrm{mA}`",
        default_value=0.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="sigma",
        types=(list,),
        description=r"Input :math:`\sigma` beam matrix in :math:`\mathrm{m}`;"
        + r" :math:`\mathrm{rad}`. Must be a list of lists of floats that can "
        + "be transformed to a 6*6 matrix.",
        default_value=[[0.0 for _ in range(6)] for _ in range(6)],
    ),
)

example_folder = Path("/home/placais/LightWin/data/example/")

FILES_CONFIG = (
    KeyValConfSpec(
        key="dat_file",
        types=(str, Path),
        description="Path to the ``.dat`` file",
        default_value=example_folder / "example.dat",
        is_a_path_that_must_exists=True,
    ),
    KeyValConfSpec(
        key="project_folder",
        types=(str, Path),
        description="Path output results will be stored file",
        default_value=example_folder / "results/",
        is_mandatory=False,
    ),
)
