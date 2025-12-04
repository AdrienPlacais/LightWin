"""Define the base objects constraining values/types of config parameters."""

import logging
from collections.abc import Callable, Collection
from pathlib import Path
from typing import Any, Literal

from lightwin.config.helper import find_path
from lightwin.config.key_val_conf_spec import KeyValConfSpec

CONFIGURABLE_OBJECTS = (
    "beam",
    "beam_calculator",
    "beam_calculator_post",
    "design_space",
    "evaluators",
    "files",
    "plots",
    "wtf",
)


class TableConfSpec:
    """Set specifications for a table, which holds several key-value pairs.

    .. note::
        This object can be subclassed for specific configuration needs, eg
        :class:`.BeamTableConfSpec`.

    """

    def __init__(
        self,
        configured_object: Literal[
            "beam",
            "beam_calculator",
            "beam_calculator_post",
            "design_space",
            "evaluators",
            "files",
            "plots",
            "wtf",
        ],
        table_entry: str,
        specs: (
            Collection[KeyValConfSpec]
            | dict[str, Collection[KeyValConfSpec]]
            | dict[bool, Collection[KeyValConfSpec]]
        ),
        is_mandatory: bool = True,
        can_have_untested_keys: bool = False,
        selectkey_n_default: tuple[str, str | bool] | None = None,
        monkey_patches: (
            dict[str, dict[str, Callable]]
            | dict[bool, dict[str, Callable]]
            | None
        ) = None,
    ) -> None:
        """Set a table of properties. Correspond to a [table] in the ``TOML``.

        Parameters
        ----------
        configured_object :
            Name of the object that will receive associated parameters.
        table_entry :
            Name of the table in the ``TOML`` file, without brackets.
        specs :
            The :class:`.KeyValConfSpec` objects in the current table. When the
            format of the table depends on the value of a key, provide a
            dictionary linking every possible table with the corresponding
            value.
        is_mandatory :
            If the current table must be provided.
        can_have_untested_keys :
            If LightWin should remain calm when some keys are provided in the
            ``TOML`` but do not correspond to any :class:`.KeyValConfSpec`.
        selectkey_n_default :
            Must be given if ``specs`` is a dict. First value is name of the
            spec, second value is default value. We will look for this spec in
            the configuration file and select the proper ``Collection`` of
            ``KeyValConfSpec`` accordingly.
        monkey_patches :
            Same keys as ``specs``, to override some default methods.

        """
        self.configured_object = configured_object
        self.table_entry = table_entry

        self._specs = specs
        self._monkey_patches = monkey_patches
        #: Selector used when ``specs`` is a dictionary.
        #: When ``specs`` is given as a dictionary (e.g. `{ "modeA": [...],
        #: "modeB": [...] }`), the configuration format depends on the value of
        #: a specific key inside the ``TOML`` table. This argument tells
        #: `TableConfSpec` which ``TOML`` key to read and which default value
        #: to use if that key is absent.
        #: The tuple must contain:
        #:
        #: - the name of the selector key (a key expected in the ``TOML``
        #:   table),
        #: - the default value to fall back on if the selector key is not
        #:   present.
        #:
        #: Example
        #: -------
        #:
        #: .. code-block:: python
        #:
        #:    specs = {
        #:      "Envelope1D": envelope_1d_specs,
        #:      "TraceWin": tracewin_specs,
        #:    }
        #:    selectkey_n_default = ("beam_calculator", "Envelope1D")
        #:
        #: then:
        #:
        #: - the value of ``toml_table["beam_calculator"]`` determines whether
        #:   `envelope_1d_specs` or `tracewin_specs` is used;
        #: - if `"beam_calculator"` is not provided in the ``TOML``,
        #:   `"Envelope1D"` is used.
        #:
        #: This parameter **must** be provided whenever ``specs`` is a
        #: dictionary. It must be ``None`` when ``specs`` is a flat collection.
        self._selectkey_n_default = selectkey_n_default
        self.specs_as_dict = self._set_specs_as_dict()

        self.is_mandatory = is_mandatory
        self.can_have_untested_keys = can_have_untested_keys
        logging.info(f".toml table [{table_entry}] loaded!")

    def __repr__(self) -> str:
        """Print how the object was created."""
        info = (
            "TableConfSpec:",
            f"{self.configured_object:>16s} -> [{self.table_entry}]",
        )
        return " ".join(info)

    def _get_specs(
        self, toml_table: dict[str, Any] | None = None
    ) -> list[KeyValConfSpec]:
        """Get the proper list of :class:`.KeyValConfSpec`.

        Used when we need to read the value of ``_selectkey_n_default``
        in the ``TOML`` to choose precisely which configuration we should
        match.

        Parameters
        ----------
        toml_table :
            A ``TOML`` table. We use it only if ``self._specs`` is not already
            a ``Collection``. We look for the value of
            ``self._selectkey_n_default[0]`` and use it to select the proper
            table. If not provided, we fall back on a default value.

        """
        if not isinstance(self._specs, dict):
            assert self._selectkey_n_default is None, (
                f"You provided {self._selectkey_n_default = }, but the"
                f" table will always be {self._specs} as you did not give a "
                "dictionary."
            )
            return list(self._specs)

        assert self._selectkey_n_default is not None, (
            "You must provide the name of the key that will allow to select "
            f"proper table among {self._specs.keys()}"
        )
        value = self._selectkey_n_default[1]
        if toml_table is not None:
            value = toml_table.get(self._selectkey_n_default[0])
        assert isinstance(value, (str, bool))

        specs = self._specs[value]
        assert specs is not None

        if self._monkey_patches is not None:
            monkey_patches = self._monkey_patches[value]
            self._apply_monkey_patches(monkey_patches)
        return list(specs)

    def _set_specs_as_dict(
        self, toml_table: dict[str, Any] | None = None
    ) -> dict[str, KeyValConfSpec]:
        """
        Select and prepare :class:`.KeyValConfSpec` used to validate this table.

        This method is responsible for determining which specification set
        applies to the current table, especially when the available specs
        depend on the value of a key inside the ``TOML`` table (via
        :attr:`._selectkey_n_default`).

        The returned value is a dictionary mapping spec names to
        :class:`.KeyValConfSpec` instances. It performs the following steps:

        1. Determine the correct list of :class:`.KeyValConfSpec` objects by
           calling ``_get_specs(toml_table)``. If ``specs`` was provided as a
           dictionary, this uses the selector key defined in
           :attr:`._selectkey_n_default` to choose the appropriate spec set. If
           ``specs`` is a flat collection, that collection is returned
           unchanged.
        2. Apply override rules and remove any earlier specs that should be
           replaced (``overrides_previously_defined=True``) using
           :func:`._remove_overriden_keys`.
        3. Return the cleaned specifications as a ``{spec.key: spec}``
           dictionary.

        This method is called multiple times during
        :meth:`.TableConfSpec.prepare`:

        - once before validation, to build the spec set according to the raw
          ``TOML`` input;
        - once after post-treatment, to ensure the final ``specs_as_dict``
          reflects any modifications (e.g. inserted defaults, resolved paths,
          or monkey patches applied during spec selection).

        Parameters
        ----------
        toml_table :
            A table from the ``TOML`` configuration file. Required only when
            spec selection depends on user-provided values. When omitted,
            default values from :attr:`._selectkey_n_default` are used.

        Returns
        -------
        dict[str, KeyValConfSpec]
            The active specification dictionary for this table.

        """
        specs = self._get_specs(toml_table)
        specs = _remove_overriden_keys(specs)
        return {spec.key: spec for spec in specs}

    def _get_proper_spec(self, spec_name: str) -> KeyValConfSpec | None:
        """Get the specification for the property named ``spec_name``."""
        spec = self.specs_as_dict.get(spec_name, None)
        if spec is not None:
            return spec
        if self.can_have_untested_keys:
            return
        msg = (
            f"The table {self.table_entry} has no specs for property "
            f"{spec_name}"
        )
        logging.error(msg)
        raise OSError(msg)

    def to_toml_strings(
        self,
        toml_table: dict[str, Any],
        original_toml_folder: Path | None = None,
        **kwargs,
    ) -> list[str]:
        """Convert the given dict in string that can be put in a ``TOML``.

        Parameters
        ----------
        toml_table :
            A dictionary corresponding to a ``TOML`` table.
        original_toml_folder :
            Where the original ``TOML`` was; this is used to resolve paths
            relative to this location.

        Returns
        -------
        list[str]
            All the ``TOML`` lines corresponding to the table under study.

        """
        strings = [f"[{self.table_entry}]"]
        for key, val in toml_table.items():
            spec = self._get_proper_spec(key)
            if spec is None:
                continue
            strings.append(
                spec.to_toml_string(
                    val, original_toml_folder=original_toml_folder, **kwargs
                )
            )

        return strings

    def _pre_treat(self, toml_table: dict[str, Any], **kwargs) -> None:
        """Insert default values for missing keys.

        You can inherit this method to perform additional pre-treating logic.

        """
        self._insert_defaults(toml_table, **kwargs)

    def _insert_defaults(self, toml_table: dict[str, Any], **kwargs) -> None:
        """Insert default values for missing keys."""
        for key, spec in self.specs_as_dict.items():
            if key in toml_table:
                continue
            if not spec.is_mandatory:
                continue
            if spec.default_value is not None:
                logging.warning(
                    f"The key {key} is missing in [{self.table_entry}]. "
                    f"Using default value: {spec.default_value}."
                )
                toml_table[key] = spec.default_value

    def prepare(self, toml_table: dict[str, Any], **kwargs) -> bool:
        """Validate the config dict and edit some values."""
        self.specs_as_dict = self._set_specs_as_dict(toml_table)
        self._pre_treat(toml_table, **kwargs)
        validations = self._validate(toml_table, **kwargs)
        self._post_treat(toml_table, **kwargs)
        self.specs_as_dict = self._set_specs_as_dict(toml_table)
        return validations

    def _validate(self, toml_table: dict[str, Any], **kwargs) -> bool:
        """Check that key-values in ``toml_table`` are valid.

        This method is defined to keep an implementation of the original method
        even when ``validate`` is overriden by a monkey patch.

        """
        validations = [self._mandatory_keys_are_present(toml_table.keys())]
        for key, val in toml_table.items():
            spec = self._get_proper_spec(key)
            if spec is None:
                continue
            validations.append(spec.validate(val, **kwargs))

        all_is_validated = all(validations)
        if not all_is_validated:
            logging.error(
                f"At least one error was raised treating {self.table_entry}"
            )

        return all_is_validated

    def _post_treat(self, toml_table: dict[str, Any], **kwargs) -> None:
        """Edit some values, create new ones. To call after validation.

        .. note::
            In general, the edited values will not be validated. To handle with
            care.

        """
        self._make_paths_absolute(toml_table, **kwargs)

    def _make_paths_absolute(
        self,
        toml_table: dict[str, Any],
        toml_folder: Path | None = None,
        **kwargs,
    ) -> None:
        """Transform the paths to their absolute resolved version."""
        for key, val in toml_table.items():
            spec = self._get_proper_spec(key)
            if spec is None:
                continue
            if Path not in spec.types:
                continue

            try:
                new_val = find_path(toml_folder, val)
                toml_table[key] = new_val
            except FileNotFoundError:
                continue

    def _mandatory_keys_are_present(self, toml_keys: Collection[str]) -> bool:
        """Ensure that all the mandatory parameters are defined."""
        they_are_all_present = True

        for key, spec in self.specs_as_dict.items():
            if not spec.is_mandatory:
                continue
            if key in toml_keys:
                continue
            if (default := spec.default_value) is not None:
                logging.warning(
                    f"The key {key} should be given but was not found. Will "
                    f"use default value: {default}. You may want to set this "
                    f"key explicitly; allowed values:\n{spec.allowed_values}"
                )
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
            for spec in self.specs_as_dict.values()
            if spec.is_mandatory or not only_mandatory
        }
        return dummy_conf

    def _apply_monkey_patches(
        self, monkey_patches: dict[str, Callable]
    ) -> None:
        """Override the base methods."""
        for method_name, method in monkey_patches.items():
            setattr(self, method_name, method.__get__(self, self.__class__))


def _remove_overriden_keys(
    specs: Collection[KeyValConfSpec],
) -> list[KeyValConfSpec]:
    """Remove the :class:`.KeyValConfSpec` objects to override.

    .. todo::
       Not Pythonic at all.

    """
    cleaned_specs = []
    keys = []
    for spec in specs:
        if key := spec.key not in keys:
            cleaned_specs.append(spec)
            keys.append(key)
            continue

        assert spec.overrides_previously_defined, (
            f"The key {spec} is defined twice, but it was not declared that it"
            " can override."
        )
        idx_to_del = keys.index(key)
        del cleaned_specs[idx_to_del]
        del keys[idx_to_del]
        cleaned_specs.append(spec)
        keys.append(key)

    return list(specs)
