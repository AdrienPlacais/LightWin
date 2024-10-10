"""Gather in a single object all the parameters for LW to run.

.. note::
    For now, there a single :class:`FullConfSpec`. But we may create different
    objects in the future, according to the various types of run.

"""

import logging
from typing import Any, Literal

from lightwin.new_config.specs.beam_calculator_envelope1d_specs import (
    ENVELOPE1D_CONFIG,
)
from lightwin.new_config.specs.beam_calculator_tracewin_specs import (
    TRACEWIN_CONFIG,
)
from lightwin.new_config.specs.beam_specs import BEAM_CONFIG
from lightwin.new_config.specs.files_specs import FILES_CONFIG
from lightwin.new_config.specs_base_objects import TableConfSpec

BEAM_CALCULATORS_CONFIGS = {
    "TraceWin": TRACEWIN_CONFIG,
    "Envelope1D": ENVELOPE1D_CONFIG,
    # "Envelope3D": ENVELOPE3D_CONFIG,
}


class FullConfSpec:
    """Hold all the LightWin inputs, their types, allowed values, etc.

    Parameters
    ----------
    MANDATORY_CONFIG_ENTRIES : tuple[str, ...]
        Entries that you should must for this :class:`FullConfSpec` to work.

    """

    MANDATORY_CONFIG_ENTRIES = ("files", "beam_calculator", "beam")  #:

    def __init__(
        self,
        *,
        beam_table_name: str = "beam",
        files_table_name: str = "files",
        beam_calculator_table_name: str = "beam_calculator",
    ) -> None:
        """Define static specifications.

        In the future, may add different mandatory specs, for example if
        failures are to be fixed or not.

        """
        self.tables_of_specs = (
            TableConfSpec("beam", beam_table_name, BEAM_CONFIG),
            TableConfSpec("files", files_table_name, FILES_CONFIG),
            TableConfSpec(
                "beam_calculator", beam_calculator_table_name, TRACEWIN_CONFIG
            ),  # temporary )
        )

    def __repr__(self) -> str:
        """Print info on how object was instantiated."""
        tables_info = (
            ["FullConfSpec("]
            + ["\t" + table.__repr__() for table in self.tables_of_specs]
            + [")"]
        )
        return "\n".join(tables_info)

    def _get_proper_table(
        self,
        table_id: str,
        id_type: Literal[
            "configured_object", "table_entry"
        ] = "configured_object",
    ) -> TableConfSpec:
        """Get the specifications for the table named ``table_id``.

        Parameters
        ----------
        table_id : str
            Name of the desired table.
        id_type : Literal["configured_object", "table_entry"], optional
            If ``table_id`` is the name of the object (eg ``'beam'``) or of the
            table entry in the ``.toml`` (eg ``'my_proton_beam'``, without
            brackets).

        Returns
        -------
        TableConfSpec
            The desired object.

        """
        for table in self.tables_of_specs:
            if table_id != getattr(table, id_type):
                continue
            return table

        raise ValueError(
            f"No table with {id_type} attribute = {table_id} found in "
            f"{self.__repr__()}."
        )

    def to_toml_strings(
        self,
        toml_fulldict: dict[str, dict[str, Any]],
        id_type: Literal[
            "configured_object", "table_entry"
        ] = "configured_object",
    ) -> list[str]:
        """Convert the given dict in string that can be put in a ``.toml``.

        Parameters
        ----------
        toml_fulldict : dict[str, dict[str, Any]]
            Holds the full configuration.
        id_type : Literal["configured_object", "table_entry"], optional
            If ``toml_fulldict`` keys are name of the object (eg ``'beam'``) or
            of the table entry in the ``.toml`` (eg ``'my_proton_beam'``,
            without brackets).

        Returns
        -------
        list[str]
            The ``.toml`` content that can be directly written to a ``.toml``
            file.

        """
        strings = []
        for key, val in toml_fulldict.items():
            spec = self._get_proper_table(key, id_type=id_type)
            strings += spec.to_toml_strings(val)

        return strings

    def validate(
        self,
        toml_fulldict: dict[str, dict[str, Any]],
        id_type: Literal[
            "configured_object", "table_entry"
        ] = "configured_object",
        **kwargs,
    ) -> bool:
        """Check that all the tables in ``toml_fulldict`` are valid.

        Parameters
        ----------
        toml_fulldict : dict[str, dict[str, Any]]
            Holds the full configuration.
        id_type : Literal["configured_object", "table_entry"], optional
            If ``toml_fulldict`` keys are name of the object (eg ``'beam'``) or
            of the table entry in the ``.toml`` (eg ``'my_proton_beam'``,
            without brackets).

        Returns
        -------
        bool
            If the dict is valid or not.
        """
        validations = [self._mandatory_keys_are_present]
        for table_name, toml_subdict in toml_fulldict.items():
            spec = self._get_proper_table(table_name, id_type=id_type)
            validations.append(spec.validate(toml_subdict, **kwargs))

        all_is_validated = all(validations)
        if not all_is_validated:
            logging.error(
                "At least one error was raised treating configuration"
            )

        return all_is_validated

    @property
    def _mandatory_keys_are_present(self) -> bool:
        """Ensure that all the mandatory parameters are defined."""
        they_are_all_present = True

        for table in self.tables_of_specs:
            if not table.is_mandatory:
                continue
            if table.configured_object in self.MANDATORY_CONFIG_ENTRIES:
                continue
            they_are_all_present = False
            logging.error(
                f"The table entry {table} should be given but was not found."
            )

        return they_are_all_present

    def generate_dummy_dict(
        self, only_mandatory: bool = True
    ) -> dict[str, dict[str, Any]]:
        """Generate a default dummy dict that should let LightWin work."""
        dummy_conf = {
            spec.table_entry: spec.generate_dummy_dict(
                only_mandatory=only_mandatory
            )
            for spec in self.tables_of_specs
            if spec.is_mandatory or not only_mandatory
        }
        return dummy_conf
