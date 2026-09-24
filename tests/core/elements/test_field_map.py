"""Define tests for :class:`.FieldMap`."""

import math
from pathlib import Path

import numpy as np
import pytest

from lightwin.core.elements.field_maps.cavity_settings import CavitySettings
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.tracewin_utils.line import DatLine


class DummyLine(DatLine):
    """Mocked :class:`.DatLine` with a minimal ``FIELD_MAP`` instruction."""

    def __init__(self) -> None:
        """Build a hardcoded single-spoke field-map line."""
        line = (
            "FIELD_MAP 100 415.16 153.171 30 1.55425 1.55425 0 0"
            " Simple_Spoke_1D 1"
        )
        super().__init__(line, idx=0)


@pytest.fixture
def dummy_cavity_settings() -> CavitySettings:
    """Return nominal cavity settings with a known phase and voltage."""
    settings = CavitySettings(
        k_e=1.55425,
        phi=math.radians(153.171),
        reference="phi_0_abs",
        status="nominal",
        freq_bunch_mhz=352.0,
        freq_cavity_mhz=352.0,
    )
    settings.phi_rf = 0.3
    settings.v_cav_mv = 5.67
    return settings


@pytest.fixture
def field_map(dummy_cavity_settings: CavitySettings) -> FieldMap:
    """Return a :class:`.FieldMap` built from the dummy line and settings."""
    return FieldMap(
        line=DummyLine(),
        default_field_map_folder=Path("/dummy/path"),
        cavity_settings=dummy_cavity_settings,
    )


def test_has_direct_attr(field_map: FieldMap) -> None:
    """``has`` finds a direct attribute and rejects an unknown one."""
    assert field_map.has("length_m")
    assert not field_map.has("nonexistent")


def test_has_nested_attr(field_map: FieldMap) -> None:
    """``has`` resolves attributes delegated to ``cavity_settings``."""
    assert field_map.has("phi_0_abs")
    assert field_map.has("v_cav_mv")


def test_has_property_name(field_map: FieldMap) -> None:
    """``has`` finds attributes exposed via properties."""
    assert field_map.has("name")


def test_get_direct_attr(field_map: FieldMap) -> None:
    """``get`` returns a direct attribute with the correct value."""
    assert np.isclose(field_map.get("length_m"), 0.41516)


def test_get_nested_attr(field_map: FieldMap) -> None:
    """``get`` retrieves nested cavity-settings attributes correctly."""
    assert np.isclose(field_map.get("phi_0_abs"), math.radians(153.171))
    assert np.isclose(field_map.get("v_cav_mv"), 5.67)


def test_get_property_name(field_map: FieldMap) -> None:
    """``get`` returns the element name as a string."""
    assert isinstance(field_map.get("name"), str)


def test_get_multiple_keys(field_map: FieldMap) -> None:
    """``get`` returns a tuple when called with multiple keys."""
    k_e, phi = field_map.get("k_e", "phi_0_abs")
    assert np.isclose(k_e, 1.55425)
    assert np.isclose(phi, math.radians(153.171))


def test_get_multiple_keys_to_deg(field_map: FieldMap) -> None:
    """``get`` converts phase keys to degrees when ``to_deg=True``."""
    k_e, phi = field_map.get("k_e", "phi_0_abs", to_deg=True)
    assert np.isclose(k_e, 1.55425)
    assert np.isclose(phi, 153.171)


def test_get_missing_key(field_map: FieldMap) -> None:
    """``get`` returns None for a key that does not exist."""
    assert field_map.get("nonexistent") is None  # pyright: ignore


def test_get_none_to_nan(field_map: FieldMap) -> None:
    """``get`` converts missing-key result to NaN when ``none_to_nan=True``."""
    val = field_map.get("nonexistent", none_to_nan=True)  # pyright: ignore
    assert np.isnan(val)


@pytest.mark.implementation
def test_to_line_phi_0_abs(field_map: FieldMap) -> None:
    """Check that the absolute entry phase is written correctly in the line."""
    expected = [
        "FIELD_MAP",
        "100",
        "415.16",
        "153.171",
        "30",
        "1.55425",
        "1.55425",
        "0",
        "0",
        "Simple_Spoke_1D",
        "1",
    ]
    returned = field_map.to_line(which_phase="phi_0_abs")
    assert expected == returned


@pytest.mark.implementation
def test_to_line_phi_0_rel(field_map: FieldMap) -> None:
    """Check that the relative entry phase is written correctly in the line."""
    expected = [
        "FIELD_MAP",
        "100",
        "415.16",
        "170.35973",
        "30",
        "1.55425",
        "1.55425",
        "0",
        "0",
        "Simple_Spoke_1D",
        "0",
    ]
    returned = field_map.to_line(which_phase="phi_0_rel", round=5)
    assert expected == returned


@pytest.mark.implementation
def test_to_line_phi_s(field_map: FieldMap) -> None:
    """Check that the synchronous phase is written correctly in the line."""
    expected = [
        "FIELD_MAP",
        "100",
        "415.16",
        "180.0",
        "30",
        "1.55425",
        "1.55425",
        "0",
        "0",
        "Simple_Spoke_1D",
        "0",
    ]
    field_map.cavity_settings._phi_s = math.pi
    returned = field_map.to_line(which_phase="phi_s", round=5)
    assert expected == returned
