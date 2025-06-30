"""Define functions to determine the compensation zone.

In most cases, we need to study only a fraction of the linac during
optimisation process. This zone should be as small as possible to reduce
computation time, it should encompass all failed cavities, all compensating
cavities, as well as the place where objectives are evaluated.

.. important::
    In this module, the indexes are *element* indexes, not cavity.

.. todo::
    end_section, elt.name

.. todo::
    ``full_linac`` seems useless. Could be a strategy instead of an override
    setting. Would need to edit the :class:`.ObjectiveFactory` too.

.. note::
    ``[*a, *b]`` will concatenate the two ``Iterable`` ``a`` and ``b``. Same as
    ``a + b`` but will work with every ``Iterable``, not just ``list``.

"""

import logging
from collections.abc import Collection, Iterable
from typing import Any, Literal

from lightwin.core.elements.element import Element
from lightwin.core.list_of_elements.list_of_elements import ListOfElements

POSITION_TO_INDEX_T = Literal[
    "end of last altered lattice",
    "one lattice after last altered lattice",
    "end of last failed lattice",
    "one lattice after last failed lattice",
    "end of linac",
    "end of every altered lattice",
]


def zone_to_recompute(
    broken_elts: ListOfElements,
    objective_position_preset: Collection[POSITION_TO_INDEX_T],
    fault_idx: Iterable[int],
    comp_idx: Iterable[int],
    full_lattices: bool = False,
    full_linac: bool = False,
    start_at_beginning_of_linac: bool = False,
) -> tuple[list[Element], list[Element]]:
    """Determine the elements from the zone to recompute.

    We use in this routine *element* indexes, not cavity indexes.

    Parameters
    ----------
    broken_elts :
        :class:`.ListOfElements` from the broken linac.
    objective_position_preset :
        Short strings that must be in :data:`.POSITION_TO_INDEX` dictionary to
        determine where the objectives should be evaluated.
    fault_idx, comp_idx :
        Cavity index of the faults and compensating cavities, directly
        converted to element index in the routine.
    full_lattices :
        If you want the compensation zone to encompass full lattices only. It
        is a little bit slower as more :class:`.Element` are calculated. Plus,
        it has no impact even with :class:`.TraceWin` solver. Keeping it in
        case it has an impact that I did not see.
    full_linac :
        To compute full linac at every step of the optimisation process. Can be
        very time-consuming, but may be necessary with some future
        :class:`.BeamCalculator`.
    start_at_beginning_of_linac :
        To make compensation zone start at the beginning of  the linac. The
        default is False.

    Returns
    -------
    elts_of_compensation_zone : list[Element]
        :class:`.Element` objects of the compensation zone.
    objective_elements : list[Element]
        Where objectives are evaluated.

    """
    objectives_positions_idx = [
        i
        for preset in objective_position_preset
        for i in _zone(preset, broken_elts, fault_idx, comp_idx)
    ]
    objective_elements = [broken_elts[i] for i in objectives_positions_idx]

    idx_start_compensation_zone = min([*fault_idx, *comp_idx])

    if start_at_beginning_of_linac:
        logging.info(
            "Force start of compensation zone @ first element of the linac."
        )
        idx_start_compensation_zone = 0
    if full_lattices:
        logging.info("Force compensation zone span over full lattices.")
        idx_start_compensation_zone = (
            _reduce_idx_start_to_include_full_lattice(
                idx_start_compensation_zone, broken_elts
            )
        )

    idx_end_compensation_zone = max(objectives_positions_idx)
    if full_linac:
        logging.info("Force compensation zone span over full linac.")
        idx_start_compensation_zone = 0
        idx_end_compensation_zone = len(broken_elts) - 2

    elts_of_compensation_zone = broken_elts[
        idx_start_compensation_zone : idx_end_compensation_zone + 1
    ]
    return elts_of_compensation_zone, objective_elements


