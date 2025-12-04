"""Test behavior of :class:`.CavitySettings`."""

from collections.abc import Callable

import pytest

from lightwin.core.elements.field_maps.cavity_settings import (
    CavitySettings,
    MissingAttributeError,
)
from lightwin.core.em_fields.field import Field
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
        field: Field | None = None,
    ) -> None:
        """Init object only with interesting args."""
        super().__init__(
            k_e=k_e,
            phi=phi,
            reference=reference,
            status=status,
            freq_bunch_mhz=freq_bunch_mhz,
            freq_cavity_mhz=freq_cavity_mhz,
            transf_mat_func_wrappers=transf_mat_func_wrappers,
            phi_s_funcs=phi_s_funcs,
            field=field,
        )

    def _phi_0_rel_to_cavity_parameters(
        self, phi_0_rel: float
    ) -> tuple[float, float]:
        """Override the normal method."""
        return 2 * phi_0_rel, -2 * phi_0_rel


def test_abs_to_rel():
    """Test calculation of phi abs -> rel."""
    settings = MockCavitySettings(phi=3, reference="phi_0_abs")
    settings.phi_rf = 1
    assert pytest.approx(settings.phi_0_rel) == 4


def test_abs_to_rel_missing_phi_rf():
    """Test calculation of phi abs -> rel, but phi_rf misses."""
    settings = MockCavitySettings(phi=3, reference="phi_0_abs")
    with pytest.raises(MissingAttributeError):
        settings.phi_0_rel


def test_rel_to_abs():
    """Test calculation of phi rel -> abs."""
    settings = MockCavitySettings(phi=3, reference="phi_0_rel")
    settings.phi_rf = 1
    assert pytest.approx(settings.phi_0_abs) == 2


def test_rel_to_abs_missing_phi_rf():
    """Test calculation of phi rel -> abs, but phi_rf misses."""
    settings = MockCavitySettings(phi=3, reference="phi_0_rel")
    with pytest.raises(MissingAttributeError):
        settings.phi_0_abs


def test_rel_to_synch():
    """Test calculation of phi rel -> s."""
    settings = MockCavitySettings(phi=3, reference="phi_0_rel")
    settings.phi_rf = 1
    assert pytest.approx(settings.phi_s) == -6


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


def test_change_reference_error():
    """Update reference phase, but new reference can't be calculated."""
    settings = MockCavitySettings(phi=3, reference="phi_0_abs")
    with pytest.raises(MissingAttributeError):
        settings.set_reference("phi_0_rel")


def test_change_reference_standard():
    """Update reference phase.

    In particular:
        - Changing reference should not raise any error because new reference
          phase can be calculated
        - The new reference phase was effectively calculated during the
          reference setting.
        - Old reference phase is not removed.

    """
    settings = MockCavitySettings(phi=3, reference="phi_0_abs")
    settings.phi_rf = 1

    settings.set_reference("phi_0_rel", ensure_can_be_calculated=True)
    assert pytest.approx(settings._phi_0_rel) == 4
    assert pytest.approx(settings._phi_0_abs) == 3


def test_change_reference_and_its_value():
    """Change of reference, also its value.

    In particular:
        - Changing reference should not raise any error because new reference
          phase was given directly.
        - The new reference phase was effectively updated during the reference
          setting.
        - Old reference phase was removed.

    This behavior corresponds to the creation of :class:`.ListOfElements` with
    ``SET_SYNC_PHASE`` command:
        1. We create :class:`.CavitySettings` objects first, using the
        ``FLAG_PHI_ABS``.
        2. Then we treat the ``SET_SYNC_PHASE``, transforming absolute/relative
        phases to synchronous phases.

    """
    settings = MockCavitySettings(phi=3.0, reference="phi_0_abs")
    settings.set_reference("phi_s", phi_ref=settings.phi_ref)
    assert pytest.approx(settings._phi_s) == 3.0
    assert not hasattr(settings, "_phi_0_abs")
