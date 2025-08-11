"""Check that the field map loading functions work as expected."""

from pathlib import Path

import numpy as np
import pytest

from lightwin.tracewin_utils.field_map_loaders import (
    load_field_1d,
    load_field_3d,
)


@pytest.fixture
def sample_field_3d(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a temporary sample field file for testing."""
    sample_data = """2 10.0
1 0.0 5.0
1 0.0 5.0
1.0
1.1
1.2
1.3
1.4
1.5
1.6
1.7
1.8
1.9
2.0
2.1
2.2
"""
    temp_dir = tmp_path_factory.mktemp("data")
    file_path = temp_dir / "sample_field_3d.edz"
    file_path.write_text(sample_data)
    return file_path


@pytest.fixture
def sample_field_1d_file(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a temporary sample 1D field file for testing."""
    sample_data = """3 10.0
1.0
1.1
1.2
1.3
"""
    temp_dir = tmp_path_factory.mktemp("data")
    file_path = temp_dir / "sample_field_1d.txt"
    file_path.write_text(sample_data)
    return file_path


@pytest.mark.implementation
@pytest.mark.smoke
def test_field_3d(sample_field_3d: Path) -> None:
    """Test ``field_3d`` with a sample 3D field file."""
    expected_nz = 2
    expected_zmax = 10.0
    expected_nx = 1
    expected_xmin = 0.0
    expected_xmax = 5.0
    expected_ny = 1
    expected_ymin = 0.0
    expected_ymax = 5.0
    expected_norm = 1.0
    expected_field = np.array(
        [
            [[1.1, 1.2], [1.3, 1.4]],
            [[1.5, 1.6], [1.7, 1.8]],
            [[1.9, 2.0], [2.1, 2.2]],
        ]
    )

    n_z, zmax, n_x, xmin, xmax, n_y, ymin, ymax, norm, field = load_field_3d(
        sample_field_3d
    )

    # Assertions
    assert n_z == expected_nz
    assert zmax == expected_zmax
    assert n_x == expected_nx
    assert xmin == expected_xmin
    assert xmax == expected_xmax
    assert n_y == expected_ny
    assert ymin == expected_ymin
    assert ymax == expected_ymax
    assert norm == expected_norm
    np.testing.assert_array_almost_equal(field, expected_field)


@pytest.mark.implementation
@pytest.mark.smoke
def test_field_1d(sample_field_1d_file: Path) -> None:
    """Test field_1d with a sample 1D field file."""
    expected_nz = 3
    expected_zmax = 10.0
    expected_norm = 1.0
    expected_field = np.array([1.1, 1.2, 1.3])
    expected_n_cell = 1

    n_z, zmax, norm, f_z, n_cell = load_field_1d(sample_field_1d_file)
    assert n_z == expected_nz
    assert zmax == expected_zmax
    assert norm == expected_norm
    np.testing.assert_array_almost_equal(f_z, expected_field)
    assert n_cell == expected_n_cell