def _zone(preset: POSITION_TO_INDEX_T, *args) -> list[int]:
    """Give compensation zone, and position where objectives are checked."""
    if preset not in POSITION_TO_INDEX:
        logging.error(f"Position {preset} not recognized.")
        raise OSError(f"Position {preset} not recognized.")
    index = POSITION_TO_INDEX[preset](*args)
    if isinstance(index, int):
        index = [index]
    return index


def _end_last_altered_lattice(
    elts: ListOfElements, fault_idx: Iterable[int], comp_idx: Iterable[int]
) -> int:
    """Evaluate obj at the end of the last lattice w/ an altered cavity."""
    idx_last = max([*fault_idx, *comp_idx])
    idx_lattice_last = elts[idx_last].get("lattice")
    idx_eval = elts.by_lattice[idx_lattice_last][-1].get(
        "elt_idx", to_numpy=False
    )
    return idx_eval


def _one_lattice_after_last_altered_lattice(
    elts: ListOfElements, fault_idx: Iterable[int], comp_idx: Iterable[int]
) -> int:
    """Evaluate objective one lattice after the last comp or failed cav."""
    idx_last = max([*fault_idx, *comp_idx])
    idx_lattice_last = elts[idx_last].get("lattice") + 1
    if idx_lattice_last > len(elts.by_lattice):
        logging.warning(
            "You asked for a lattice after the end of the linac. Revert back "
            "to previous lattice, i.e. end of linac."
        )
        idx_lattice_last -= 1
    idx_eval = elts.by_lattice[idx_lattice_last][-1].get(
        "elt_idx", to_numpy=False
    )
    return idx_eval


def _end_last_failed_lattice(
    elts: ListOfElements, fault_idx: Collection[int], comp_idx: Collection[int]
) -> int:
    """Evaluate obj at the end of the last lattice w/ a failed cavity."""
    idx_last = max(fault_idx)
    idx_lattice_last = elts[idx_last].get("lattice")
    idx_eval = elts.by_lattice[idx_lattice_last][-1].get(
        "elt_idx", to_numpy=False
    )
    return idx_eval


def _one_lattice_after_last_failed_lattice(
    elts: ListOfElements, fault_idx: Collection[int], comp_idx: Collection[int]
) -> int:
    """Evaluate 1 lattice after end of the last lattice w/ a failed cavity."""
    idx_after = max(fault_idx) + 1
    idx_lattice_after = elts[idx_after].get("lattice")
    idx_eval = elts.by_lattice[idx_lattice_after][-1].get(
        "elt_idx", to_numpy=False
    )
    return idx_eval


def _end_linac(elts: ListOfElements, fault_idx: Any, comp_idx: Any) -> int:
    """Evaluate objective at the end of the linac."""
    return elts[-1].get("elt_idx")


def _reduce_idx_start_to_include_full_lattice(
    idx: int, elts: ListOfElements
) -> int:
    """Force compensation zone to start at the 1st element of lattice."""
    elt = elts[idx]
    lattice_idx = elt.get("lattice", to_numpy=False)
    elt = elts.by_lattice[lattice_idx][0]
    idx = elt.get("elt_idx", to_numpy=False)
    return idx


def _end_of_every_altered_lattice(
    elts: ListOfElements, fault_idx: Collection[int], comp_idx: Collection[int]
) -> list[int]:
    idx_first = min([*fault_idx, *comp_idx])
    idx_lattice_first = elts[idx_first].get("lattice")

    idx_last = max([*fault_idx, *comp_idx])
    idx_lattice_last = elts[idx_last].get("lattice")

    indexes_eval = [
        elts.by_lattice[i][-1].get("elt_idx", to_numpy=False)
        for i in range(idx_lattice_first, idx_lattice_last + 1)
    ]
    return indexes_eval


POSITION_TO_INDEX = {
    "end of last altered lattice": _end_last_altered_lattice,
    "one lattice after last altered lattice": _one_lattice_after_last_altered_lattice,
    "end of last failed lattice": _end_last_failed_lattice,
    "one lattice after last failed lattice": _one_lattice_after_last_failed_lattice,
    "end of linac": _end_linac,
    "end of every altered lattice": _end_of_every_altered_lattice,
}  #:
