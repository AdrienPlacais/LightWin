"""Define allowed values for :class:`.SimulationOutputEvaluator`.

.. note::
    I do not test that every key is in IMPLEMENTED_EVALUATORS anymore. User's
    responsibility.

"""

from lightwin.new_config.key_val_conf_spec import KeyValConfSpec

EVALUATORS_CONFIG = (
    KeyValConfSpec(
        key="beam_calc_post",
        types=(list[str],),
        description=(
            "The names of the evaluators, that must be in "
            ":data:`.IMPLEMENTED_EVALUATORS`."
        ),
        default_value=["mismatch factor at end"],
        is_mandatory=False,
    ),
)
