"""Provide tests for :class:`.ElementBeamCalculatorParameters`."""

import numpy as np
import pytest

from lightwin.beam_calculation.parameters.element_parameters import (
    ElementBeamCalculatorParameters,
)


class DummyElementBeamCalculatorParameters(ElementBeamCalculatorParameters):
    """Subclass of :class:`.ElementBeamCalculatorParameters` for testing.

    Exposes a scalar, a list, and a numpy array attribute to exercise the
    ``has`` and ``get`` interface without requiring a real beam-calculator
    setup.

    """

    def __init__(self) -> None:
        """Set up minimal attributes covering the three supported types."""
        self.scalar = 42
        self.list_value = [1, 2, 3]
        self.array_value = np.array([4.0, 5.0, 6.0])

    def re_set_for_broken_cavity(self) -> None:
        """No-op implementation required by the abstract base class."""
        return


@pytest.fixture
def calc_param() -> DummyElementBeamCalculatorParameters:
    """Return fresh :class:`DummyElementBeamCalculatorParameters` instance."""
    return DummyElementBeamCalculatorParameters()


def test_has_existing_key(
    calc_param: DummyElementBeamCalculatorParameters,
) -> None:
    """``has`` returns True for attributes that exist on the instance."""
    assert calc_param.has("scalar")
    assert calc_param.has("list_value")


def test_has_missing_key(
    calc_param: DummyElementBeamCalculatorParameters,
) -> None:
    """``has`` returns False for attributes that do not exist."""
    assert not calc_param.has("nonexistent")


def test_get_scalar(calc_param: DummyElementBeamCalculatorParameters) -> None:
    """``get`` returns a scalar attribute unchanged."""
    assert calc_param.get("scalar") == 42


def test_get_list_value_to_numpy(
    calc_param: DummyElementBeamCalculatorParameters,
) -> None:
    """``get`` converts a list attribute to a numpy array by default."""
    result = calc_param.get("list_value")
    assert isinstance(result, np.ndarray)
    np.testing.assert_array_equal(result, np.array([1, 2, 3]))


def test_get_list_value_no_numpy(
    calc_param: DummyElementBeamCalculatorParameters,
) -> None:
    """``get`` returns a list as-is when ``to_numpy=False``."""
    result = calc_param.get("list_value", to_numpy=False)
    assert isinstance(result, list)
    assert result == [1, 2, 3]


def test_get_array_value_to_numpy(
    calc_param: DummyElementBeamCalculatorParameters,
) -> None:
    """``get`` returns np array attribute unchanged when ``to_numpy=True``."""
    result = calc_param.get("array_value")
    assert isinstance(result, np.ndarray)
    np.testing.assert_array_equal(result, np.array([4.0, 5.0, 6.0]))


def test_get_array_value_no_numpy(
    calc_param: DummyElementBeamCalculatorParameters,
) -> None:
    """``get`` converts a numpy array to a list when ``to_numpy=False``."""
    result = calc_param.get("array_value", to_numpy=False)
    assert isinstance(result, list)
    assert result == [4.0, 5.0, 6.0]


def test_get_multiple_keys(
    calc_param: DummyElementBeamCalculatorParameters,
) -> None:
    """``get`` returns a tuple when called with multiple keys."""
    scalar, arr = calc_param.get("scalar", "array_value")
    assert scalar == 42
    np.testing.assert_array_equal(arr, np.array([4.0, 5.0, 6.0]))


def test_get_missing_key_returns_none(
    calc_param: DummyElementBeamCalculatorParameters,
) -> None:
    """``get`` returns None for an attribute that does not exist."""
    assert calc_param.get("nonexistent") is None
