"""Test that all the :class:`.DesignSpace` have working implementation.

As for now, we keep a tiny design space centered around solutions known to
work. Hence, we do not check if the design space are adapted to the problem
under study.

.. todo::
    Set ``constraints.csv`` to also study design spaces with constraints.

"""

from typing import Any

import pytest
from tests.pytest_helpers.simulation_output import wrap_approx

import lightwin.config_manager
from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.beam_calculation.factory import BeamCalculatorsFactory
from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.constants import example_config
from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.core.accelerator.factory import WithFaults
from lightwin.failures.fault_scenario import (
    FaultScenario,
    fault_scenario_factory,
)

params = [
    pytest.param(
        ("abs_phase_amplitude",),
        marks=pytest.mark.smoke,
        id="vars: phi_0_abs and k_e",
    ),
    pytest.param(
        ("rel_phase_amplitude",),
        marks=pytest.mark.smoke,
        id="vars: phi_0_rel and k_e",
    ),
    pytest.param(
        ("sync_phase_amplitude",),
        marks=pytest.mark.smoke,
        id="vars: phi_s and k_e",
    ),
    pytest.param(
        ("abs_phase_amplitude_with_constrained_sync_phase",),
        marks=pytest.mark.smoke,
        id="vars: phi_0_abs and k_e; constr: phi_s",
    ),
    pytest.param(
        ("rel_phase_amplitude_with_constrained_sync_phase",),
        marks=pytest.mark.smoke,
        id="vars: phi_0_rel and k_e; constr: phi_s",
    ),
]


@pytest.fixture(scope="class", params=params)
def config(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
) -> dict[str, dict[str, Any]]:
    """Set the configuration."""
    out_folder = tmp_path_factory.mktemp("tmp")
    (design_space_preset,) = request.param

    config_keys = {
        "files": "files",
        "beam_calculator": "generic_envelope1d",
        "beam": "beam",
        "wtf": "generic_wtf",
        "design_space": "tiny_design_space",
    }
    override = {
        "files": {
            "project_folder": out_folder,
        },
        "design_space": {
            "design_space_preset": design_space_preset,
        },
    }
    my_config = lightwin.config_manager.process_config(
        example_config,
        config_keys,
        warn_mismatch=True,
        override=override,
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
    accelerator_factory = WithFaults(beam_calculators=solvers, **config)
    accelerators = accelerator_factory.run_all()
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
class TestDesignSpaceImplementation:

    def test_w_kin(
        self, simulation_outputs: tuple[SimulationOutput, SimulationOutput]
    ) -> None:
        """Check the beam energy at the exit of the linac."""
        assert wrap_approx("w_kin", *simulation_outputs)

    def test_phi_abs(
        self, simulation_outputs: tuple[SimulationOutput, SimulationOutput]
    ) -> None:
        """Check the beam phase at the exit of the linac."""
        assert wrap_approx("phi_abs", *simulation_outputs)

    def test_phi_s(
        self, simulation_outputs: tuple[SimulationOutput, SimulationOutput]
    ) -> None:
        """Check the synchronous phase of the cavity 142."""
        assert wrap_approx("phi_s", *simulation_outputs, abs=1e-2, elt="FM142")

    def test_v_cav(
        self, simulation_outputs: tuple[SimulationOutput, SimulationOutput]
    ) -> None:
        """Check the accelerating voltage of the cavity 142."""
        assert wrap_approx("v_cav_mv", *simulation_outputs, elt="FM142")
