"""Test the :class:`.Envelope3D` solver.

.. todo::
    Test emittance, envelopes, cavity phase definitions.

"""

from typing import Any

import pytest
from tests.reference import compare_with_reference

import lightwin.config_manager
from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.beam_calculation.factory import BeamCalculatorsFactory
from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.constants import example_config
from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.core.accelerator.factory import NoFault

params = [
    pytest.param(
        (False, 40), marks=pytest.mark.smoke, id="Envelope3D relative phase"
    ),
    pytest.param(
        (True, 40), marks=pytest.mark.smoke, id="Envelope3D absolute phase"
    ),
]


@pytest.fixture(scope="class", params=params)
def config(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
) -> dict[str, dict[str, Any]]:
    """Set the configuration, common to all solvers."""
    out_folder = tmp_path_factory.mktemp("tmp")
    flag_phi_abs, n_steps_per_cell = request.param

    config_keys = {
        "files": "files",
        "beam_calculator": "generic_envelope3d",
        "beam": "beam",
    }
    override = {
        "files": {
            "project_folder": out_folder,
        },
        "beam_calculator": {
            "tool": "Envelope3D",
            "flag_phi_abs": flag_phi_abs,
            "n_steps_per_cell": n_steps_per_cell,
        },
    }
    my_config = lightwin.config_manager.process_config(
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


@pytest.mark.envelope3d
class TestSolver3D:
    """Gater all the tests in a single class."""

    _w_kin_tol = 1e-3
    _phi_abs_tol = 1e-2
    _phi_s_tol = 1e-2
    _v_cav_tol = 1e-3
    _r_xx_tol = 5e-1
    _r_yy_tol = 5e-1
    _r_zdelta_tol = 5e-3

    def test_w_kin(self, simulation_output: SimulationOutput) -> None:
        """Verify that final energy is correct."""
        return compare_with_reference(
            simulation_output, "w_kin", tol=self._w_kin_tol
        )

    def test_phi_abs(self, simulation_output: SimulationOutput) -> None:
        """Verify that final absolute phase is correct."""
        return compare_with_reference(
            simulation_output, "phi_abs", tol=self._phi_abs_tol
        )

    def test_phi_s(self, simulation_output: SimulationOutput) -> None:
        """Verify that synchronous phase in last cavity is correct."""
        return compare_with_reference(
            simulation_output, "phi_s", elt="FM142", tol=self._phi_s_tol
        )

    def test_v_cav(self, simulation_output: SimulationOutput) -> None:
        """Verify that accelerating voltage in last cavity is correct."""
        return compare_with_reference(
            simulation_output, "v_cav_mv", elt="FM142", tol=self._v_cav_tol
        )

    def test_r_xx(self, simulation_output: SimulationOutput) -> None:
        """Verify that final xx transfer matrix is correct."""
        return compare_with_reference(
            simulation_output, "r_xx", tol=self._r_xx_tol
        )

    def test_r_yy(self, simulation_output: SimulationOutput) -> None:
        """Verify that final yy transfer matrix is correct."""
        return compare_with_reference(
            simulation_output, "r_yy", tol=self._r_yy_tol
        )

    def test_r_zdelta(self, simulation_output: SimulationOutput) -> None:
        """Verify that final longitudinal transfer matrix is correct."""
        return compare_with_reference(
            simulation_output, "r_zdelta", tol=self._r_zdelta_tol
        )
