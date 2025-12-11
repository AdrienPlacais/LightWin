"""Define allowed values for wtf (what to fit).

.. todo::
    Some tests disappeared with the new config method... Checking the correct
    match of compensating manual for example

"""

import logging
from types import NoneType
from typing import Any

from lightwin.config.key_val_conf_spec import KeyValConfSpec
from lightwin.config.table_spec import TableConfSpec
from lightwin.failures.helper import TIE_POLITICS
from lightwin.failures.strategy import AUTOMATIC_STUDY, STRATEGIES_MAPPING
from lightwin.optimisation.algorithms.factory import ALGORITHM_SELECTOR
from lightwin.optimisation.objective.factory import OBJECTIVE_PRESETS
from lightwin.util.typing import ID_NATURE

#: Configuration keys that are common to all strategies.
WTF_COMMON = (
    KeyValConfSpec(
        key="automatic_study",
        types=(str, NoneType),
        description=(
            """Automatically generate the list of failed cavities to avoid
            manually typing all the cavities identifiers in systematic studies.
            """
        ),
        default_value=None,
        allowed_values=AUTOMATIC_STUDY,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="failed",
        types=(list,),
        description=(
            "Identifies list of failed cavities. This is typically a list of "
            "list of cavity identifiers (2D), but it can be a 1D list for "
            "automatic studies and it must be a 3D array if ``strategy`` is "
            "set to ``'manual'``."
        ),
        default_value=[[5]],
    ),
    KeyValConfSpec(
        key="history_kwargs",
        types=(dict,),
        description=("kwargs for the :class:`.OptimizationHistory`."),
        default_value={"folder": None},
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="id_nature",
        types=(str,),
        description=(
            "Indicates if `failed` is name of element(s), index of element(s),"
            "index of cavities. It can also be the index(es) of one or several"
            "section(s), or of one or several lattice(s)."
        ),
        allowed_values=ID_NATURE,
        default_value="element",
    ),
    KeyValConfSpec(
        key="index_offset",
        types=(int,),
        description=(
            """
            Specify whether user-provided cavity indices are 0-based or
            1-based. Set `0` if the first cavity has index 0 (Python-style,
            default). Set `1` if the first cavity has index 1
            (human-friendly). This affects how the `failed` and
            `compensating_manual` lists interpret integer indices.
            """
        ),
        allowed_values=(0, 1),
        default_value=0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="objective_preset",
        types=(str,),
        description="Objectives for the optimisation algorithm.",
        allowed_values=tuple(OBJECTIVE_PRESETS.keys()),
        default_value="EnergyMismatch",
    ),
    KeyValConfSpec(
        key="optimisation_algorithm",
        types=(str,),
        description="Name of optimisation algorithm.",
        allowed_values=tuple(ALGORITHM_SELECTOR.keys()),
        default_value="DownhillSimplex",
    ),
    KeyValConfSpec(
        key="optimisation_algorithm_kwargs",
        types=(dict,),
        description="Keyword arguments passed to the optimisation algorithm.",
        default_value={},
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="strategy",
        types=(str,),
        description="How compensating cavities are selected.",
        allowed_values=tuple(STRATEGIES_MAPPING.keys()),
        default_value="k out of n",
    ),
)

#: Configuration keys for all strategies but ``"manual"``
_WTF_COMMON_NON_MANUAL = (
    KeyValConfSpec(
        key="tie_politics",
        types=(str,),
        description=(
            "How to select the compensating elements when several are "
            "equidistant to the failure."
        ),
        allowed_values=TIE_POLITICS,
        default_value="downstream first",
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="shift",
        types=(int,),
        description=(
            "Distance increase for downstream elements (`shift < 0`) or "
            "upstream elements (`shift > 0`). Used to have a window of "
            "compensating cavities which is not centered around the failed "
            "elements."
        ),
        default_value=0,
        is_mandatory=False,
    ),
)
WTF_K_OUT_OF_N_SPECIFIC = _WTF_COMMON_NON_MANUAL + (
    KeyValConfSpec(
        key="k",
        types=(int,),
        description="Number of compensating cavities per failed cavity.",
        default_value=5,
    ),
)

WTF_K_OUT_OF_N = WTF_COMMON + WTF_K_OUT_OF_N_SPECIFIC

