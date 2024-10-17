"""Test that :file:`example.toml` and the :class:`.TableConfSpec` match.

We sequentially load each relatable table of :file:`example.toml`, and match it
with the corresponding :class:`.TableSpec`.

.. todo::
    Writting to ``.toml`` will fail with lists of dictionaries

"""

from typing import Any

import pytest

from lightwin.constants import (
    example_config,
    example_dat,
    example_folder,
    example_ini,
    example_machine_config,
)
from lightwin.new_config.config_manager import (
    dict_to_toml,
    load_toml,
    process_config,
)
from lightwin.new_config.full_specs import ConfSpec

CONFIG_KEYS = (
    pytest.param(({"beam": "beam"},), id="Beam configuration"),
    pytest.param(({"files": "files"},), id="Files configuration"),
    pytest.param(
        ({"beam_calculator": "generic_tracewin"},), id="TraceWin configuration"
    ),
    pytest.param(
        ({"beam_calculator": "generic_envelope1d"},),
        id="Envelope1D configuration",
    ),
    pytest.param(
        ({"plots": "plots_minimal"},), id="Simple plots configuration"
    ),
    pytest.param(
        ({"evaluators": "evaluators"},), id="Simple evaluators configuration"
    ),
    pytest.param(
        ({"design_space": "design_space_from_file"},),
        id="Configuration of a design space from .csv files",
    ),
    pytest.param(
        ({"design_space": "generic_design_space"},),
        id="Configuration of a design space without any external file",
    ),
    pytest.param(
        ({"wtf": "generic_wtf"},),
        id="Configuration of compensating cavities with k out of n method.",
    ),
    pytest.param(
        ({"wtf": "wtf_l_neighboring_lattices"},),
        id=(
            "Configuration of compensating cavities with l neighboring "
            "lattices method."
        ),
    ),
    pytest.param(
        ({"wtf": "wtf_manual"},),
        id="Configuration of compensating cavities with manual method.",
    ),
)  #: Links every LightWin parameter with a table from :file:`example.toml`.


@pytest.fixture(scope="class", params=CONFIG_KEYS)
def config_key(request: pytest.FixtureRequest) -> dict[str, str]:
    """Give the dict for a single table study.

    Returns
    -------
    config_key : dict[str, str]
        A dictionary with a unique key-value pair. The key is the name of a
        LightWin configuration entry (eg ``beam`` or ``wtf``), the value is a
        table in :file:`example.toml` (eg ``generic_envelope1d``).
    """
    (config_key,) = request.param
    return config_key


@pytest.fixture(scope="class")
def toml_dict(config_key: dict[str, str]) -> dict[str, dict[str, Any]]:
    """Check that loading the table does not raise any error."""
    toml_dict = load_toml(
        example_config, config_key, warn_mismatch=True, override=None
    )
    return toml_dict


@pytest.fixture(scope="class")
def conf_spec(config_key: dict[str, str]) -> ConfSpec:
    """Check that the configuration specifications can be created."""
    conf_spec = ConfSpec(**config_key)
    return conf_spec


@pytest.mark.smoke
@pytest.mark.implementation
class TestSingleTable:
    """Test a single [table] from the ``.toml``.

    This tests will be run individually for every table in the
    :file:`example.toml`, as defined in ``params``.

    """

    def test_load(self, toml_dict: dict[str, dict[str, Any]]) -> None:
        """Check that loading the table does not raise any error."""
        assert isinstance(toml_dict, dict), f"Error loading {config_key}"

    def test_instantiate_conf_spec(self, conf_spec: ConfSpec) -> None:
        """Check that the configuration specifications can be created."""
        assert isinstance(
            conf_spec, ConfSpec
        ), f"Error creating ConfSpec for {config_key}."

    def test_validate(
        self, toml_dict: dict[str, dict[str, Any]], conf_spec: ConfSpec
    ) -> None:
        """Check that the example table matches associated specifications."""
        assert conf_spec.validate(
            toml_dict, id_type="configured_object", toml_folder=example_folder
        ), f"Mismatch between {toml_dict = } and {conf_spec = }"

    def test_config_can_be_saved_to_file(
        self,
        config_key: dict[str, str],
        toml_dict: dict[str, dict[str, Any]],
        conf_spec: ConfSpec,
        tmp_path_factory: pytest.TempPathFactory,
    ):
        """Check that the loaded config can be saved back to ``.toml``."""
        toml_path = (
            tmp_path_factory.mktemp("test_configurations")
            / "test_config_can_be_saved_to_file.toml"
        )
        dict_to_toml(
            toml_dict,
            toml_path,
            conf_spec,
            original_toml_folder=example_folder,
        )
        process_config(toml_path, config_key, conf_specs=conf_spec)
        assert True

    def atest_generate_works(self, *args, **kwargs) -> None:
        """Check that creating a dummy toml dict works."""
        pass

    def atest_generated_is_valid(self, *args, **kwargs) -> None:
        """Check the the generated dummy toml dict is valid."""
        pass
