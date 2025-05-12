"""Define base :class:`Element`, declined in Drift, FieldMap, etc.

.. todo::
    clean the patch for the 'name'. my has and get methods do not work with
    @property

"""

import logging
from typing import Any, Literal, Protocol

import numpy as np

from lightwin.beam_calculation.parameters.element_parameters import (
    ElementBeamCalculatorParameters,
)
from lightwin.core.elements.field_maps.cavity_settings import CavitySettings
from lightwin.core.instruction import Instruction
from lightwin.tracewin_utils.line import DatLine
from lightwin.util.helper import recursive_getter, recursive_items
from lightwin.util.typing import GETTABLE_ELT_T, STATUS_T


class Element(Instruction):
    """Generic element.

    Parameters
    ----------
    base_name :
        Short name for the element according to TraceWin. Should be overriden.
    increment_elt_idx :
        If the element should be considered when counting the elements. If
        False, ``elt_idx`` will keep  its default value of ``-1``. As for now,
        there is no element with this attribute set to False.
    increment_lattice_idx :
        If the element should be considered when determining the lattice.
        Should be True for physical elements, such as ``DRIFT``, and False for
        other elements such as ``DIAGNOSTIC``.

    """

    base_name = "ELT"
    increment_elt_idx = True
    increment_lattice_idx = True
    is_implemented = True

    def __init__(
        self,
        line: DatLine,
        dat_idx: int | None = None,
        idx_in_lattice: int = -1,
        lattice: int = -1,
        section: int = -1,
        **kwargs,
    ) -> None:
        """Init parameters common to all elements.

        Parameters
        ----------
        line :
            A line of the ``DAT`` file. If the element was given a name, it
            must not appear in ``line`` but rather in ``name``. First
            element of the list must be in :data:`.implemented_elements`.
        dat_idx :
            Position in the ``DAT`` file.
        name :
            Non-default name of the element, as given in the ``DAT`` file. The
            default is None, in which case an automatic name will be given
            later.

        """
        super().__init__(line, dat_idx, **kwargs)

        self.elt_info = {
            "nature": line.splitted[0],
        }
        self.length_m = 1e-3 * float(line.splitted[1])

        # TODO: init the indexes to -1 or something, to help type hinting
        # dict with pure type: int
        new_idx = {
            "elt_idx": -1,
            "lattice": lattice,
            "idx_in_lattice": idx_in_lattice,
            "section": section,
        }
        self.idx = self.idx | new_idx
        self.beam_calc_param: dict[str, ElementBeamCalculatorParameters] = {}

    def has(self, key: str) -> bool:
        """Check if the given key exists in this element or its nested members.

        Parameters
        ----------
        key :
            Name of the attribute to check.

        Returns
        -------
        bool
            True if the key exists, False otherwise.

        """
        if key == "name":  # @property are not caught by vars(self)
            return True
        return key in recursive_items(vars(self))

    def get(
        self, *keys: GETTABLE_ELT_T, to_numpy: bool = True, **kwargs: Any
    ) -> Any:
        """Get attributes from this class or its nested members.

        Parameters
        ----------
        *keys :
            Names of the desired attributes.
        to_numpy :
            If True, convert lists to NumPy arrays. If False, convert NumPy
            arrays to lists.
        **kwargs :
            Other arguments passed to the recursive getter.

        Returns
        -------
        out :
            A single attribute value if one key is provided, otherwise a tuple
            of values.

        """

        def resolve_key(key: str) -> Any:
            if key == "name":
                return self.name
            if not self.has(key):
                return None
            return recursive_getter(key, vars(self), **kwargs)

        values = [resolve_key(key) for key in keys]

        if to_numpy:
            values = [
                np.array(v) if isinstance(v, list) else v for v in values
            ]
        else:
            values = [
                v.tolist() if isinstance(v, np.ndarray) else v for v in values
            ]

        return values[0] if len(values) == 1 else tuple(values)

    def keep_rf_field(self, *args, **kwargs) -> None:
        """Save data calculated by :meth:`.BeamCalculator.run_with_this`.

        .. deprecated:: 0.6.16
            Prefer :meth:`keep_cavity_settings`

        """
        logging.warning("prefer keep_cavity_settings")
        return self.keep_cavity_settings(*args, **kwargs)

    def keep_cavity_settings(
        self,
        cavity_settings: CavitySettings,
    ) -> None:
        """Save data calculated by :meth:`.BeamCalculator.run_with_this`."""
        raise NotImplementedError("Please override this method.")

    @property
    def is_accelerating(self) -> bool:
        """Say if this element is accelerating or not.

        Will return False by default.

        """
        return False

    @property
    def can_be_retuned(self) -> bool:
        """Tell if we can modify the element's tuning.

        Will return False by default.

        """
        return False

    def update_status(self, new_status: STATUS_T) -> None:
        """Change the status of the element. To override."""
        if not self.can_be_retuned:
            logging.error(
                f"You want to give {new_status = } to the element f{self.name},"
                " which can't be retuned. Status of elements has meaning only "
                "if they can be retuned."
            )
            return

        logging.error(
            f"You want to give {new_status = } to the element f{self.name}, "
            "which update_status method is not defined."
        )


#: Allowed values for the ``pos`` keyword argument in ``get`` methods.
POS_T = Literal["in", "out"]


class ELEMENT_TO_INDEX_T(Protocol):
    """Type for function linking an :class:`Element` or its name to its index.

    In particular, it is used for the ``get`` methods.

    """

    def __call__(
        self,
        *,
        elt: str | Element,
        pos: POS_T | None = None,
        return_elt_idx: bool = False,
    ) -> int | slice: ...

    """Return indexes of element ``elt``.

    Parameters
    ----------
    elt :
        :class:`Element` for which you want position. Can be the
        :attr:`Element.name` attribute or the :class:`Element` instance itself.
    pos :
        Position within the :class:`Element`. If not provided, all indexes of
        :class:`Element` will be returned.
    return_elt_idx :
        Return a position in a :class:`.ListOfElements` instance. Used for
        arguments such as `phi_s`, which holds one value per :class:`.Element`.

    Returns
    -------
    indexes : int | slice
        Index(es) of given ``elt``, at given ``pos``. Returns all indexes in
        this default function.

    """


def default_element_to_index(
    *,
    elt: str | Element,
    pos: POS_T | None = None,
    return_elt_idx: bool = False,
) -> int | slice:
    """Return all indexes whatever the inputs are.

    Parameters
    ----------
    elt :
        :class:`Element` for which you want position. Can be the
        :attr:`Element.name` attribute or the :class:`Element` instance itself.
        Actually unused in this default function.
    pos :
        Position within the :class:`Element`. If not provided, all indexes of
        :class:`Element` will be returned. Actually unused in this default
        function.
    return_elt_idx :
        Return a position in a :class:`.ListOfElements` instance. Used for
        arguments such as `phi_s`, which holds one value per :class:`.Element`.
        Actually unused in this default function.

    Returns
    -------
    indexes : int | slice
        Index(es) of given ``elt``, at given ``pos``. Returns all indexes in
        this default function.

    """
    logging.warning(
        "Actual ``element_to_index`` was not set, you are calling a default. "
        f"{elt = }; {pos = }, {return_elt_idx = }."
    )
    return slice(0, -1)
