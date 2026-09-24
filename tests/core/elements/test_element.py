"""Define tests for the :class:`.Element` class."""

import pytest

from lightwin.core.elements.element import Element
from lightwin.tracewin_utils.line import DatLine


class DummyLine(DatLine):
    """Minimal valid :class:`.DatLine` for testing an element."""

    def __init__(self) -> None:
        """Create a simple line defining a drift."""
        super().__init__("DRIFT 10.0", idx=0)


class DummyElement(Element):
    """Minimal concrete subclass of :class:`.Element` for testing."""

    n_attributes = 1

    def __init__(self, **kwargs) -> None:
        """Create a simple drift element."""
        super().__init__(line=DummyLine(), **kwargs)


@pytest.fixture
def element() -> DummyElement:
    """Return a default :class:`DummyElement` instance."""
    return DummyElement()


def test_has_direct_attr(element: DummyElement) -> None:
    """``has`` finds a direct attribute and rejects an unknown one."""
    assert element.has("elt_info")
    assert not element.has("nonexistent")


def test_has_property_name(element: DummyElement) -> None:
    """``has`` finds attributes exposed via properties."""
    assert element.has("name")


def test_has_nested_attr(element: DummyElement) -> None:
    """``has`` resolves keys nested inside ``idx``."""
    assert element.has("elt_idx")


def test_get_direct_attr(element: DummyElement) -> None:
    """``get`` returns a direct attribute with the correct value."""
    assert element.get("length_m") == 0.01


def test_get_property_name(element: DummyElement) -> None:
    """``get`` returns the element name as a string."""
    name = element.get("name")
    assert isinstance(name, str)


def test_get_nested_attr(element: DummyElement) -> None:
    """``get`` retrieves a key nested inside ``idx``."""
    assert element.get("elt_idx") == -1


def test_get_missing_key(element: DummyElement) -> None:
    """``get`` returns None for a key that does not exist."""
    assert element.get("nonexistent") is None  # pyright: ignore


def test_get_multiple_keys(element: DummyElement) -> None:
    """``get`` returns a tuple when called with multiple keys."""
    nature, elt_idx = element.get("nature", "elt_idx")
    assert nature == "DRIFT"
    assert elt_idx == -1
