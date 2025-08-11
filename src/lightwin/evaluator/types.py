"""Define some types to lighten the typing."""

from typing import Callable

import numpy as np

value_t = np.ndarray | float
ref_value_t = np.ndarray | float
post_treated_value_t = np.ndarray | float
post_treater_t = Callable[[value_t, ref_value_t], post_treated_value_t]
tester_t = Callable[[post_treated_value_t], float | bool | None]
