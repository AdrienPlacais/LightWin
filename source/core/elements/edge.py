"""Define :class:`Edge`. It does nothing.

.. todo::
    Check behavior w.r.t. LATTICE.

"""

import logging

from core.elements.element import Element
from tracewin_utils.line import DatLine


class Edge(Element):
    """A dummy object."""

    base_name = "EDG"
    increment_lattice_idx = False
    is_implemented = False

    def __init__(
        self,
        line: DatLine,
        dat_idx: int | None = None,
        **kwargs: str,
    ) -> None:
        """Force an element with null-length, with no index."""
        super().__init__(line, dat_idx, **kwargs)
        self.length_m = 0.0
        logging.warning(
            "Documentation does not mention that EDGE element should be "
            "ignored by LATTICE. So why did I set increment_lattice_idx to "
            "False?"
        )
