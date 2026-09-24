"""Hold :class:`Quad`."""

from lightwin.core.elements.element import Element
from lightwin.tracewin_utils.line import DatLine


class Quad(Element):
    """A partially defined quadrupole."""

    base_name = "QP"
    n_attributes = range(3, 10)

    def __init__(
        self,
        line: DatLine,
        dat_idx: int | None = None,
        idx_in_lattice: int = -1,
        lattice: int = -1,
        section: int = -1,
        **kwargs: str | int,
    ) -> None:
        """Check number of attributes, set gradient."""
        super().__init__(
            line,
            dat_idx,
            idx_in_lattice=idx_in_lattice,
            lattice=lattice,
            section=section,
            **kwargs,
        )
        self.grad = float(line.splitted[2])
