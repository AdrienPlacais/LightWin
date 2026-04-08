"""Define helper function for objectives."""

from collections import defaultdict
from collections.abc import Collection

from lightwin.core.elements.element import Element
from lightwin.optimisation.objective.objective import (
    MAGIC_ALL_ELTS,
    MAGIC_ALL_ELTS_T,
    Objective,
)


def by_element(
    objectives: Collection[Objective],
) -> dict[Element | MAGIC_ALL_ELTS_T, list[Objective]]:
    """Sort the provided objectives per |E|.

    Parameters
    ----------
    objectives :
        Objectives you want the evaluation position from.

    Returns
    -------
        Maps every |E| at which at least one objective is evaluated to
        corresponding objectives.

    """
    objectives_by_element: dict[
        Element | MAGIC_ALL_ELTS_T, list[Objective]
    ] = defaultdict(list)

    for obj in objectives:
        get_kwargs = getattr(obj, "get_kwargs", None)
        if get_kwargs is None:
            continue
        element = get_kwargs.get("elt", MAGIC_ALL_ELTS)
        objectives_by_element[element].append(obj)
    return objectives_by_element
