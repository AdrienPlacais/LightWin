"""Define several helper functions for proper ``.toml`` formatting."""

import logging
from pathlib import Path
from typing import Any


def str_toml(key: str, value: Any) -> str:
    """Format the value for proper toml writing."""
    if not isinstance(value, str):
        try:
            value = str(value)
        except TypeError:
            msg = (
                f"You gave to {key = } the {value = }, which is not "
                "broadcastable to a string."
            )
            logging.error(msg)
            raise TypeError(msg)
    return '"' + value + '"'


def bool_toml(key: str, value: Any) -> str:
    """Format the value for proper toml writing."""
    if not isinstance(value, bool):
        try:
            value = bool(value)
        except TypeError:
            msg = (
                f"You gave to {key = } the {value = }, which is not "
                "broadcastable to a bool."
            )
            logging.error(msg)
            raise TypeError(msg)

    if value:
        return "true"
    return "false"
