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
    """Return a ``zdelta`` phase space with known Twiss and envelope values."""
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
    """Return an :class:`.InitialBeamParameters` with ``zdelta`` attached."""
    beam = InitialBeamParameters(z_abs=0.5, gamma_kin=100.0, beta_kin=0.9)
    beam.zdelta = dummy_phase_space
    return beam


def test_has_direct(beam: InitialBeamParameters) -> None:
    """``has`` finds direct attributes and rejects unknown ones."""
    assert beam.has("z_abs")
    assert not beam.has("nonexistent")


def test_has_nested(beam: InitialBeamParameters) -> None:
    """``has`` resolves nested phase-space keys and rejects missing ones."""
    assert beam.has("twiss_zdelta")
    assert not beam.has("twiss_phiw")
    assert not beam.has("twiss_nonexistent")


def test_get_single_key(beam: InitialBeamParameters) -> None:
    """``get`` retrieves Twiss parameter with explicit ``phase_space_name``."""
    assert beam.get("alpha", phase_space_name="zdelta") == 10.0


def test_get_inferred_key(beam: InitialBeamParameters) -> None:
    """``get`` infers phase space from a suffixed key like ``alpha_zdelta``."""
    assert beam.get("alpha_zdelta") == 10.0


def test_get_missing_key(beam: InitialBeamParameters) -> None:
    """``get`` returns None for a key that does not exist."""
    assert beam.get("nonexistent") is None  # pyright: ignore


def test_get_none_to_nan(beam: InitialBeamParameters) -> None:
    """``get`` converts missing-key result to NaN when ``none_to_nan=True``."""
    assert np.isnan(
        beam.get("nonexistent", none_to_nan=True)  # pyright: ignore
    )


def test_get_multiple_keys(beam: InitialBeamParameters) -> None:
    """``get`` returns a tuple when called with multiple phase-space keys."""
    alpha, beta = beam.get("alpha_zdelta", "beta_zdelta")
    assert alpha == 10.0
    assert beta == 20.0


def test_get_mixed(beam: InitialBeamParameters) -> None:
    """``get`` handles a mix of phase-space and direct keys in one call."""
    alpha, z_abs = beam.get("alpha_zdelta", "z_abs")
    assert alpha == 10.0
    assert z_abs == 0.5


def test_get_mixed_phase_space_name(beam: InitialBeamParameters) -> None:
    """``get`` applies ``phase_space_name`` uniformly across mixed keys."""
    alpha, z_abs = beam.get("alpha", "z_abs", phase_space_name="zdelta")
    assert alpha == 10.0
    assert z_abs == 0.5


def test_get_to_numpy(beam: InitialBeamParameters) -> None:
    """``get`` returns array-valued attributes as numpy arrays."""
    val = beam.get("twiss_zdelta")
    assert isinstance(val, np.ndarray)


def test_sigma(beam: InitialBeamParameters) -> None:
    """``sigma`` assembles a 6×6 matrix with zdelta in the bottom-right."""
    sigma = beam.sigma
    assert sigma.shape == (6, 6)
    expected = np.array([[-1.0, -2.0], [-3.0, -4.0]])
    np.testing.assert_array_equal(sigma[4:, 4:], expected)