WTF_L_NEIGHBORING_LATTICES_SPECIFIC = _WTF_COMMON_NON_MANUAL + (
    KeyValConfSpec(
        key="l",
        types=(int,),
        description="Number of compensating lattices per failed cavity.",
        default_value=2,
    ),
    KeyValConfSpec(
        key="min_number_of_cavities_in_lattice",
        types=(int,),
        description=(
            "Minimum number of compensating cavities in the lattice; when a "
            "lattice does not reach this number, we use it anyway for "
            "compensation, but we also take another lattice. Designed to "
            "remove the lattices that do not have any cavity."
        ),
        default_value=1,
        is_mandatory=False,
    ),
)
WTF_L_NEIGHBORING_LATTICES = WTF_COMMON + WTF_L_NEIGHBORING_LATTICES_SPECIFIC

WTF_CORRECTOR_AT_EXIT_SPECIFC = _WTF_COMMON_NON_MANUAL + (
    KeyValConfSpec(
        key="n_compensating",
        types=(int,),
        description=(
            "Number of compensating cavities around every failure. They are "
            "used to shape the beam without retrieving nominal energy, so that"
            " it can propagate up to the ``correctors`` without losses. "
            "Currently, you must set at least 1 compensating cavity to avoid "
            "errors."
        ),
        default_value=1,
    ),
    KeyValConfSpec(
        key="n_correctors",
        types=(int,),
        description=(
            "Number of compensating cavities at the exit of the linac. They "
            "are used to retrieve nominal energy. Not affected by the "
            "``shift`` keyword."
        ),
        default_value=2,
    ),
)
WTF_CORRECTOR_AT_EXIT = WTF_COMMON + WTF_CORRECTOR_AT_EXIT_SPECIFC

WTF_MANUAL_SPECIFIC = (
    KeyValConfSpec(
        key="failed",
        types=(list,),
        description=(
            "Index/name of failed cavities. For manual strategy, it must be a "
            "3D list."
        ),
        default_value=[[[5]]],
        overrides_previously_defined=True,
    ),
    KeyValConfSpec(
        key="compensating_manual",
        types=(list,),
        description=(
            "Index/name of compensating cavities cavities. Must be a 3D list, "
            "which two first level lengths must match the ones of `failed`."
        ),
        default_value=[[[3, 4, 6, 7]]],
    ),
)
WTF_MANUAL = WTF_COMMON + WTF_MANUAL_SPECIFIC


def apply_index_offset(
    self: TableConfSpec, toml_table: dict[str, Any], **kwargs
) -> None:
    """Apply the ``index_offset`` key."""
    index_offset = toml_table.get("index_offset")
    if index_offset is None or index_offset == 0:
        return

    assert isinstance(index_offset, int)
    id_nature = toml_table.get("id_nature")
    valid_id_nature = ("cavity", "element", "lattice", "section")
    if id_nature not in valid_id_nature:
        logging.warning(
            f"The configuration key {index_offset = } was disregarded because "
            f"it makes no sense with {id_nature = }. Index offsetting is "
            f"implemented for {valid_id_nature}."
        )
        return

    applicable = ("failed", "compensating_manual")
    for key in applicable:
        indexes = toml_table.get(key, None)
        if indexes is None:
            continue

        toml_table[key] = _apply_offset_to_nested_list(indexes, index_offset)


def _apply_offset_to_nested_list(x: int | list, offset: int) -> int | list:
    """Recursively subtract offset from integers in nested lists."""
    if isinstance(x, int):
        return x - offset
    return [_apply_offset_to_nested_list(elem, offset) for elem in x]


COMMON_MONKEY_PATCHES = {"_pre_treat": apply_index_offset}


WTF_CONFIGS = {
    "corrector at exit": WTF_CORRECTOR_AT_EXIT,
    "k out of n": WTF_K_OUT_OF_N,
    "l neighboring lattices": WTF_L_NEIGHBORING_LATTICES,
    "manual": WTF_MANUAL,
}
WTF_MONKEY_PATCHES = {
    key: COMMON_MONKEY_PATCHES
    for key in (
        "corrector at exit",
        "k out of n",
        "l neighboring lattices",
        "manual",
    )
}
