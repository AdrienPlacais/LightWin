"""Define the function related to the ``strategy`` key of ``wtf``.

In particular, it answers the question:
**Given this set of faults, which compensating cavities will be used?**

.. note::
    In order to add a compensation strategy, you must add it to the
    :data:`STRATEGIES_MAPPING` dict.

"""

from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import Any, Literal

from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.list_of_elements.helper import (
    group_elements_by_lattice,
    is_list_of_list_of_field_maps,
)
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.failures.helper import (
    TIE_POLITICS_T,
    gather,
    nested_containing_desired,
    sort_by_position,
)
from lightwin.util.helper import flatten

cavities_id = Sequence[int] | Sequence[str]
nested_cavities_id = Sequence[Sequence[int]] | Sequence[Sequence[str]]


def failed_and_compensating(
    elts: ListOfElements,
    failed: cavities_id | nested_cavities_id,
    id_nature: Literal["cavity", "element", "name"],
    strategy: STRATEGIES_T,
    compensating_manual: nested_cavities_id | None = None,
    **wtf: Any,
) -> tuple[list[list[FieldMap]], list[list[FieldMap]]]:
    """Determine the compensating cavities for every failure.

    Parameters
    ----------
    elts :
        Contains the failed linac.
    failed :
        Identify the failed cavities.
    id_nature :
        Nature of information stored in ``failed``.
    strategy :
        Compensation strategy.
    compensating_gathered :
        Associates every group of failed cavities in ``failed`` with a group
        of compensating cavities; both must hold a list of list of cavity
        identifier.
    wtf :
        Other keyword arguments passed to the actual strategy function.

    Returns
    -------
    failed_gathered :
        Failed cavities; cavities that will be compensated together are
        gathered.
    compensating_gathered :
        Same size as ``failed_gathered``. Associates every group of failed
        cavities to a group of compensating cavities.

    """
    failed_cavities = elts.take(failed, id_nature=id_nature)
    assert [cavity.can_be_retuned for cavity in flatten(failed_cavities)]
    tunable_cavities = elts.tunable_cavities

    if strategy == "manual":
        assert (
            compensating_manual is not None
        ), f"With {strategy = } you must provide the compensating cavities."
        compensating_cavities = elts.take(
            compensating_manual, id_nature=id_nature
        )
        return manual(failed_cavities, compensating_cavities)

    fun_sort = partial(
        STRATEGIES_MAPPING[strategy],
        elements=tunable_cavities,
        elements_gathered_by_lattice=group_elements_by_lattice(
            tunable_cavities
        ),
        remove_failed=False,
        **wtf,
    )
    failed_gathered, compensating_gathered = gather(
        failed_elements=failed_cavities, fun_sort=fun_sort
    )

    # Manually add correctors
    if strategy == "corrector at exit":
        n_correctors = wtf.get("n_correctors", None)
        assert n_correctors is not None
        compensating_gathered.append(tunable_cavities[-n_correctors:])
        # The last ``n_correctors`` are associated with an empty list of failed
        # cavities, which will require special treatment from the objective
        # factory
        failed_gathered.append([])

    return failed_gathered, compensating_gathered


def k_out_of_n[T](
    elements: Sequence[T],
    failed_elements: Sequence[T],
    *,
    k: int,
    tie_politics: TIE_POLITICS_T = "upstream first",
    shift: int = 0,
    remove_failed: bool = False,
    **kwargs,
) -> list[T]:
    r"""Return ``k`` compensating cavities per failed in ``elts_of_interest``.

    Compensate the :math:`n` failed cavities with :math:`k\times n` closest
    cavities :cite:`saini_assessment_2021,Yee-Rendon2022a`.

    .. note::
        ``T`` can represent a :class:`.Element`, or a list of
        :class:`.Element`. Returned type/data structure will be the same as
        what was given in arguments. This function is hereby also used by
        :func:`l_neighboring_lattices` which gives in lattices.

    Parameters
    ----------
    elements :
        All the tunable elements/lattices/sections.
    failed_elements :
        Failed cavities/lattice.
    k :
        Number of compensating cavity per failure.
    tie_politics :
        When two elements have the same position, will you want to have the
        upstream or the downstream first?
    shift :
        Distance increase for downstream elements (``shift < 0``) or upstream
        elements (``shift > 0``). Used to have a window of compensating
        cavities which is not centered around the failed elements.

    Returns
    -------
        Contains all the altered elements/lattices. The :math:`n` first are
        failed, the :math:`k \times n` following are compensating.

    """
    sorted_by_position = sort_by_position(
        elements,
        failed_elements,
        tie_politics,
        shift,
    )
    n = len(failed_elements)
    altered = sorted_by_position[: n + k * n]
    if remove_failed:
        return altered[n:]
    return altered


