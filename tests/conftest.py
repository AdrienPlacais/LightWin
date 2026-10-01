"""Provide configuration for all tests."""

import pytest

from lightwin.core import files_specs


@pytest.fixture(autouse=True)
def no_logging_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the function setting up logging by a dummy func.

    .. note::
        The ``autouse`` makes it called before every test.

    """
    monkeypatch.setattr(
        files_specs, "set_up_logging", lambda *args, **kwargs: None
    )
