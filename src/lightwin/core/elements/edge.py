"""Define :class:`Edge`. It does nothing.

.. todo::
    Check behavior w.r.t. LATTICE.

"""

import logging
from functools import lru_cache

from lightwin.core.elements.element import Element
from lightwin.tracewin_utils.line import DatLine


@lru_cache(1)
def warn_edge() -> None:
    """Raise this warning only once.

    https://stackoverflow.com/questions/31953272/logging-print-message-only-once

    """
    logging.warning(
        "Documentation does not mention that EDGE element should be ignored by"
        " LATTICE. So why did I set increment_lattice_idx to False?"
    )


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
        warn_edge()
