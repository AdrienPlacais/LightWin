"""Hold mismatch related functions.

It has its own module as this quantity is pretty specific.

"""

import logging

from lightwin.optimisation.objective.objective import (
    MinimizeMismatch as _MinimizeMismatch,
)


class MinimizeMismatch(_MinimizeMismatch):
    """Minimize a mismatch factor.

    .. deprecated::
        Prefer ``from lightwin.optimisation.objective.objective import ...``
        path.

    """

    def __init__(self, *args, **kwargs) -> None:
        """Instantiate object, log deprecation warning."""
        logging.warning(
            "MinimizeMismatch has moved to "
            "lightwin.optimisation.objective, please update your import."
        )
        super().__init__(*args, **kwargs)
