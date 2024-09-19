"""Define parameters necessary to define files.

.. todo::
    Replace hard written filepath, prefer inferring it from the location of
    current file

"""

from pathlib import Path

from lightwin.new_config.config_specs import KeyValConfSpec

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
