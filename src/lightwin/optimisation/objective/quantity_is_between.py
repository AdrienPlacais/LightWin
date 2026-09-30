"""Define an objective that is a quantity must be within some bounds.

.. todo::
    Implement loss functions.

"""

import logging

logger = logging.getLogger(__name__)

from lightwin.optimisation.objective.objective import (
    QuantityIsBetween as _QuantityIsBetween,
)


class QuantityIsBetween(_QuantityIsBetween):
    """Quantity must be within some bounds.

    .. deprecated::
        Prefer ``from lightwin.optimisation.objective.objective import ...``
        path.

    """

    def __init__(self, *args, **kwargs) -> None:
        """Instantiate object, log deprecation warning."""
        logger.warning(
            "QuantityIsBetween has moved to "
            "lightwin.optimisation.objective, please update your import."
        )
        super().__init__(*args, **kwargs)