def l_neighboring_lattices[T](
    elements_gathered_by_lattice: Sequence[Sequence[T]],
    failed_elements: Sequence[T],
    *,
    l: int,
    tie_politics: TIE_POLITICS_T = "upstream first",
    shift: int = 0,
    remove_failed: bool = False,
    min_number_of_cavities_in_lattice: int = 1,
    **kwargs,
) -> list[T]:
    """Select full lattices neighboring the failed cavities.

    Every fault will be compensated by ``l`` full lattices, direct neighbors of
    the errors :cite:`Bouly2014,Placais2022a`. You must provide ``l``.
    Non-failed cavities in the same lattice as the failure are also used.

    Parameters
    ----------
    elements_by_lattice :
        Tunable elements sorted by lattice.
    failed_elements :
        Failed cavities/lattice.
    l :
        Number of compensating lattice per failure.
    tie_politics :
        When two elements have the same position, will you want to have the
        upstream or the downstream first?
    shift :
        Distance increase for downstream elements (``shift < 0``) or upstream
        elements (``shift > 0``). Used to have a window of compensating
        cavities which is not centered around the failed elements.
    remove_failed :
        To remove the failed lattices from the output.
    min_number_of_cavities_in_lattice :
        If a lattice has less than this number of functional cavities, we
        look for another lattice. This is designed to removed lattices which
        have no cavities. Note that lattices that have some functional cavities
        but not enough will be used for compensation anyway.

    Returns
    -------
        Contains all the altered cavities.

    """
    lattices_with_a_fault = nested_containing_desired(
        elements_gathered_by_lattice, failed_elements
    )

    elements_gathered_by_lattice = [
        x
        for x in elements_gathered_by_lattice
        if len(x) >= min_number_of_cavities_in_lattice
        or x in lattices_with_a_fault
    ]

    compensating_lattices = k_out_of_n(
        elements_gathered_by_lattice,
        lattices_with_a_fault,
        k=l,
        tie_politics=tie_politics,
        shift=shift,
        remove_failed=True,
    )
    for lattice in compensating_lattices:
        if len(lattice) >= min_number_of_cavities_in_lattice:
            continue
        elements_gathered_by_lattice.remove(lattice)

    altered_lattices = k_out_of_n(
        elements_gathered_by_lattice,
        lattices_with_a_fault,
        k=l,
        tie_politics=tie_politics,
        shift=shift,
        remove_failed=False,
    )

    altered_cavities = [x for x in flatten(altered_lattices)]
    if remove_failed:
        altered_cavities = [
            x for x in altered_cavities if x not in failed_elements
        ]

    return altered_cavities


def manual(
    failed_cavities: Sequence[list[FieldMap]],
    compensating_cavities: list[list[FieldMap]] | Any,
) -> tuple[list[list[FieldMap]], list[list[FieldMap]]]:
    """Associate failed with compensating cavities."""
    assert is_list_of_list_of_field_maps(
        failed_cavities
    ), f"{failed_cavities = } is not a nested list of cavities."
    assert is_list_of_list_of_field_maps(
        compensating_cavities
    ), f"{compensating_cavities = } is not a nested list of cavities."
    assert len(failed_cavities) == len(compensating_cavities), (
        f"Mismatch between {len(failed_cavities) = } and "
        f"{len(compensating_cavities) = }"
    )
    return failed_cavities, compensating_cavities


def global_compensation[T](
    elements: Sequence[T],
    failed_elements: Sequence[T],
    *,
    remove_failed: bool = False,
    **kwargs,
) -> list[T]:
    """Give all the cavities of the linac.

    Parameters
    ----------
    elements :
        All the tunable elements.
    failed_elements :
        Failed cavities.

    Returns
    -------
        Contains all the altered elements.

    """
    if not remove_failed:
        return list(elements)
    altered = [x for x in elements if x not in failed_elements]
    return altered


