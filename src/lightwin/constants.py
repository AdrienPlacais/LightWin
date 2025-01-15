"""Define constants."""

from pathlib import Path

# Physics
c = 2.99792458e8

# Folders
_lw_base_folder = Path(__file__).absolute().parents[2]
doc_folder = _lw_base_folder / "docs/"
example_folder = _lw_base_folder / "data/example/"
example_results = example_folder / "results"
test_folder = _lw_base_folder / "tests/"
test_data_folder = test_folder / "data/"
# Files
example_config = example_folder / "lightwin.toml"
example_constraints = example_folder / "constraints.csv"
example_dat = example_folder / "example.dat"
example_ini = example_folder / "example.ini"
example_machine_config = example_folder / "machine_config.toml"
example_variables = example_folder / "variables.csv"
test_config = test_data_folder / "lightwin.toml"
test_constraints = test_data_folder / "constraints.csv"
test_dat = test_data_folder / "test.dat"
test_ini = test_data_folder / "test.ini"
test_machine_config = test_data_folder / "machine_config.toml"
test_variables = test_data_folder / "variables.csv"

NEW = False
