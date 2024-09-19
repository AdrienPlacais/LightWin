"""Define several helper functions for proper ``.toml`` formatting."""

import logging
from typing import Any


def format_for_toml(input_type: type, key: str, value: Any) -> str:
    """Format the value so that it matches ``toml`` standard."""
    if input_type is str:
        return _str_toml(key, value)
    if input_type is bool:
        return _bool_toml(key, value)
    return f"{value}"


def _str_toml(key: str, value: Any) -> str:
    """Surround value with quotation marks."""
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


def _bool_toml(key: str, value: Any) -> str:
    """Return 'true' or 'false'."""
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
