"""Define helper function for objectives."""

from collections.abc import Collection

from lightwin.core.elements.element import Element
from lightwin.optimisation.objective.objective import Objective


def by_element(
    objectives: Collection[Objective],
) -> dict[Element, list[Objective]]:
    """Sort the provided objectives per :class:`.Element`."""
    objectives_by_element: dict[Element, list[Objective]] = {}

    for obj in objectives:
        get_kwargs = getattr(obj, "get_kwargs", None)
        if get_kwargs is None:
            continue
        element = get_kwargs["elt"]

        if element not in objectives_by_element:
            objectives_by_element[element] = []
        objectives_by_element[element].append(obj)
    return objectives_by_element
