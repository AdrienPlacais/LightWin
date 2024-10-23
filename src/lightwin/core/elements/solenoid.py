"""Define :class:`Solenoid`."""

from lightwin.core.elements.element import Element
from lightwin.tracewin_utils.line import DatLine


class Solenoid(Element):
    """A partially defined solenoid."""

    base_name = "SOL"
    n_attributes = 3

    def __init__(
        self,
        line: DatLine,
        dat_idx: int | None = None,
        **kwargs: str,
    ) -> None:
        """Check number of attributes."""
        super().__init__(line, dat_idx, **kwargs)
