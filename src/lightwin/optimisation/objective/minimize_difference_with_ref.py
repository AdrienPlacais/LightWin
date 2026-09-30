"""Define a simple optimization objective.

It is a simple difference over a given quantity between the reference linac and
the linac under tuning.

"""

import logging

logger = logging.getLogger(__name__)

from lightwin.optimisation.objective.objective import (
    MinimizeDifferenceWithRef as _MinimizeDifferenceWithRef,
)


class MinimizeDifferenceWithRef(_MinimizeDifferenceWithRef):
    """A simple difference at a given point between ref and fix.

    .. deprecated::
        Prefer ``from lightwin.optimisation.objective.objective import ...``
        path.

    """

    def __init__(self, *args, **kwargs) -> None:
        """Instantiate object, log deprecation warning."""
        logger.warning(
            "MinimizeDifferenceWithRef has moved to "
            "lightwin.optimisation.objective, please update your import."
        )
        super().__init__(*args, **kwargs)
