"""Define constants."""

from pathlib import Path

# Physics
c = 2.99792458e8

# Folders
example_folder = Path(__file__).absolute().parents[2] / "data/example/"
test_folder = Path(__file__).absolute().parents[2] / "tests/"
# Files
example_config = example_folder / "lightwin.toml"
example_dat = example_folder / "example.dat"
example_ini = example_folder / "example.ini"
example_machine_config = example_folder / "machine_config.toml"
