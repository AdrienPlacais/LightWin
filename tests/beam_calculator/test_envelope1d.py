"""Test the :class:`.Envelope1D` solver.

.. todo::
    Test emittance, envelopes, different cavity phase definitions.

"""

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
from lightwin.core.accelerator.factory import NoFault
from lightwin.beam_calculation.envelope_1d.simulation_output_factory import (
    compute_phi_2,
    solve_scalar_equation_brent, 
)
import numpy as np
from unittest.mock import patch


leapfrog_marker = pytest.mark.xfail(
    condition=True,
    reason="leapfrog method has not been updated since 0.0.0.0.1 or so",
)

params = [
    pytest.param(
        ("RK4", False, False, 40),
        marks=pytest.mark.smoke,
        id="1D RK4 relative phase",
    ),
    pytest.param(
        ("RK4", False, True, 40),
        marks=pytest.mark.smoke,
        id="1D RK4 absolute phase",
    ),
    pytest.param(
        ("RK4", True, False, 40),
        marks=pytest.mark.cython,
        id="1D RK4 relative phase Cython",
    ),
    pytest.param(
        ("leapfrog", False, False, 60),
        marks=leapfrog_marker,
        id="1D leapfrog relative phase",
    ),
    pytest.param(
        ("leapfrog", True, False, 60),
        marks=(leapfrog_marker, pytest.mark.cython),
        id="1D leapfrog relative phase Cython",
    ),
]


@pytest.fixture(scope="class", params=params)
def config(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
) -> dict[str, dict[str, Any]]:
    """Set the configuration, common to all solvers."""
    out_folder = tmp_path_factory.mktemp("tmp")
    method, flag_cython, flag_phi_abs, n_steps_per_cell = request.param

    config_keys = {
        "files": "files",
        "beam_calculator": "generic_envelope1d",
        "beam": "beam",
    }
    override = {
        "files": {
            "project_folder": out_folder,
        },
        "beam_calculator": {
            "tool": "Envelope1D",
            "method": method,
            "flag_cython": flag_cython,
            "flag_phi_abs": flag_phi_abs,
            "n_steps_per_cell": n_steps_per_cell,
        },
    }
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
def accelerator(
    solver: BeamCalculator,
    config: dict[str, dict[str, Any]],
) -> Accelerator:
    """Create an example linac."""
    accelerator_factory = NoFault(beam_calculators=solver, **config)
    accelerator = accelerator_factory.run()
    return accelerator


@pytest.fixture(scope="class")
def simulation_output(
    solver: BeamCalculator,
    accelerator: Accelerator,
) -> SimulationOutput:
    """Init and use a solver to propagate beam in an example accelerator."""
    my_simulation_output = solver.compute(accelerator)
    return my_simulation_output


@pytest.mark.envelope1d
class TestSolver1D:
    """Gather all the tests in a single class."""

    def test_w_kin(self, simulation_output: SimulationOutput) -> None:
        """Check the beam energy at the exit of the linac."""
        assert wrap_approx("w_kin", simulation_output)

    def test_phi_abs(self, simulation_output: SimulationOutput) -> None:
        """Check the beam phase at the exit of the linac."""
        assert wrap_approx("phi_abs", simulation_output)

    def test_phi_s(self, simulation_output: SimulationOutput) -> None:
        """Check the synchronous phase of the cavity 142."""
        assert wrap_approx("phi_s", simulation_output, abs=1e-2, elt="FM142")

    def test_v_cav(self, simulation_output: SimulationOutput) -> None:
        """Check the accelerating voltage of the cavity 142."""
        assert wrap_approx(
            "v_cav_mv", simulation_output, abs=1e-3, elt="FM142"
        )

    def test_r_zdelta(self, simulation_output: SimulationOutput) -> None:
        """Verify that longitudinal transfer matrix is correct."""
        assert wrap_approx("r_zdelta", simulation_output, abs=5e-3)

    def test_phase_acceptance(self, simulation_output: SimulationOutput) -> None:
        """Verify that phase acceptance is correct."""
        assert wrap_approx("phi_acceptance", simulation_output, abs=5, elt="FM142")

    def test_energy_acceptance(self, simulation_output: SimulationOutput) -> None:
        """Verify that energy acceptance is correct."""
        assert wrap_approx("energy_acceptance", simulation_output, abs=1e-1, elt="FM142")

def test_compute_phi_2() -> None:
    """Test the compute_phi_2 function with various inputs."""
    phi_2 = -0.5
    phi_s = 1.0
    result = compute_phi_2(phi_2, phi_s)
    expected = (np.sin(phi_2) - phi_2 * np.cos(phi_s)) + (np.sin(phi_s) - phi_s * np.cos(phi_s))
    assert np.isclose(result, expected)


@patch("lightwin.beam_calculation.envelope_1d.simulation_output_factory.brentq")
def test_solve_scalar_equation_brent_mocked(mock_brentq):
    """Test the scalar equation solver using a mocked brentq function."""
    mock_brentq.side_effect = lambda f, a, b: -0.8

    def mock_func(x, param):
        return x + param - np.pi

    params = np.array([4.0, 4.2, 4.4])

    result = solve_scalar_equation_brent(mock_func, params, (-np.pi, 0))

    assert np.allclose(result, [-0.8, -0.8, -0.8])
    assert mock_brentq.call_count == 3

def test_solve_scalar_equation_brent_no_sign_change():
    """Test the scalar equation when the change of sign condition is not respected"""
    def mock_func(x, param):
        return x + param + 10 

    params = np.array([1.0, 2.0])
    result = solve_scalar_equation_brent(mock_func, params, (-np.pi, 0))

    assert np.isnan(result).all()