def global_downstream[T](
    elements: Sequence[T],
    failed_elements: Sequence[T],
    *,
    remove_failed: bool = False,
    **kwargs,
) -> list[T]:
    """Give all the cavities of the linac after the first failed cavity.

    Parameters
    ----------
    elements :
        All tunable the elements.
    failed_elements :
        Failed cavities.

    Returns
    -------
        Contains all the altered elements.

    """
    indexes = [elements.index(cavity) for cavity in failed_elements]
    first_index = min(indexes)
    altered = elements[first_index:]
    if not remove_failed:
        return list(altered)
    altered = [x for x in altered if x not in failed_elements]
    return altered


def corrector_at_exit(
    elements: Sequence[cavities_id],
    failed_elements: Sequence[cavities_id],
    *,
    n_compensating: int,
    n_correctors: int,
    tie_politics: TIE_POLITICS_T = "downstream first",
    shift: int = 0,
    remove_failed: bool = False,
    include_correctors: bool = False,
    **kwargs,
) -> list[cavities_id]:
    r"""Return ``k out of n`` cavities, plus additional cavities at exit.

    The idea between this strategy is the following:
    - Use ``n_compensating`` cavities around the failure to shape the beam and
      accelerate it as much as possible.
    - Rephase downstream cavities to keep the beam as intact as possible.
      - ``reference_phase_policy = "phi_s"`` is the best choice to preserve
        longitudinal acceptance along the linac.
    - Give an ultimate energy boost to the beam with the last ``n_correctors``
      cavities.
      - The :class:`.ObjectiveFactory` must set different objectives at the
        linac exit than at the compensation zone(s) exit.

    This method is inspired by Shishlo and Peters who tested it on SNS
    superconducting linac :cite:`Shishlo2022`; they used
    ``n_compensating = 0``. It also showed very promising results on the
    SPIRAL2 superconducting linac :cite:`Placais2024b`.

    Parameters
    ----------
    elements :
        All the tunable elements/lattices/sections.
    failed_elements :
        Failed cavities/lattice.
    n_compensating :
        Number of compensating cavity per failure; this is the ``k`` of the
        ``k out of n`` method.
    n_correctors :
        Number of corrector cavities at the exit of the linac.
    tie_politics :
        When two elements have the same position, will you want to have the
        upstream or the downstream first?
    shift :
        Distance increase for downstream elements (``shift < 0``) or upstream
        elements (``shift > 0``). Used to have a window of compensating
        cavities which is not centered around the failed elements.
    include_correctors :
        If corrector cavities should be included in returned list. If this
        function is called within :func:`.gather`, set it to ``False``. As all
        failed cavities of the linac would require these compensating cavities,
        it would mess up with the failures gathering. Current workaround is to
        add correctors manually after the :func:`.gather` call, in
        :func:`.failed_and_compensating`.

    Returns
    -------
        Contains all the altered elements. The :math:`n` first are failed, the
        :math:`n_\mathrm{compensating} \times n` following are compensating,
        the last :math:`n_\mathrm{correctors}` are correctors.

    """
    altered = k_out_of_n(
        elements=elements,
        failed_elements=failed_elements,
        k=n_compensating,
        tie_politics=tie_politics,
        shift=shift,
        remove_failed=remove_failed,
        **kwargs,
    )
    correctors = elements[-n_correctors:]

    failed_and_corrector = list(set(failed_elements) & set(correctors))
    if len(failed_and_corrector) > 0:
        raise NotImplementedError(
            "Some cavities are failed AND in the last `n_correctors` cavities "
            "of the linac, which is presently not handled.\n"
            f"{failed_and_corrector = }"
        )
    altered_and_corrector = list(set(altered) & set(correctors))
    if len(altered_and_corrector) > 0:
        raise NotImplementedError(
            "Some cavities are compensating AND in the last `n_correctors` "
            "cavities  of the linac, which is presently not handled.\n"
            f"{altered_and_corrector = }"
        )

    if include_correctors:
        altered += correctors
    return altered


#: Defines the compensation strategies, *i.e.* selection of compensating
#: cavities for given failures.
STRATEGIES_MAPPING = {
    "corrector at exit": corrector_at_exit,
    "global": global_compensation,
    "global_downstream": global_downstream,
    "k out of n": k_out_of_n,
    "l neighboring lattices": l_neighboring_lattices,
    "manual": manual,
}
STRATEGIES_T = Literal[
    "corrector at exit",
    "global downstream",
    "global",
    "k out of n",
    "l neighboring lattices",
    "manual",
]
