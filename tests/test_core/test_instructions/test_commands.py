from pathlib import Path
from typing import Any

import numpy as np
import pytest

import lightwin.config_manager
from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.beam_calculation.factory import BeamCalculatorsFactory
from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.core.accelerator.factory import NoFault

all_expected = {
    ("repeat_ele.dat", "generic_envelope3d"): np.array(
        # fmt: off
        [
            [+8.756510e-01, +1.050080e-01, +0.000000e+00, +0.000000e+00, +0.000000e+00, +0.000000e+00],
            [-2.221121e+00, +8.756510e-01, +0.000000e+00, +0.000000e+00, +0.000000e+00, +0.000000e+00],
            [+0.000000e+00, +0.000000e+00, +1.129680e+00, +1.151298e-01, +0.000000e+00, +0.000000e+00],
            [+0.000000e+00, +0.000000e+00, +2.398841e+00, +1.129680e+00, +0.000000e+00, +0.000000e+00],
            [+0.000000e+00, +0.000000e+00, +0.000000e+00, +0.000000e+00, +1.000000e+00, +1.054563e-01],
            [+0.000000e+00, +0.000000e+00, +0.000000e+00, +0.000000e+00, +0.000000e+00, +1.000000e+00]
        ]
    ),
    ("bigger_repeat_ele.dat", "generic_envelope3d"): np.array(
        # fmt: off
        [
            [+6.632069e-01, +2.870471e-01, +0.000000e+00, +0.000000e+00, +0.000000e+00, +0.000000e+00],
            [-5.374628e-01, +1.275202e+00, +0.000000e+00, +0.000000e+00, +0.000000e+00, +0.000000e+00],
            [+0.000000e+00, +0.000000e+00, +1.221456e+00, +2.312222e-01, +0.000000e+00, +0.000000e+00],
            [+0.000000e+00, +0.000000e+00, -5.374628e-01, +7.169532e-01, +0.000000e+00, +0.000000e+00],
            [+0.000000e+00, +0.000000e+00, +0.000000e+00, +0.000000e+00, +1.000000e+00, +3.836693e+01],
            [+0.000000e+00, +0.000000e+00, +0.000000e+00, +0.000000e+00, +0.000000e+00, +1.000000e+00]
        ]
    ),
    ("set_sync_phase.dat", "generic_envelope3d"): np.array(
        # fmt: off
        [
            [-2.050881e+00, +5.376586e+00, +0.000000e+00, +0.000000e+00, +0.000000e+00, +0.000000e+00],
            [-1.080199e+00, +2.353456e+00, +0.000000e+00, +0.000000e+00, +0.000000e+00, +0.000000e+00],
            [+0.000000e+00, +0.000000e+00, -3.225156e-01, +1.779094e+00, +0.000000e+00, +0.000000e+00],
            [+0.000000e+00, +0.000000e+00, -6.706392e-01, +6.573501e-01, +0.000000e+00, +0.000000e+00],
            [+0.000000e+00, +0.000000e+00, +0.000000e+00, +0.000000e+00, +2.474433e-01, +1.669207e+00],
            [+0.000000e+00, +0.000000e+00, +0.000000e+00, +0.000000e+00, -5.952788e-01, -5.059394e-02]
        ]
    ),
}

DATA_DIR = Path("data", "test_instructions")


@pytest.fixture
def expected(request):
    dat_file = request.node.funcargs["dat_file"]
    beam_calculator_key = request.node.funcargs["beam_calculator_key"]
    return all_expected.get((dat_file, beam_calculator_key), None)


@pytest.fixture
def config(
    request, tmp_path_factory: pytest.TempPathFactory
) -> dict[str, dict[str, Any]]:
    """Set the configuration, common to all solvers."""
    dat_file = request.node.funcargs["dat_file"]
    beam_calculator_key = request.node.funcargs["beam_calculator_key"]
    out_folder = tmp_path_factory.mktemp("tmp")

    config_path = DATA_DIR / "test_instructions.toml"
    config_keys = {
        "files": "files",
        "beam_calculator": beam_calculator_key,
        "beam": "beam",
    }
    override = {
        "files": {
            "project_folder": out_folder,
            "dat_file": dat_file,
        },
    }
    my_config = lightwin.config_manager.process_config(
        config_path, config_keys, warn_mismatch=True, override=override
    )
    return my_config


@pytest.fixture
def solver(config: dict[str, dict[str, Any]]) -> BeamCalculator:
    """Instantiate the solver with the proper parameters."""
    factory = BeamCalculatorsFactory(
        beam_calculator=config["beam_calculator"],
        files=config["files"],
    )
    my_solver = factory.run_all()[0]
    return my_solver


@pytest.fixture
def accelerator(
    solver: BeamCalculator, config: dict[str, dict[str, Any]]
) -> Accelerator:
    """Create an example linac."""
    accelerator_factory = NoFault(beam_calculator=solver, **config["files"])
    accelerator = accelerator_factory.run()
    return accelerator


@pytest.fixture
def simulation_output(
    solver: BeamCalculator, accelerator: Accelerator
) -> SimulationOutput:
    """Init and use a solver to propagate beam in an example accelerator."""
    my_simulation_output = solver.compute(accelerator)
    return my_simulation_output


@pytest.mark.implementation
@pytest.mark.parametrize(
    "dat_file, beam_calculator_key",
    [
        ("repeat_ele.dat", "generic_envelope3d"),
        ("bigger_repeat_ele.dat", "generic_envelope3d"),
        ("set_sync_phase.dat", "generic_envelope3d"),
    ],
)
def test_transfer_matrix(
    dat_file: str | Path,
    beam_calculator_key: str,
    expected: np.ndarray,
    simulation_output: SimulationOutput,
) -> None:
    """Verify that the final transfer matrix is correct."""
    transfer_matrix = simulation_output.transfer_matrix
    assert transfer_matrix is not None
    returned = transfer_matrix.cumulated[-1]

    assert np.allclose(
        expected, returned, atol=1e-2
    ), f"{expected = }, but {returned = }"
