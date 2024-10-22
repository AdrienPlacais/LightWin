"""Define some constants for the :class:`.Envelope1D`."""

from typing import Literal

ENVELOPE1D_METHODS = ("RK4", "leapfrog")  #:
ENVELOPE1D_METHODS_T = Literal["RK4", "leapfrog"]
