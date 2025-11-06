"""Define an objective that is a quantity must be within some bounds.

.. todo::
    Implement loss functions.

"""

import logging

from lightwin.optimisation.objective.objective import (
    QuantityIsBetween as _QuantityIsBetween,
)


class QuantityIsBetween(_QuantityIsBetween):

    def __init__(self, *args, **kwargs):
        logging.warning(
            "QuantityIsBetween has moved to "
            "lightwin.optimisation.objective, please update your import."
        )
        return super().__init__(*args, **kwargs)
