"""Define a base class for :class:`ElementBeamCalculatorParameters`.

It is an attribute of an :class:`.Element`, and holds parameters that depend on
both the :class:`.Element` under study and the :class:`.BeamCalculator` solver
that is used.

Currently, it is used by :class:`.Envelope1D` and :class:`.Envelope3D` only, as
:class:`.TraceWin` handles it itself.

"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

import numpy as np

from lightwin.util.helper import recursive_items
from lightwin.util.typing import GETTABLE_BEAM_CALC_PARAMETERS_T


class ElementBeamCalculatorParameters(ABC):
    """Parent class to hold solving parameters. Attribute of :class:`.Element`.

    Used by :class:`.Envelope1D` and :class:`.Envelope3D`.

    """

    def has(self, key: str) -> bool:
        """Tell if the required attribute is in this class."""
        return key in recursive_items(vars(self))

    def get(
        self,
        *keys: GETTABLE_BEAM_CALC_PARAMETERS_T,
        to_numpy: bool = True,
        **kwargs: Any,
    ) -> Any:
        """
        Shorthand to get attributes.

        Parameters
        ----------
        *keys :
            One or more attribute names to retrieve.
        to_numpy :
            If True, convert lists to NumPy arrays. If False, convert NumPy
            arrays to lists.
        **kwargs :
            Reserved for future extensions.

        Returns
        -------
        Any
            A single value if one key is given, or a tuple of values.

        """
        values = [getattr(self, key, None) for key in keys]

        if to_numpy:
            values = [
                np.array(v) if isinstance(v, list) else v for v in values
            ]
        else:
            values = [
                v.tolist() if isinstance(v, np.ndarray) else v for v in values
            ]

        return values[0] if len(values) == 1 else tuple(values)

    @abstractmethod
    def re_set_for_broken_cavity(self) -> None | Callable:
        """Update solver after a cavity is broken."""
