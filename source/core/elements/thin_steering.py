"""Define :class:`ThinSteering`. It does nothing."""

from core.elements.element import Element
from tracewin_utils.line import DatLine


class ThinSteering(Element):
    """A dummy object."""

    base_name = "TS"
    increment_lattice_idx = False
    is_implemented = False

    def __init__(
        self,
        line: DatLine,
        dat_idx: int | None = None,
        **kwargs: str,
    ) -> None:
        """Force an element with null-length."""
        super().__init__(line, dat_idx, **kwargs)
        self.length_m = 0.0
