#!/usr/bin/env python3
"""Define a generic compensation workflow."""
from pathlib import Path
from typing import Any

from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.beam_calculation.factory import BeamCalculatorsFactory
from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.config import config_manager
from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.core.accelerator.factory import NoFault


def _set_up_solvers(
    config: dict[str, Any]
) -> tuple[BeamCalculator, list[str]]:
    """Create the beam calculators."""
    factory = BeamCalculatorsFactory(**config)
    beam_calculators = factory.run_all()
    beam_calculators_id = factory.beam_calculators_id
    return beam_calculators[0], beam_calculators_id


def _set_up_accelerators(
    config: dict[str, Any],
    beam_calculator: BeamCalculator,
) -> Accelerator:
    """Create the accelerators."""
    factory = NoFault(beam_calculators=beam_calculator, **config)
    accelerator = factory.run()
    return accelerator


def set_up(
    config: dict[str, Any],
) -> tuple[
    BeamCalculator,
    Accelerator,
]:
    """Set up everything."""
    beam_calculator, _ = _set_up_solvers(config)
    accelerator = _set_up_accelerators(config, beam_calculator)
    return beam_calculator, accelerator


def main(
    config: dict[str, dict[str, Any]],
) -> tuple[SimulationOutput, Accelerator]:
    """Set up the various faults and fix it."""
    beam_calculator, accelerator = set_up(config)
    simulation_output = beam_calculator.compute(accelerator)
    return simulation_output, accelerator


if __name__ == "__main__":
    toml_filepath = Path("test_instructions.toml")
    toml_keys = {
        "files": "files",
        # "plots": "plots_minimal",
        "beam_calculator": "generic_envelope1d",
        "beam": "beam",
    }
    override = {
        "files": {
            "dat_file": "superpose_map.dat",
        },
        # "beam_calculator": {"n_steps_per_cell": 40},
    }
    config = config_manager.process_config(
        toml_filepath, toml_keys, override=override
    )
    simulation_output, accelerator = main(config)
    x = simulation_output.transfer_matrix.individual
    y = simulation_output.transfer_matrix.cumulated
