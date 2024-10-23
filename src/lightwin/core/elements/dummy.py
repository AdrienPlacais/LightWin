"""Define :class:`DummyElement`. It does nothing."""

from lightwin.core.elements.element import Element
from lightwin.tracewin_utils.line import DatLine


class DummyElement(Element):
    """A dummy object."""

    is_implemented = False

    def __init__(
        self,
        line: DatLine,
        dat_idx: int | None = None,
        **kwargs,
    ) -> None:
        """Force an element with null-length, with no index."""
        super().__init__(line, dat_idx, **kwargs)
        self.length_m = 0.0
