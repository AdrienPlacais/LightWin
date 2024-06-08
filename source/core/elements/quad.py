"""This module holds :class:`Quad`."""

from core.elements.element import Element
from tracewin_utils.line import DatLine


class Quad(Element):
    """A partially defined quadrupole."""

    base_name = "QP"
    n_attributes = range(3, 10)

    def __init__(
        self,
        line: DatLine,
        dat_idx: int | None = None,
        **kwargs: str,
    ) -> None:
        """Check number of attributes, set gradient."""
        super().__init__(line, dat_idx, **kwargs)
        self.grad = float(line.splitted[2])
