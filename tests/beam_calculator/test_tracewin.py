"""Test the :class:`.TraceWin` solver.

.. todo::
    Fix :class:`.TransferMatrix` for this solver, and reintegrate the transfer
    matrix tests.

.. todo::
    Test emittance, envelopes, different cavity phase definitions.

"""

from typing import Any
from unittest.mock import call, patch

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

params = [
    pytest.param((0,), id="TraceWin envelope"),
    pytest.param((1,), marks=pytest.mark.slow, id="TraceWin multiparticle"),
]


@pytest.fixture(scope="class", params=params)
def config(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
) -> dict[str, dict[str, Any]]:
    """Set the configuration, common to all solvers."""
    out_folder = tmp_path_factory.mktemp("tmp")
    (partran,) = request.param

    config_keys = {
        "files": "files",
        "beam_calculator": "generic_tracewin",
        "beam": "beam",
    }
    override = {
        "files": {
            "project_folder": out_folder,
        },
        "beam_calculator": {
            "partran": partran,
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


@pytest.mark.tracewin
class TestSolver3D:
    """Gater all the tests in a single class.

    Note that, in absence of failure, the ``reference_phase_policy`` should not
    have any influence.

    """

    def test_w_kin(self, simulation_output: SimulationOutput) -> None:
        """Check the beam energy at the exit of the linac."""
        assert wrap_approx("w_kin", simulation_output, abs=5e-3)

    def test_phi_abs(self, simulation_output: SimulationOutput) -> None:
        """Check the beam phase at the exit of the linac."""
        assert wrap_approx("phi_abs", simulation_output, abs=5e0)

    def test_phi_s(self, simulation_output: SimulationOutput) -> None:
        """Check the synchronous phase of the cavity 142."""
        assert wrap_approx("phi_s", simulation_output, elt="FM142")

    def test_v_cav(self, simulation_output: SimulationOutput) -> None:
        """Check the accelerating voltage of the cavity 142."""
        assert wrap_approx("v_cav_mv", simulation_output, elt="FM142")

    @pytest.mark.xfail(
        condition=True,
        reason="TransferMatrix.get bugs w/ TraceWin",
        raises=IndexError,
    )
    def test_r_xx(self, simulation_output: SimulationOutput) -> None:
        """Verify that final xx transfer matrix is correct."""
        assert wrap_approx("r_xx", simulation_output)

    @pytest.mark.xfail(
        condition=True,
        reason="TransferMatrix.get bugs w/ TraceWin",
        raises=IndexError,
    )
    def test_r_yy(self, simulation_output: SimulationOutput) -> None:
        """Verify that final yy transfer matrix is correct."""
        assert wrap_approx("r_yy", simulation_output)

    @pytest.mark.xfail(
        condition=True,
        reason="TransferMatrix.get bugs w/ TraceWin",
        raises=IndexError,
    )
    def test_r_zdelta(self, simulation_output: SimulationOutput) -> None:
        """Verify that final longitudinal transfer matrix is correct."""
        assert wrap_approx("r_zdelta", simulation_output)


@pytest.mark.tracewin
def test_deprecated_flag_phi_abs_false(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """Check that the ``flag_phi_abs`` is considered, but warning is raised."""
    out_folder = tmp_path_factory.mktemp("tmp")
    config_keys = {
        "files": "files",
        "beam_calculator": "generic_tracewin",
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


@pytest.mark.tracewin
def test_deprecated_flag_phi_abs_true(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """Check that the ``flag_phi_abs`` is considered, but warning is raised."""
    out_folder = tmp_path_factory.mktemp("tmp")
    config_keys = {
        "files": "files",
        "beam_calculator": "generic_tracewin",
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
