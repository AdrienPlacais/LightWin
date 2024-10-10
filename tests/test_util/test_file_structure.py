"""Test that the files that should exist do exist."""

from pathlib import Path
from typing import Literal

import pytest

from lightwin.constants import (
    example_config,
    example_constraints,
    example_dat,
    example_folder,
    example_ini,
    example_machine_config,
    example_variables,
)

params = [
    pytest.param(
        (example_folder, "directory"),
        id="example_folder",
    ),
]


@pytest.mark.smoke
@pytest.mark.implementation
@pytest.mark.parametrize(
    ("file_or_folder", "nature"),
    [
        (example_folder, "directory"),
        (example_constraints, "file"),
        (example_config, "file"),
        (example_dat, "file"),
        (example_ini, "file"),
        (example_machine_config, "file"),
        (example_variables, "file"),
    ],
)
def test_example_files_exist(
    file_or_folder: Path, nature: Literal["directory", "file"]
) -> None:
    """Test that all the defined folders and files exist."""
    match nature:
        case "directory":
            meth_name = "is_dir"
        case "file":
            meth_name = "is_file"
        case _:
            raise ValueError("bad test")

    meth = getattr(file_or_folder, meth_name)
    assert meth(), f"{file_or_folder} should exist but was not found"
