"""Test that :file:`example.toml` and the :class:`.TableConfSpec`. match.

We sequentially load every table of :file:`example.toml` and check it with the
corresponding :class:`.TableConfSpec`.

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
from lightwin.new_config.config_manager import load_toml
from lightwin.new_config.full_specs import ConfSpec

params = (
    pytest.param(({"beam": "beam"},)),
    pytest.param(({"files": "files"},)),
    pytest.param(({"beam_calculator": "generic_tracewin"},)),
    pytest.param(({"beam_calculator": "generic_envelope1d"},)),
    pytest.param(({"plots": "plots"},)),
    pytest.param(({"evaluators": "evaluators"},)),
    pytest.param(({"design_space": "design_space_from_file"},)),
    pytest.param(({"design_space": "design_space_calculated"},)),
    pytest.param(({"wtf": "wtf_k_out_of_n"},)),
    pytest.param(({"wtf": "wtf_l_neighboring_lattices"},)),
    pytest.param(({"wtf": "wtf_manual"},)),
)  #: kwargs to create a dummy :class:`.ConfSpec` per possible :class:`.TableConfSpec`


@pytest.fixture(scope="class", params=params)
def toml_dict_with_one_table(
    request: pytest.FixtureRequest,
) -> dict[str, dict[str, Any]]:
    """Load the :file:`example.toml` with a unique table entry."""
    (config_key,) = request.param
    toml_dict = load_toml(
        example_config, config_key, warn_mismatch=True, override=None
    )
    return toml_dict


@pytest.fixture(scope="class", params=params)
def conf_spec_with_one_table_spec(request: pytest.FixtureRequest) -> ConfSpec:
    """Create a :class:`.ConfSpec` holding a single :class:`.TableConfSpec`."""
    (config_key,) = request.param
    conf_spec = ConfSpec(**config_key)
    return conf_spec
