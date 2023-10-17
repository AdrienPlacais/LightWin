#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 13 11:07:31 2023.

@author: placais

In this module we define some helper functions to filter
:class:`.ListOfElements` or ``list`` of :class:`.Element`.

.. todo::
    Filtering consistency. Also, use more types and less ``nature``.

"""
import logging
from typing import Any
from functools import partial

import numpy as np

from core.elements.element import Element
from core.list_of_elements.list_of_elements import ListOfElements


# actually, type of elements and outputs is Nested[list[Element]]
def filter_out(elts: Any,
               to_exclude: tuple[type]) -> Any:
    """Filter out types while keeping the input list structure."""
    if isinstance(elts[0], list):
        return [filter_out(sub, to_exclude) for sub in elts]

    elif isinstance(elts, list):
        return list(filter(lambda elt: not isinstance(elt, to_exclude),
                           elts))
    else:
        raise TypeError("Wrong type for data filtering.")

    return elts


def filter_elts(elts: ListOfElements | list[Element], key: str, val: Any
                ) -> list[Element]:
    """Shortcut for filtering elements according to (key, val)."""
    return list(filter(lambda elt: elt.get(key) == val, elts))


# Legacy, prefer sorting on the type
filter_cav = partial(filter_elts, key='nature', val='FIELD_MAP')


def elt_at_this_s_idx(elts: ListOfElements | list[Element],
                      s_idx: int, show_info: bool = False
                      ) -> Element | None:
    """Give the element where the given index is.

    Parameters
    ----------
    elts : ListOfElements | list[Element]
        List of elements in which to look for.
    s_idx : int
        Index to look for.
    show_info : bool
        If the element that we found should be outputed.

    Returns
    -------
    elt : Element | None
        Element where the mesh index ``s_idx`` is in ``elts``.

    """
    for elt in elts:
        if s_idx in range(elt.idx['s_in'], elt.idx['s_out']):
            if show_info:
                logging.info(
                    f"Mesh index {s_idx} is in {elt.get('elt_info')}.\n"
                    + f"Indexes of this elt: {elt.get('idx')}.")
            return elt

    logging.warning(f"Mesh index {s_idx} not found.")
    return None


def equivalent_elt_idx(elts: ListOfElements | list[Element],
                       elt: Element | str) -> int:
    """
    Return the index of element from ``elts`` corresponding to ``elt``.

    .. important::
        This routine uses the name of the element and not its adress. So
        it will not complain if the :class:`.Element` object that you asked for
        is not in this list of elements.
        In the contrary, it was meant to find equivalent cavities between
        different lists of elements.

    See also
    --------
    :func:`equivalent_elt`
    :meth:`.Accelerator.equivalent_elt`

    Parameters
    ----------
    elts : ListOfElements | list[Element]
        List of elements where you want the position.
    elt : Element | str
        Element of which you want the position. If you give a str, it should be
        the name of an element. If it is an :class:`.Element`, we take its name
        in the routine. Magic keywords ``'first'``, ``'last'`` are also
        accepted.

    Returns
    -------
    int
        Index of equivalent element.

    """
    if not isinstance(elt, str):
        elt = elt.get("elt_name")

    magic_keywords = {"first": 0, "last": -1}
    names = [x.elt_info["elt_name"] for x in elts]

    if elt in names:
        return names.index(elt)

    if elt in magic_keywords:
        return magic_keywords[elt]

    logging.error(f"Element {elt} not found in this list of elements.")
    logging.debug(f"List of elements is:\n{elts}")
    raise IOError(f"Element {elt} not found in this list of elements.")


def equivalent_elt(elts: ListOfElements | list[Element],
                   elt: Element | str) -> Element:
    """
    Return the element from ``elts`` corresponding to ``elt``.

    .. important::
        This routine uses the name of the element and not its adress. So
        it will not complain if the :class:`.Element` object that you asked for
        is not in this list of elements.
        In the contrary, it was meant to find equivalent cavities between
        different lists of elements.

    See also
    --------
    :func:`equivalent_elt_idx`
    :meth:`.Accelerator.equivalent_elt`

    Parameters
    ----------
    elts : ListOfElements | list[Element]
        List of elements where you want the position.
    elt : Element | str
        Element of which you want the position. If you give a str, it should be
        the name of an element. If it is an :class:`.Element`, we take its name
        in the routine. Magic keywords ``'first'``, ``'last'`` are also
        accepted.

    Returns
    -------
    out_elt : Element
        Equivalent element.

    """
    out_elt_idx = equivalent_elt_idx(elts, elt)
    out_elt = elts[out_elt_idx]
    return out_elt


def indiv_to_cumul_transf_mat(tm_cumul_in: np.ndarray,
                              r_zz_elt: list[np.ndarray], n_steps: int
                              ) -> np.ndarray:
    """
    Compute cumulated transfer matrix.

    Parameters
    ----------
    tm_cumul_in : np.ndarray
        Cumulated transfer matrix @ first element. Should be eye matrix if we
        are at the first element.
    r_zz_elt : list[np.ndarray]
        List of individual transfer matrix of the elements.
    n_steps : int
        Number of elements or elements slices.

    Returns
    -------
    cumulated_transfer_matrices : np.ndarray
        Cumulated transfer matrices.

    """
    cumulated_transfer_matrices = np.full((n_steps, 2, 2), np.NaN)
    cumulated_transfer_matrices[0] = tm_cumul_in
    for i in range(1, n_steps):
        cumulated_transfer_matrices[i] = \
            r_zz_elt[i - 1] @ cumulated_transfer_matrices[i - 1]
    return cumulated_transfer_matrices
