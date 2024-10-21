"""Define allowed values for wtf (what to fit).

.. todo::
    Some tests disappeared with the new config method... Checking the correct
    match of compensating manual for example

"""

from typing import Any

from lightwin.failures.strategy import COMPENSATING_SELECTOR
from lightwin.new_config.key_val_conf_spec import KeyValConfSpec
from lightwin.optimisation.algorithms.factory import ALGORITHM_SELECTOR
from lightwin.optimisation.objective.factory import OBJECTIVE_PRESETS

_WTF_BASE = (
    KeyValConfSpec(
        key="failed",
        types=(list,),
        description=(
            "Index/name of failed cavities. Must be a list[list[int]] or "
            "list[list[str]]."
        ),
        default_value=[[5]],
    ),
    KeyValConfSpec(
        key="id_nature",
        types=(str,),
        description=(
            "Indicates if failed is element index/cavity index/name, "
            "``element`` or ``cavity`` or ``name``."
        ),
        allowed_values=("element", "cavity", "name"),
        default_value="element",
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
        allowed_values=tuple(COMPENSATING_SELECTOR.keys()),
        default_value="k out of n",
    ),
)

_WTF_BASE_AUTOMATIC = _WTF_BASE + (
    KeyValConfSpec(
        key="tie_politics",
        types=(str,),
        description=(
            "How to select the compensating elements when several are "
            "equidistant to the failure."
        ),
        allowed_values=("upstream_first", "downstream_first"),
        default_value="downstream_first",
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="shift",
        types=(int,),
        description=(
            "Distance increase for downstream elements (``shift < 0``) or "
            "upstream elements (``shift > 0``). Used to have a window of "
            "compensating cavities which is not centered around the failed "
            "elements."
        ),
        default_value=0,
        is_mandatory=False,
    ),
)

WTF_K_OUT_OF_N = _WTF_BASE_AUTOMATIC + (
    KeyValConfSpec(
        key="k",
        types=(int,),
        description="Number of compensating cavities per failed cavity.",
        default_value=5,
    ),
)

K_OUT_OF_N_MONKEY_PATCHES: dict[str, Any] = {}

WTF_L_NEIGHBORING_LATTICES = _WTF_BASE_AUTOMATIC + (
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
L_NEIGHBORING_LATTICES_MONKEY_PATCHES: dict[str, Any] = {}

WTF_MANUAL = _WTF_BASE + (
    KeyValConfSpec(
        key="failed",
        types=(list,),
        description=(
            "Index/name of failed cavities. Must be a list[list[list[int]]] or"
            " list[list[list[str]]]."
        ),
        default_value=[[[5]]],
        overrides_previously_defined=True,
    ),
    KeyValConfSpec(
        key="compensating_manual",
        types=(list,),
        description=(
            "Index/name of compensating cavities cavities. Must be a "
            "list[list[list[int]]] or list[list[list[str]]]. The number of "
            "FaultScenarios (length of most outer list) must match ``failed``."
            " The number of groups of compensating cavities (second level) "
            "must match ``failed``."
        ),
        default_value=[[[3, 4, 6, 7]]],
    ),
)

MANUAL_MONKEY_PATCHES: dict[str, Any] = {}

WTF_CONFIGS = {
    "k out of n": WTF_K_OUT_OF_N,
    "l neighboring lattices": WTF_L_NEIGHBORING_LATTICES,
    "manual": WTF_MANUAL,
}
WTF_MONKEY_PATCHES = {
    "k out of n": K_OUT_OF_N_MONKEY_PATCHES,
    "l neighboring lattices": L_NEIGHBORING_LATTICES_MONKEY_PATCHES,
    "manual": MANUAL_MONKEY_PATCHES,
}
