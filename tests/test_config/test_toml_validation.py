"""Ensure that loading and validating ``.toml`` works as expected."""

from pathlib import Path

import pytest

from lightwin.new_config.config_manager import process_config

DATA_DIR = Path("data", "example")


@pytest.mark.implementation
def test():
    """Test."""
    config_path = DATA_DIR / "lightwin.toml"
    config_keys = {"beam": "beam", "files": "files"}
    config = process_config(config_path, config_keys, warn_mismatch=True)
    assert isinstance(config, dict)
