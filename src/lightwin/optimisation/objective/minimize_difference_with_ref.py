"""Define a simple optimization objective.

It is a simple difference over a given quantity between the reference linac and
the linac under tuning.

"""

import logging

from lightwin.optimisation.objective.objective import (
    MinimizeDifferenceWithRef as _MinimizeDifferenceWithRef,
)


class MinimizeDifferenceWithRef(_MinimizeDifferenceWithRef):

    def __init__(self, *args, **kwargs):
        logging.warning(
            "MinimizeDifferenceWithRef has moved to "
            "lightwin.optimisation.objective, please update your import."
        )
        return super().__init__(*args, **kwargs)
