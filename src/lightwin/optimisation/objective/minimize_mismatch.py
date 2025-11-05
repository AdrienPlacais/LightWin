"""Hold mismatch related functions.

It has its own module as this quantity is pretty specific.

"""

import logging

from lightwin.optimisation.objective.objective import (
    MinimizeMismatch as _MinimizeMismatch,
)


class MinimizeMismatch(_MinimizeMismatch):

    def __init__(self, *args, **kwargs):
        logging.warning(
            "MinimizeMismatch has moved to "
            "lightwin.optimisation.objective, please update your import."
        )
        return super().__init__(*args, **kwargs)
