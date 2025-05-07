"""Define tests for the :class:`.Element` class."""

import pytest

from lightwin.core.elements.element import Element
from lightwin.tracewin_utils.line import DatLine


class DummyLine(DatLine):
    """Minimal valid DatLine for testing an element."""

    def __init__(self) -> None:
        super().__init__("DRIFT 10.0", idx=0)


class DummyElement(Element):
    """Minimal concrete subclass of Element for testing."""

    n_attributes = 1

    def __init__(self, **kwargs):
        super().__init__(line=DummyLine(), **kwargs)


@pytest.fixture
def element() -> DummyElement:
    return DummyElement()


def test_has_direct_attr(element: DummyElement) -> None:
    assert element.has("elt_info")
    assert not element.has("nonexistent")


def test_has_property_name(element: DummyElement) -> None:
    assert element.has("name")


def test_has_nested_attr(element: DummyElement) -> None:
    assert element.has("elt_idx")


@pytest.mark.xfail(
    condition=True,
    reason="One key returned an array instead of a float",
    raises=AssertionError,
)
def test_get_direct_attr(element: DummyElement) -> None:
    assert element.get("length_m") == 0.1


def test_get_property_name(element: DummyElement) -> None:
    name = element.get("name")
    assert isinstance(name, str)


def test_get_nested_attr(element: DummyElement) -> None:
    assert element.get("elt_idx") == -1


@pytest.mark.xfail(
    condition=True,
    reason="One key returned an array of None instead of a None",
    raises=AssertionError,
)
def test_get_missing_key(element: DummyElement) -> None:
    assert element.get("nonexistent") is None  # pyright: ignore


def test_get_multiple_keys(element: DummyElement) -> None:
    nature, elt_idx = element.get("nature", "elt_idx")
    assert nature == "DRIFT"
    assert elt_idx == -1
