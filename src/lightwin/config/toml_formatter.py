"""Define several helper functions for proper ``TOML`` formatting."""

import logging
from typing import Any

import numpy as np


def format_for_toml(key: str, value: Any, preferred_type: type) -> str:
    """Format the key-value pair so that it matches ``toml`` standard."""
    if isinstance(value, dict):
        formatted_value = _concat_dict(value)
    elif isinstance(value, (list, np.ndarray)):
        formatted_value = _format_list(value, preferred_type)
    else:
        formatted_value = _format_value(key, value, preferred_type)

    return f"{key} = {formatted_value}"


def _concat_dict(value: dict[str, Any]) -> str:
    """Adapt Python dict to toml inline table."""
    entries = (
        format_for_toml(subkey, subval, type(subval))
        for subkey, subval in value.items()
    )
    return "{ " + ", ".join(entries) + " }"


def _format_list(value: list | np.ndarray, preferred_type: type) -> str:
    """Format a list of values, including handling lists of dicts."""
    if all(isinstance(item, dict) for item in value):
        formatted_items = [_concat_dict(item) for item in value]
    else:
        if isinstance(value, np.ndarray):
            value = value.tolist()
        formatted_items = [str(item) for item in value]
    return "[ " + ", ".join(formatted_items) + " ]"


def _format_value(key: str, value: Any, preferred_type: type) -> str:
    """Format the value so that it matches ``toml`` standard."""
    if preferred_type is str:
        return _str_toml(key, value)
    if preferred_type is bool:
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
