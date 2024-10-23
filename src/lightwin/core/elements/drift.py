"""Define :class:`Drift`."""

from lightwin.core.elements.element import Element
from lightwin.tracewin_utils.line import DatLine


class Drift(Element):
    """A simple drift tube."""

    base_name = "DR"
    n_attributes = (2, 3, 5)

    def __init__(
        self,
        line: DatLine,
        dat_idx: int | None = None,
        **kwargs: str,
    ) -> None:
        """Check that number of attributes is valid."""
        super().__init__(line, dat_idx, **kwargs)
