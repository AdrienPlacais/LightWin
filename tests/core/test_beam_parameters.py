"""Define tests for :class:`.BeamParameters`."""

import numpy as np
import pytest

from lightwin.core.beam_parameters.beam_parameters import BeamParameters
from lightwin.core.beam_parameters.phase_space.phase_space_beam_parameters import (
    PhaseSpaceBeamParameters,
)
from lightwin.core.elements.element import POS_T, Element


@pytest.fixture
def dummy_phase_space() -> PhaseSpaceBeamParameters:
    """Return a ``zdelta`` phase space with known per-element Twiss values."""
    twiss = np.array(
        [[10.0, 20.0, 30.0], [11.0, 21.0, 31.0], [12.0, 22.0, 32.0]]
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
    """Return a :class:`.BeamParameters` with ``zdelta`` attached.

    The ``element_to_index`` stub maps ``"ELT1"``, ``"ELT2"``, ``"ELT3"`` to
    indices 0, 1, 2 respectively.

    """

    def element_to_index(
        *, elt: str | Element, pos: POS_T | None = None, **kwargs
    ) -> int | slice:
        """Get index corresponding to current element.

        Do not use this one in real life, its a dummy fixture.

        """
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


def test_has_direct(beam: BeamParameters) -> None:
    """``has`` finds direct attributes and rejects unknown ones."""
    assert beam.has("z_abs")
    assert not beam.has("nonexistent")


def test_has_nested(beam: BeamParameters) -> None:
    """``has`` resolves nested phase-space keys and rejects missing ones."""
    assert beam.has("twiss_zdelta")
    assert not beam.has("twiss_phiw")
    assert not beam.has("twiss_nonexistent")


def test_get_single_key(beam: BeamParameters) -> None:
    """``get`` returns the full array with explicit ``phase_space_name``."""
    val = beam.get("alpha", phase_space_name="zdelta")
    np.testing.assert_array_equal(val, np.array([10.0, 11.0, 12.0]))


def test_get_single_key_elt(beam: BeamParameters) -> None:
    """``get`` returns a scalar when an element name is provided."""
    val = beam.get("alpha", phase_space_name="zdelta", elt="ELT2")
    assert val == 11.0


def test_get_inferred_key(beam: BeamParameters) -> None:
    """``get`` infers phase space from a suffixed key like ``alpha_zdelta``."""
    val = beam.get("alpha_zdelta")
    np.testing.assert_array_equal(val, np.array([10.0, 11.0, 12.0]))


def test_get_missing_key(beam: BeamParameters) -> None:
    """``get`` returns None for a key that does not exist."""
    assert beam.get("nonexistent") is None  # pyright: ignore


def test_get_none_to_nan(beam: BeamParameters) -> None:
    """``get`` converts missing-key result to NaN when ``none_to_nan=True``."""
    val = beam.get("nonexistent", none_to_nan=True)  # pyright: ignore
    assert np.isnan(val)


def test_get_multiple_keys(beam: BeamParameters) -> None:
    """``get`` returns a tuple of arrays for multiple phase-space keys."""
    alpha, beta = beam.get("alpha_zdelta", "beta_zdelta")
    np.testing.assert_array_equal(alpha, np.array([10.0, 11.0, 12.0]))
    np.testing.assert_array_equal(beta, np.array([20.0, 21.0, 22.0]))


def test_get_multiple_keys_elt(beam: BeamParameters) -> None:
    """``get`` returns scalars for multiple keys when an element is given."""
    alpha, beta = beam.get("alpha_zdelta", "beta_zdelta", elt="ELT2")
    assert alpha == 11.0
    assert beta == 21.0


def test_get_mixed(beam: BeamParameters) -> None:
    """``get`` handles a mix of phase-space and direct keys in one call."""
    alpha, z_abs = beam.get("alpha_zdelta", "z_abs")
    np.testing.assert_array_equal(alpha, np.array([10.0, 11.0, 12.0]))
    np.testing.assert_array_equal(z_abs, np.array([0.0, 0.5, 1.0]))


def test_get_mixed_phase_space_name(beam: BeamParameters) -> None:
    """``get`` applies ``phase_space_name`` uniformly across mixed keys."""
    alpha, z_abs = beam.get("alpha", "z_abs", phase_space_name="zdelta")
    np.testing.assert_array_equal(alpha, np.array([10.0, 11.0, 12.0]))
    np.testing.assert_array_equal(z_abs, np.array([0.0, 0.5, 1.0]))


def test_get_to_numpy(beam: BeamParameters) -> None:
    """``get`` returns array-valued attributes as numpy arrays."""
    val = beam.get("twiss_zdelta")
    assert isinstance(val, np.ndarray)
    assert val.shape == (3, 3)


def test_sigma(beam: BeamParameters) -> None:
    """``sigma`` assembles (n, 6, 6) array with zdelta in the bottom- right."""
    sigma = beam.sigma
    assert sigma.shape == (3, 6, 6)
    np.testing.assert_array_equal(sigma[:, 4:, 4:], beam.zdelta.sigma)
