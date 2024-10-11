"""Define parameters necessary to define files."""

from pathlib import Path

from lightwin.constants import example_dat, example_folder
from lightwin.new_config.key_val_conf_spec import KeyValConfSpec

FILES_CONFIG = (
    KeyValConfSpec(
        key="dat_file",
        types=(str, Path),
        description="Path to the ``.dat`` file",
        default_value=example_dat,
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
