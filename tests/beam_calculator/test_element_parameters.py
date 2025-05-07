"""Provide tests for :class:`.ElementBeamCalculatorParameters`."""

import numpy as np
import pytest

from lightwin.beam_calculation.parameters.element_parameters import (
    ElementBeamCalculatorParameters,
)


class DummyElementBeamCalculatorParameters(ElementBeamCalculatorParameters):
    """Concrete class for testing base functionality."""

    def __init__(self):
        self.scalar = 42
        self.list_value = [1, 2, 3]
        self.array_value = np.array([4.0, 5.0, 6.0])

    def re_set_for_broken_cavity(self):
        return None


@pytest.fixture
def calc_param() -> DummyElementBeamCalculatorParameters:
    return DummyElementBeamCalculatorParameters()


def test_has_existing_key(calc_param):
    assert calc_param.has("scalar")
    assert calc_param.has("list_value")


def test_has_missing_key(calc_param):
    assert not calc_param.has("nonexistent")


def test_get_scalar(calc_param):
    assert calc_param.get("scalar") == 42


def test_get_list_value_to_numpy(calc_param):
    result = calc_param.get("list_value")
    assert isinstance(result, np.ndarray)
    np.testing.assert_array_equal(result, np.array([1, 2, 3]))


def test_get_list_value_no_numpy(calc_param):
    result = calc_param.get("list_value", to_numpy=False)
    assert isinstance(result, list)
    assert result == [1, 2, 3]


def test_get_array_value_to_numpy(calc_param):
    result = calc_param.get("array_value")
    assert isinstance(result, np.ndarray)
    np.testing.assert_array_equal(result, np.array([4.0, 5.0, 6.0]))


def test_get_array_value_no_numpy(calc_param):
    result = calc_param.get("array_value", to_numpy=False)
    assert isinstance(result, list)
    assert result == [4.0, 5.0, 6.0]


def test_get_multiple_keys(calc_param):
    scalar, arr = calc_param.get("scalar", "array_value")
    assert scalar == 42
    np.testing.assert_array_equal(arr, np.array([4.0, 5.0, 6.0]))


def test_get_missing_key_returns_none(calc_param):
    assert calc_param.get("nonexistent") is None
