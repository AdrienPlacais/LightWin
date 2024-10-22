"""Gather in a single object all the parameters for LW to run."""

import logging
from pathlib import Path
from typing import Any, Literal

from lightwin.config.specs.beam_calculator_specs import (
    BEAM_CALCULATOR_MONKEY_PATCHES,
    BEAM_CALCULATORS_CONFIGS,
)
from lightwin.config.specs.beam_specs import BEAM_CONFIG, BeamTableConfSpec
from lightwin.config.specs.design_space_specs import DESIGN_SPACE_CONFIGS
from lightwin.config.specs.evaluators_specs import EVALUATORS_CONFIG
from lightwin.config.specs.files_specs import FILES_CONFIG, FilesTableConfSpec
from lightwin.config.specs.plots_specs import PLOTS_CONFIG
from lightwin.config.specs.wtf_specs import WTF_CONFIGS, WTF_MONKEY_PATCHES
from lightwin.config.table_spec import TableConfSpec


class ConfSpec:
    """Define structure of a configuration object.

    Parameters
    ----------
    MANDATORY_CONFIG_ENTRIES : tuple[str, ...]
        Entries that you must declare for this :class:`ConfSpec` to work.

    """

    MANDATORY_CONFIG_ENTRIES: tuple[str, ...] = ()

    def __init__(
        self,
        files: str = "",
        beam: str = "",
        beam_calculator: str = "",
        post_beam_calculator: str = "",
        plots: str = "",
        evaluators: str = "",
        design_space: str = "",
        wtf: str = "",
        **kwargs,
    ) -> None:
        """Declare the attributes."""
        table_of_specs = []
        if files:
            table_of_specs.append(
                FilesTableConfSpec("files", files, FILES_CONFIG)
            )
        if beam:
            table_of_specs.append(BeamTableConfSpec("beam", beam, BEAM_CONFIG))
        if beam_calculator:
            table_of_specs.append(
                TableConfSpec(
                    "beam_calculator",
                    beam_calculator,
                    BEAM_CALCULATORS_CONFIGS,
                    selectkey_n_default=("tool", "Envelope1D"),
                    monkey_patches=BEAM_CALCULATOR_MONKEY_PATCHES,
                )
            )
        if post_beam_calculator:
            table_of_specs.append(
                TableConfSpec(
                    "beam_calculator",
                    post_beam_calculator,
                    BEAM_CALCULATORS_CONFIGS,
                    selectkey_n_default=("tool", "Envelope1D"),
                    monkey_patches=BEAM_CALCULATOR_MONKEY_PATCHES,
                )
            )
        if plots:
            table_of_specs.append(TableConfSpec("plots", plots, PLOTS_CONFIG))
        if evaluators:
            table_of_specs.append(
                TableConfSpec("evaluators", evaluators, EVALUATORS_CONFIG)
            )
        if design_space:
            table_of_specs.append(
                TableConfSpec(
                    "design_space",
                    design_space,
                    DESIGN_SPACE_CONFIGS,
                    selectkey_n_default=("from_file", True),
                )
            )
        if wtf:
            table_of_specs.append(
                TableConfSpec(
                    "wtf",
                    wtf,
                    WTF_CONFIGS,
                    selectkey_n_default=("strategy", "k out of n"),
                    monkey_patches=WTF_MONKEY_PATCHES,
                )
            )
        self.tables_of_specs = tuple(table_of_specs)

    def __repr__(self) -> str:
        """Print info on how object was instantiated."""
        tables_info = (
            [f"{self.__class__.__name__}("]
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
        """Get the :class:`.TableConfSpec` named ``table_id``.

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
        original_toml_folder: Path | None = None,
        **kwargs,
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
        original_toml_folder : pathlib.Path | None, optional
            Where the original ``.toml`` was; this is used to resolve paths
            relative to this location.

        Returns
        -------
        list[str]
            The ``.toml`` content that can be directly written to a ``.toml``
            file.

        """
        strings = []
        for key, val in toml_fulldict.items():
            spec = self._get_proper_table(key, id_type=id_type)
            strings += spec.to_toml_strings(
                val, original_toml_folder=original_toml_folder, **kwargs
            )

        return strings

    def prepare(
        self,
        toml_fulldict: dict[str, dict[str, Any]],
        toml_folder: Path,
        id_type: Literal[
            "configured_object", "table_entry"
        ] = "configured_object",
        **kwargs,
    ) -> bool:
        """Check that all the tables in ``toml_fulldict`` are valid.

        Also edit some values if necessary.

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
            validations.append(
                spec.prepare(toml_subdict, toml_folder=toml_folder, **kwargs)
            )

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

        for table_id in self.MANDATORY_CONFIG_ENTRIES:
            try:
                _ = self._get_proper_table(
                    table_id, id_type="configured_object"
                )

            except ValueError:
                logging.error(
                    f"The table entry {table_id} should be given but was not "
                    "found."
                )
                they_are_all_present = False
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


class SimplestConfSpec(ConfSpec):
    """Hold all the LightWin inputs, their types, allowed values, etc.

    Defined for a run without optimization.

    """

    MANDATORY_CONFIG_ENTRIES = (
        "beam",
        "files",
        "beam_calculator",
    )  #:

    def __init__(
        self,
        *,
        beam: str = "beam",
        files: str = "files",
        beam_calculator: str = "beam_calculator",
    ) -> None:
        """Define static specifications.

        In the future, may add different mandatory specs, for example if
        failures are to be fixed or not.

        """
        super().__init__(
            beam=beam,
            files=files,
            beam_calculator=beam_calculator,
        )
