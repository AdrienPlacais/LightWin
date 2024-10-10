"""Test that the files that should exist do exist."""

import pytest

from lightwin.constants import example_dat, example_folder


@pytest.mark.smoke
@pytest.mark.implementation
def test_example_folder_exists() -> None:
    """Check if the folder where examples are stored is still here."""
    assert (
        example_folder.is_dir()
    ), f"{example_folder = } does not exists anymore."


@pytest.mark.smoke
@pytest.mark.implementation
def test_example_dat_exists() -> None:
    """Check if the example linac is still here."""
    assert example_dat.is_file(), f"{example_dat = } does not exists anymore."
