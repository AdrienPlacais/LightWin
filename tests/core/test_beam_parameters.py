"""Define tests for :class:`.BeamParameters`."""

import numpy as np
import pytest

from lightwin.core.beam_parameters.beam_parameters import BeamParameters
from lightwin.core.beam_parameters.phase_space.phase_space_beam_parameters import (
    PhaseSpaceBeamParameters,
)
from lightwin.core.elements.element import Element


@pytest.fixture
def dummy_phase_space() -> PhaseSpaceBeamParameters:
    twiss = np.array(
        [
            [10.0, 20.0, 30.0],
            [11.0, 21.0, 31.0],
            [12.0, 22.0, 32.0],
        ]
    )
    ps = PhaseSpaceBeamParameters(
        phase_space_name="zdelta",
        eps_no_normalization=np.array([1.0, 1.1, 1.2]),
        eps_normalized=np.array([2.0, 2.1, 2.2]),
        envelopes=np.array([[3.0, 4.0], [3.1, 4.1], [3.2, 4.2]]),
        twiss=twiss,
        sigma=np.random.rand(3, 2, 2),
        tm_cumul=np.random.rand(3, 2, 2),
        mismatch_factor=np.array([42.0, 43.0, 44.0]),
    )

    return ps


@pytest.fixture
def beam(dummy_phase_space: PhaseSpaceBeamParameters) -> BeamParameters:
    def element_to_index(elt: str | Element, pos: str | None) -> int:
        """This is just for quick tests, do not use this in real life."""
        allowed = ("ELT1", "ELT2", "ELT3")
        return allowed.index(elt)

    beam = BeamParameters(
        z_abs=np.array([0.0, 0.5, 1.0]),
        gamma_kin=np.array([100.0, 101.0, 102.0]),
        beta_kin=np.array([0.9, 0.91, 0.92]),
        element_to_index=element_to_index,
    )
    beam.zdelta = dummy_phase_space
    return beam


@pytest.mark.implementation
def test_has_direct(beam: BeamParameters) -> None:
    assert beam.has("z_abs")
    assert not beam.has("nonexistent")


@pytest.mark.implementation
def test_has_nested(beam: BeamParameters) -> None:
    assert beam.has("twiss_zdelta")
    assert not beam.has("twiss_phiw")
    assert not beam.has("twiss_nonexistent")


@pytest.mark.implementation
def test_get_single_key(beam: BeamParameters) -> None:
    val = beam.get("alpha", phase_space_name="zdelta")
    np.testing.assert_array_equal(val, np.array([10.0, 11.0, 12.0]))


@pytest.mark.implementation
def test_get_single_key_elt(beam: BeamParameters) -> None:
    val = beam.get("alpha", phase_space_name="zdelta", elt="ELT2")
    assert val == 11.0


@pytest.mark.implementation
def test_get_inferred_key(beam: BeamParameters) -> None:
    val = beam.get("alpha_zdelta")
    np.testing.assert_array_equal(val, np.array([10.0, 11.0, 12.0]))


@pytest.mark.implementation
def test_get_missing_key(beam: BeamParameters) -> None:
    assert beam.get("nonexistent") is None  # pyright: ignore


@pytest.mark.implementation
def test_get_none_to_nan(beam: BeamParameters) -> None:
    val = beam.get("nonexistent", none_to_nan=True)  # pyright: ignore
    assert np.isnan(val)


@pytest.mark.implementation
def test_get_multiple_keys(beam: BeamParameters) -> None:
    alpha, beta = beam.get("alpha_zdelta", "beta_zdelta")
    np.testing.assert_array_equal(alpha, np.array([10.0, 11.0, 12.0]))
    np.testing.assert_array_equal(beta, np.array([20.0, 21.0, 22.0]))


@pytest.mark.implementation
def test_get_multiple_keys_elt(beam: BeamParameters) -> None:
    alpha, beta = beam.get("alpha_zdelta", "beta_zdelta", elt="ELT2")
    assert alpha == 11.0
    assert beta == 21.0


@pytest.mark.implementation
def test_get_mixed(beam: BeamParameters) -> None:
    alpha, z_abs = beam.get("alpha_zdelta", "z_abs")
    np.testing.assert_array_equal(alpha, np.array([10.0, 11.0, 12.0]))
    np.testing.assert_array_equal(z_abs, np.array([0.0, 0.5, 1.0]))


@pytest.mark.implementation
def test_get_mixed_phase_space_name(beam: BeamParameters) -> None:
    alpha, z_abs = beam.get("alpha", "z_abs", phase_space_name="zdelta")
    np.testing.assert_array_equal(alpha, np.array([10.0, 11.0, 12.0]))
    np.testing.assert_array_equal(z_abs, np.array([0.0, 0.5, 1.0]))


@pytest.mark.implementation
def test_get_to_numpy(beam: BeamParameters) -> None:
    val = beam.get("twiss_zdelta")
    assert isinstance(val, np.ndarray)
    assert val.shape == (3, 3)


@pytest.mark.implementation
def test_sigma(beam: BeamParameters) -> None:
    sigma = beam.sigma
    assert sigma.shape == (3, 6, 6)
    # We only check the last block, which should match zdelta.sigma
    np.testing.assert_array_equal(sigma[:, 4:, 4:], beam.zdelta.sigma)
