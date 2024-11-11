#!/usr/bin/env python3
"""Define a generic compensation workflow."""
import tomllib
from collections.abc import Collection, Sequence
from pathlib import Path

import pandas as pd
from my_own_objectives import MyObjectiveFactory

from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.config_manager import process_config
from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.experimental.new_evaluator.simulation_output.factory import (
    SimulationOutputEvaluatorsFactory,
)
from lightwin.experimental.plotter.pd_plotter import PandasPlotter
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


def _perform_evaluations_new_implementation(
    accelerators: Sequence[Accelerator],
    beam_calculators_ids: Sequence[str],
    evaluator_kw: Collection[dict[str, str | float | bool]] | None = None,
) -> pd.DataFrame:
    """Post-treat, with new implementation. Still not fully implemented.

    To execute after the :func:`.workflow_setup.fix` and
    :func:`.workflow_setup.recompute` functions.

    """
    if evaluator_kw is None:
        with open("lightwin.toml", "rb") as f:
            config = tomllib.load(f)
        evaluator_kw = config["evaluators"]["simulation_output"]
    assert evaluator_kw is not None
    factory = SimulationOutputEvaluatorsFactory(
        evaluator_kw, plotter=PandasPlotter()
    )
    evaluators = factory.run(accelerators, beam_calculators_ids[0])
    tests = factory.batch_evaluate(
        evaluators, accelerators, beam_calculators_ids[0]
    )
    return tests


if __name__ == "__main__":
    toml_filepath = Path("lightwin.toml")
    toml_keys = {
        "files": "files",
        "plots": "plots_minimal",
        "beam_calculator": "generic_envelope1d",
        "beam_calculator_post": "generic_tracewin",
        "beam": "beam",
        "wtf": "generic_wtf",
        # "design_space": "fit_phi_s_design_space",
        "design_space": "tiny_design_space",
    }
    NEW_EVALUATIONS = True
    BEAUTY_PASS = False
    config = process_config(toml_filepath, toml_keys)
    fault_scenarios = run_simulation(
        config,
        # objective_factory_class=MyObjectiveFactory
    )
