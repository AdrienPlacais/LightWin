#!/usr/bin/env python3
"""Define a generic compensation workflow."""
import tomllib
from collections.abc import Collection, Sequence
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from my_own_objectives import (
    EnergyPhaseMismatchMoreElements,
    MyObjectiveFactory,
)

from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.config.config_manager import process_config
from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.experimental.new_evaluator.simulation_output.factory import (
    SimulationOutputEvaluatorsFactory,
)
from lightwin.failures.fault_scenario import FaultScenario
from lightwin.ui.workflow_setup import run_simulation
from lightwin.util.pass_beauty import insert_pass_beauty_instructions


def add_beauty_instructions(
    fault_scenarios: Collection[FaultScenario], beam_calculator: BeamCalculator
) -> None:
    """Edit dat file to include beauty instructions.

    To execute after the :func:`.workflow_setup.set_up` function.

    """
    for fault_scenario in fault_scenarios:
        insert_pass_beauty_instructions(fault_scenario, beam_calculator)


def _perform_evaluations(
    accelerators: Sequence[Accelerator],
    evaluator_kw: Collection[dict[str, str | float | bool]] | None = None,
    get_overrides: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Perform ultimate tests.

    To execute after the :func:`.workflow_setup.fix` and
    :func:`.workflow_setup.recompute` functions.

    """
    if evaluator_kw is None:
        with open("lightwin.toml", "rb") as f:
            config = tomllib.load(f)
        evaluator_kw = config["evaluators"]["simulation_output"]
    assert evaluator_kw is not None
    factory = SimulationOutputEvaluatorsFactory(evaluator_kw)
    evaluators = factory.run(
        accelerators,
        solvers_ids=list(accelerators[0].simulation_outputs.keys())[0],
    )
    tests = factory.batch_evaluate(
        evaluators, accelerators, get_overrides=get_overrides
    )
    return tests


def study(new_evaluations: bool = False) -> list[Accelerator]:
    toml_filepath = Path("lightwin.toml")
    toml_keys = {
        "files": "files",
        "plots": "plots_minimal",
        "beam_calculator": "generic_envelope1d",
        # "beam_calculator_post": "generic_tracewin",
        "beam": "beam",
        "wtf": "generic_wtf",
        "design_space": "fit_phi_s_design_space",
        # "wtf": "tiny_wtf",
        # "design_space": "tiny_design_space",
    }
    config = process_config(toml_filepath, toml_keys)
    fault_scenarios = run_simulation(
        config,
        # objective_factory_class=MyObjectiveFactory,
    )

    fs = fault_scenarios[0]
    assert isinstance(fs, FaultScenario)
    accelerators = [fs.ref_acc, fs.fix_acc]
    fix = list(accelerators[1].simulation_outputs.values())[0]

    if new_evaluations:
        # Example
        # linac_only = [x.name for x in fix.elts()[:453]]
        # get_overrides = {"elt": linac_only}

        get_overrides = None
        _perform_evaluations(accelerators, get_overrides=get_overrides)
    return list(accelerators)


if __name__ == "__main__":
    accelerators = study()
    plt.show()
