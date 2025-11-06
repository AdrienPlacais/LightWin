"""Test the :class:`.Envelope1D` solver.

.. todo::
    Test emittance, envelopes, different cavity phase definitions.

"""

from typing import Any
from unittest.mock import call, patch

import numpy as np
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
from lightwin.util.solvers import solve_scalar_equation_brent

leapfrog_marker = pytest.mark.xfail(
    condition=True,
    reason="leapfrog method has not been updated since 0.0.0.0.1 or so",
)

# Arguments are:
# method, flag_cython, reference_phase_policy, n_steps_per_cell
params = [
    pytest.param(
        ("RK4", False, "phi_0_rel", 40),
        marks=pytest.mark.smoke,
        id="1D RK4 relative phase",
    ),
    pytest.param(
        ("RK4", False, "phi_0_abs", 40),
        marks=pytest.mark.smoke,
        id="1D RK4 absolute phase",
    ),
    pytest.param(
        ("RK4", False, "phi_s", 40),
        marks=pytest.mark.smoke,
        id="1D RK4 synchronous phase",
    ),
    pytest.param(
        ("RK4", False, "as_in_original_dat", 40),
        marks=pytest.mark.smoke,
        id="1D RK4 different phases, matching original ``DAT``",
    ),
    pytest.param(
        ("RK4", True, "phi_0_rel", 40),
        marks=pytest.mark.cython,
        id="1D RK4 relative phase Cython",
    ),
    pytest.param(
        ("RK4", True, "phi_0_abs", 40),
        marks=pytest.mark.cython,
        id="1D RK4 absolute phase Cython",
    ),
    pytest.param(
        ("RK4", True, "phi_s", 40),
        marks=pytest.mark.cython,
        id="1D RK4 synchronous phase Cython",
    ),
    pytest.param(
        ("RK4", True, "as_in_original_dat", 40),
        marks=pytest.mark.cython,
        id="1D RK4 different phases, matching original ``DAT`` Cython",
    ),
    pytest.param(
        ("leapfrog", False, "phi_0_rel", 60),
        marks=leapfrog_marker,
        id="1D leapfrog relative phase",
    ),
    pytest.param(
        ("leapfrog", True, "phi_0_rel", 60),
        marks=(leapfrog_marker, pytest.mark.cython),
        id="1D leapfrog relative phase Cython",
    ),
]


@pytest.fixture(scope="class")
def solver(config: dict[str, dict[str, Any]]) -> BeamCalculator:
    """Instantiate the solver with the proper parameters."""
    factory = BeamCalculatorsFactory(**config)
    my_solver = factory.run_all()[0]
    return my_solver


@pytest.fixture(scope="class", params=params)
def config(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
) -> dict[str, dict[str, Any]]:
    """Set the configuration, common to all solvers."""
    out_folder = tmp_path_factory.mktemp("tmp")
    method, flag_cython, reference_phase_policy, n_steps_per_cell = (
        request.param
    )

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
            "reference_phase_policy": reference_phase_policy,
            "n_steps_per_cell": n_steps_per_cell,
        },
    }
    my_config = config_manager.process_config(
        example_config, config_keys, warn_mismatch=True, override=override
    )
    return my_config


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
    """Gather all the tests in a single class.

    Note that, in absence of failure, the ``reference_phase_policy`` should not
    have any influence.

    """

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

    def test_phase_acceptance(
        self, simulation_output: SimulationOutput
    ) -> None:
        """Verify that phase acceptance is correct."""
        assert wrap_approx(
            "acceptance_phi", simulation_output, abs=5, elt="FM142"
        )

    def test_acceptance_energy(
        self, simulation_output: SimulationOutput
    ) -> None:
        """Verify that energy acceptance is correct."""
        assert wrap_approx(
            "acceptance_energy", simulation_output, abs=1e-1, elt="FM142"
        )


def test_inverted_bounds_warning() -> None:
    """Tests that the method accepts inverted bounds with a warning and still finds the roots."""

    def example_func(x: float, a: float) -> float:
        return x - a

    param_value = 1
    with patch("logging.warning") as mock_warning:
        result = solve_scalar_equation_brent(example_func, param_value, (5, 0))
        assert np.allclose(result, np.array(1.0))
        mock_warning.assert_any_call(
            "The range (5, 0) is inverted. It has been corrected to (0, 5)."
        )


def test_no_sign_change_warning() -> None:
    """Tests that lack of sign change in Brent's method triggers a warning and returns NaN."""

    def example_func(x: float, a: float) -> float:
        return x**2 + a

    param_values = 1
    with patch("logging.warning") as mock_warning:
        result = solve_scalar_equation_brent(
            example_func, param_values, (-5, 5)
        )
        assert np.isnan(result)
        calls = [str(call.args[0]) for call in mock_warning.call_args_list]
        assert any("have the same sign" in msg for msg in calls)


@pytest.mark.envelope1d
def test_deprecated_flag_phi_abs_false(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """Check that the ``flag_phi_abs`` is considered, but warning is raised."""
    out_folder = tmp_path_factory.mktemp("tmp")
    config_keys = {
        "files": "files",
        "beam_calculator": "generic_envelope1d",
        "beam": "beam",
    }
    override = {
        "files": {"project_folder": out_folder},
        "beam_calculator": {
            "reference_phase_policy": "phi_0_abs",
            "flag_phi_abs": False,
        },
    }
    calls = [
        call(
            "Overriding ``reference_phase_policy`` following (deprecated) "
            "flag_phi_abs = False. reference_phase_policy phi_0_abs -> "
            "phi_0_rel"
        ),
        call(
            "The ``flag_phi_abs`` option is deprecated, prefer using the "
            "``reference_phase_policy``.\nflag_phi_abs=False -> "
            "reference_phase_policy='phi_0_rel'\nflag_phi_abs=True -> "
            "reference_phase_policy='phi_0_abs'"
        ),
    ]
    with patch("logging.warning") as mock_warning:
        my_config = config_manager.process_config(
            example_config, config_keys, override=override
        )
        mock_warning.assert_has_calls(calls)
        assert (
            my_config["beam_calculator"]["reference_phase_policy"]
            == "phi_0_rel"
        )


@pytest.mark.envelope1d
def test_deprecated_flag_phi_abs_true(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """Check that the ``flag_phi_abs`` is considered, but warning is raised."""
    out_folder = tmp_path_factory.mktemp("tmp")
    config_keys = {
        "files": "files",
        "beam_calculator": "generic_envelope1d",
        "beam": "beam",
    }
    override = {
        "files": {"project_folder": out_folder},
        "beam_calculator": {
            "reference_phase_policy": "phi_s",
            "flag_phi_abs": True,
        },
    }
    calls = [
        call(
            "Overriding ``reference_phase_policy`` following (deprecated) "
            "flag_phi_abs = True. reference_phase_policy phi_s -> "
            "phi_0_abs"
        ),
        call(
            "The ``flag_phi_abs`` option is deprecated, prefer using the "
            "``reference_phase_policy``.\nflag_phi_abs=False -> "
            "reference_phase_policy='phi_0_rel'\nflag_phi_abs=True -> "
            "reference_phase_policy='phi_0_abs'"
        ),
    ]
    with patch("logging.warning") as mock_warning:
        my_config = config_manager.process_config(
            example_config, config_keys, override=override
        )
        mock_warning.assert_has_calls(calls)
        assert (
            my_config["beam_calculator"]["reference_phase_policy"]
            == "phi_0_abs"
        )
