"""Tests the various :class:`.OptimisationAlgorithm`."""

from typing import Any

import pytest
from tests.pytest_helpers.simulation_output import wrap_approx

import lightwin.config.config_manager as config_manager
from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.beam_calculation.factory import BeamCalculatorsFactory
from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.constants import example_config
from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.failures.fault_scenario import (
    FaultScenario,
    fault_scenario_factory,
)
from lightwin.ui.workflow_setup import set_up_accelerators

params = [
    pytest.param(
        ("downhill_simplex",), marks=pytest.mark.smoke, id="Downhill Simplex"
    ),
    pytest.param(("least_squares",), id="Least Squares"),
]


@pytest.fixture(scope="class", params=params)
def config(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
) -> dict[str, dict[str, Any]]:
    """Set the configuration, common to all solvers."""
    out_folder = tmp_path_factory.mktemp("tmp")
    (optimisation_algorithm,) = request.param

    config_keys = {
        "files": "files",
        "beam_calculator": "generic_envelope1d",
        "beam": "beam",
        "wtf": "generic_wtf",
        "design_space": "generic_design_space",
    }
    override = {
        "files": {
            "project_folder": out_folder,
        },
        "wtf": {
            "optimisation_algorithm": optimisation_algorithm,
        },
    }
    # Remove Downhill Simplex specific kwargs
    if optimisation_algorithm != "downhill_simplex":
        override["wtf"]["optimisation_algorithm_kwargs"] = {}

    my_config = config_manager.process_config(
        example_config, config_keys, warn_mismatch=True, override=override
    )
    return my_config


@pytest.fixture(scope="class")
def solver(config: dict[str, dict[str, Any]]) -> BeamCalculator:
    """Instantiate the solver with the proper parameters."""
    factory = BeamCalculatorsFactory(**config)
    my_solver = factory.run_all()[0]
    return my_solver


@pytest.fixture(scope="class")
def accelerators(
    solver: BeamCalculator,
    config: dict[str, dict[str, Any]],
) -> list[Accelerator]:
    """Create ref linac, linac we will break, compute ref simulation_output."""
    solvers = (solver,)
    accelerators = set_up_accelerators(config, solvers)
    solver.compute(accelerators[0])
    return accelerators


@pytest.fixture(scope="class")
def fault_scenario(
    accelerators: list[Accelerator],
    solver: BeamCalculator,
    config: dict[str, dict[str, Any]],
) -> FaultScenario:
    """Create the fault(s) to fix."""
    factory = fault_scenario_factory
    fault_scenario = factory(
        accelerators, solver, config["wtf"], config["design_space"]
    )[0]
    return fault_scenario


@pytest.fixture(scope="class")
def simulation_outputs(
    solver: BeamCalculator,
    accelerators: list[Accelerator],
    fault_scenario: FaultScenario,
) -> tuple[SimulationOutput, SimulationOutput]:
    """Get ref simulation output, fix fault, compute fix simulation output."""
    ref_simulation_output = list(accelerators[0].simulation_outputs.values())[
        0
    ]
    fault_scenario.fix_all()
    fix_simulation_output = solver.compute(accelerators[1])
    return fix_simulation_output, ref_simulation_output


@pytest.mark.envelope1d
class TestOptimisationAlgorithms:

    def test_w_kin(
        self, simulation_outputs: tuple[SimulationOutput, SimulationOutput]
    ) -> None:
        """Check the beam energy at the exit of the linac."""
        assert wrap_approx("w_kin", *simulation_outputs, abs=1e-3)

    def test_phi_abs(
        self, simulation_outputs: tuple[SimulationOutput, SimulationOutput]
    ) -> None:
        """Check the beam phase at the exit of the linac."""
        assert wrap_approx("phi_abs", *simulation_outputs, abs=1e-2)

    def test_phi_s(
        self, simulation_outputs: tuple[SimulationOutput, SimulationOutput]
    ) -> None:
        """Check the synchronous phase of the cavity 142."""
        assert wrap_approx("phi_s", *simulation_outputs, abs=1e-2, elt="FM142")

    def test_v_cav(
        self, simulation_outputs: tuple[SimulationOutput, SimulationOutput]
    ) -> None:
        """Check the accelerating voltage of the cavity 142."""
        assert wrap_approx(
            "v_cav_mv", *simulation_outputs, abs=1e-3, elt="FM142"
        )
