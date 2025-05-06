"""Define tests for the :class:`.InitialBeamParameters` class."""

import numpy as np
import pytest

from lightwin.core.beam_parameters.initial_beam_parameters import (
    InitialBeamParameters,
)
from lightwin.core.beam_parameters.phase_space.initial_phase_space_beam_parameters import (
    InitialPhaseSpaceBeamParameters,
)


@pytest.fixture
def dummy_phase_space() -> InitialPhaseSpaceBeamParameters:
    ps = InitialPhaseSpaceBeamParameters(
        phase_space_name="zdelta",
        eps_no_normalization=1.0,
        eps_normalized=2.0,
        envelopes=np.array([3.0, 4.0]),
        twiss=np.array([10.0, 20.0, 30.0]),
        sigma=np.array([[-1.0, -2.0], [-3.0, -4.0]]),
        tm_cumul=np.array([[-10.0, -20.0], [-30.0, -40.0]]),
        mismatch_factor=42.0,
    )
    return ps


@pytest.fixture
def beam(
    dummy_phase_space: InitialPhaseSpaceBeamParameters,
) -> InitialBeamParameters:
    beam = InitialBeamParameters(z_abs=0.5, gamma_kin=100.0, beta_kin=0.9)
    beam.zdelta = dummy_phase_space
    return beam


def test_has_direct(beam: InitialBeamParameters) -> None:
    assert beam.has("z_abs")
    assert not beam.has("nonexistent")


def test_has_nested(beam: InitialBeamParameters) -> None:
    assert beam.has("twiss_zdelta")
    assert not beam.has("twiss_phiw")
    assert not beam.has("twiss_nonexistent")


def test_get_single_key(beam: InitialBeamParameters) -> None:
    assert beam.get("alpha", phase_space_name="zdelta") == 10.0


def test_get_inferred_key(beam: InitialBeamParameters) -> None:
    assert beam.get("alpha_zdelta") == 10.0


def test_get_missing_key(beam: InitialBeamParameters) -> None:
    assert beam.get("nonexistent") is None  # pyright: ignore


def test_get_none_to_nan(beam: InitialBeamParameters) -> None:
    assert np.isnan(
        beam.get("nonexistent", none_to_nan=True)  # pyright: ignore
    )


def test_get_multiple_keys(beam: InitialBeamParameters) -> None:
    alpha, beta = beam.get("alpha_zdelta", "beta_zdelta")
    assert alpha == 10.0
    assert beta == 20.0


def test_get_mixed(beam: InitialBeamParameters) -> None:
    alpha, z_abs = beam.get("alpha_zdelta", "z_abs")
    assert alpha == 10.0
    assert z_abs == 0.5


def test_get_mixed_phase_space_name(beam: InitialBeamParameters) -> None:
    alpha, z_abs = beam.get("alpha", "z_abs", phase_space_name="zdelta")
    assert alpha == 10.0
    assert z_abs == 0.5


def test_get_to_numpy(beam: InitialBeamParameters) -> None:
    val = beam.get("twiss_zdelta")
    assert isinstance(val, np.ndarray)


def test_sigma(beam: InitialBeamParameters) -> None:
    sigma = beam.sigma
    assert sigma.shape == (6, 6)
    expected = np.array([[-1.0, -2.0], [-3.0, -4.0]])
    np.testing.assert_array_equal(sigma[4:, 4:], expected)
