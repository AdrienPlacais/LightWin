"""Define allowed values for :class:`.SimulationOutputEvaluator`.

.. note::
    I do not test that every key is in IMPLEMENTED_EVALUATORS anymore. User's
    responsibility.

"""

from lightwin.config.key_val_conf_spec import KeyValConfSpec

EVALUATORS_CONFIG = (
    KeyValConfSpec(
        key="beam_calc_post",
        types=(list,),
        description="The names of the evaluators.",
        default_value=["mismatch factor at end"],
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="simulation_output",
        types=(list,),
        description=(
            "Keyword arguments for the :class:`.SimulationOutputEvaluator`."
        ),
        default_value=[
            {
                "name": "LongitudinalEmittance",
                "max_percentage_rel_increase": 0.005,
            }
        ],
        is_mandatory=False,
    ),
)
