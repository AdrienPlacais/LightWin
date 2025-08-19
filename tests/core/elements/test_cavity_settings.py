"""Test behavior of :class:`.CavitySettings`."""

from collections.abc import Callable

import pytest

from lightwin.core.elements.field_maps.cavity_settings import (
    CavitySettings,
    MissingAttributeError,
)
from lightwin.core.em_fields.field import Field
from lightwin.core.em_fields.rf_field import RfField
from lightwin.util.typing import REFERENCE_PHASES_T, STATUS_T


class MockCavitySettings(CavitySettings):

    def __init__(
        self,
        phi: float,
        reference: REFERENCE_PHASES_T,
        status: STATUS_T = "nominal",
        k_e: float = 1,
        freq_bunch_mhz: float = 1,
        freq_cavity_mhz: float | None = 1,
        transf_mat_func_wrappers: dict[str, Callable] | None = None,
        phi_s_funcs: dict[str, Callable] | None = None,
        rf_field: RfField | None = None,
        field: Field | None = None,
    ) -> None:
        """Init object only with interesting args."""
        super().__init__(
            k_e,
            phi,
            reference,
            status,
            freq_bunch_mhz,
            freq_cavity_mhz,
            transf_mat_func_wrappers,
            phi_s_funcs,
            rf_field,
            field,
        )

    def _phi_0_rel_to_cavity_parameters(
        self, phi_0_rel: float
    ) -> tuple[float, float]:
        """Override the normal method."""
        return 2 * phi_0_rel, -2 * phi_0_rel


@pytest.mark.implementation
def test_abs_to_rel():
    """Test calculation of phi abs -> rel."""
    settings = MockCavitySettings(phi=3, reference="phi_0_abs")
    settings.phi_rf = 1
    assert pytest.approx(settings.phi_0_rel) == 4


@pytest.mark.implementation
def test_abs_to_rel_missing_phi_rf():
    """Test calculation of phi abs -> rel, but phi_rf misses."""
    settings = MockCavitySettings(phi=3, reference="phi_0_abs")
    with pytest.raises(MissingAttributeError):
        settings.phi_0_rel


@pytest.mark.implementation
def test_rel_to_abs():
    """Test calculation of phi rel -> abs."""
    settings = MockCavitySettings(phi=3, reference="phi_0_rel")
    settings.phi_rf = 1
    assert pytest.approx(settings.phi_0_abs) == 2


@pytest.mark.implementation
def test_rel_to_abs_missing_phi_rf():
    """Test calculation of phi rel -> abs, but phi_rf misses."""
    settings = MockCavitySettings(phi=3, reference="phi_0_rel")
    with pytest.raises(MissingAttributeError):
        settings.phi_0_abs


@pytest.mark.implementation
def test_rel_to_synch():
    """Test calculation of phi rel -> s."""
    settings = MockCavitySettings(phi=3, reference="phi_0_rel")
    settings.phi_rf = 1
    assert pytest.approx(settings.phi_s) == -6


@pytest.mark.implementation
def test_update_phi_ref():
    """Test behavior when reference phase is changed.

    In particular:
       - Reference phase should be updated
       - Non-reference phases should be deleted
       - Non-reference phases should be re-calculated without issue

    """
    settings = MockCavitySettings(phi=3, reference="phi_0_abs")
    settings.phi_rf = 1
    assert pytest.approx(settings.phi_0_rel) == 4

    settings.phi_ref = 0
    assert pytest.approx(settings.phi_0_abs) == 0
    assert not hasattr(settings, "_phi_0_rel")
    assert pytest.approx(settings.phi_0_rel) == 1


@pytest.mark.implementation
def test_change_reference_error():
    """Update reference phase, but new reference can't be calculated."""
    settings = MockCavitySettings(phi=3, reference="phi_0_abs")
    with pytest.raises(MissingAttributeError):
        settings.set_reference("phi_0_rel")
