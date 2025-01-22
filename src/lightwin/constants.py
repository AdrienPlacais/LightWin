"""Define constants."""

from importlib import resources
from pathlib import Path

# Physics
c = 2.99792458e8

# Folders
_lw_base_folder = Path(__file__).absolute().parents[2]
doc_folder = _lw_base_folder / "docs/"
example_folder = _lw_base_folder / "data/example/"
example_results = example_folder / "results"
test_folder = _lw_base_folder / "tests/"

# Files
example_folder = resources.files("lightwin.data.ads")
example_config = example_folder / "lightwin.toml"
example_constraints = example_folder / "constraints.csv"
example_dat = example_folder / "ads.dat"
example_ini = example_folder / "ads.ini"
example_machine_config = example_folder / "machine_config.toml"
example_variables = example_folder / "variables.csv"

NEW = False
