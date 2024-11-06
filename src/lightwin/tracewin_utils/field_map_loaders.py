"""Define functions to load field maps."""

import itertools
import logging
from collections.abc import Collection
from functools import lru_cache
from pathlib import Path

import numpy as np


@lru_cache(100)
def warn_norm(path: Path, norm: float):
    """Raise this warning only once.

    https://stackoverflow.com/questions/31953272/logging-print-message-only-once

    """
    logging.warning(
        f"The field in {path} has a normalization factor of {norm}, different "
        "from unity."
    )


def load_field_1d(path: Path) -> tuple[int, float, float, np.ndarray, int]:
    """Load a 1D field.

    Parameters
    ----------
    path : pathlib.Path
        The path to the file to load.

    Returns
    -------
    n_z : int
        Number of steps in the array.
    zmax : float
        z position of the filemap end.
    norm : float
        Electric field normalisation factor. It is different from ``k_e`` (6th
        argument of the FIELD_MAP command). Electric fields are normalised by
        ``k_e/norm``, hence norm should be unity by default.
    f_z : numpy.ndarray
        Array holding field. If electric, will be in :unit:`MV/m`.
    n_cell : int
        Number of cells in the cavity.

    """
    n_z: int | None = None
    zmax: float | None = None
    norm: float | None = None

    f_z = []
    try:
        with open(path, "r", encoding="utf-8") as file:
            for i, line in enumerate(file):
                if i == 0:
                    line_splitted = line.split(" ")

                    # Sometimes the separator is a tab and not a space:
                    if len(line_splitted) < 2:
                        line_splitted = line.split("\t")

                    n_z = int(line_splitted[0])
                    # Sometimes there are several spaces or tabs between
                    # numbers
                    zmax = float(line_splitted[-1])
                    continue

                if i == 1:
                    try:
                        norm = float(line)
                    except ValueError as e:
                        logging.error(f"Error reading {line = } in {path}.")
                    continue

                f_z.append(float(line))
    except UnicodeDecodeError as e:
        logging.error(
            f"File {path} could not be loaded. Check that it is non-binary."
            "Returning nothing and trying to continue without it."
        )
        raise RuntimeError(e)

    assert n_z is not None
    assert zmax is not None
    assert norm is not None
    n_cell = get_number_of_cells(f_z)
    if abs(norm - 1.0) > 1e-6:
        warn_norm(path, norm)
    return n_z, zmax, norm, np.array(f_z), n_cell


def is_a_valid_1d_electric_field(
    n_z: int,
    zmax: float,
    f_z: np.ndarray,
    cavity_length: float,
    tol: float = 1e-6,
    **validity_check_kwargs,
) -> bool:
    """Assert that the electric field that we loaded is valid."""
    if f_z.shape[0] != n_z + 1:
        logging.error(
            f"The electric field file should have {n_z + 1} lines, but it is "
            f"{f_z.shape[0]} lines long. "
        )
        return False

    if abs(zmax - cavity_length) > tol:
        logging.error(
            f"Mismatch between the length of the field map {zmax = } and "
            f"{cavity_length = }."
        )
        return False

    return True


def load_field_3d(
    path: Path,
) -> tuple[
    int, float, int, float, float, int, float, float, float, np.ndarray
]:
    """Load a 3D field.

    Parameters
    ----------
    path : pathlib.Path
        The path to the file to load.

    Returns
    -------
    n_z : int
        Number of steps along the z-axis.
    zmax : float
        Maximum z position.
    n_x : int
        Number of steps along the x-axis.
    xmin : float
        Minimum x position.
    xmax : float
        Maximum x position.
    n_y : int
        Number of steps along the y-axis.
    ymin : float
        Minimum y position.
    ymax : float
        Maximum y position.
    norm : float
        Field normalization factor.
    field_values : numpy.ndarray
        3D array holding field values. If electric, will be in :unit:`MV/m`.

    """
    field_values = []
    try:
        with open(path, "r", encoding="utf-8") as file:
            n_z, zmax = map(float, file.readline().split())
            n_z = int(n_z)

            n_x, xmin, xmax = map(float, file.readline().split())
            n_x = int(n_x)

            n_y, ymin, ymax = map(float, file.readline().split())
            n_y = int(n_y)

            norm = float(file.readline().strip())

            field_values = np.zeros((n_z + 1, n_y + 1, n_x + 1))

            for k in range(n_z + 1):
                for j in range(n_y + 1):
                    for i in range(n_x + 1):
                        line = file.readline().strip()
                        field_values[k, j, i] = float(line)

    except UnicodeDecodeError as e:
        logging.error(
            f"File {path} could not be loaded. Ensure it is a valid text file."
        )
        raise RuntimeError(e)

    except ValueError as e:
        logging.error(
            f"Error parsing field data from file {path}. Ensure format consistency."
        )
        raise RuntimeError(e)

    assert norm is not None, "Normalization factor (norm) is missing."

    if abs(norm - 1.0) > 1e-6:
        warn_norm(path, norm)

    return n_z, zmax, n_x, xmin, xmax, n_y, ymin, ymax, norm, field_values


def is_a_valid_3d_field(
    zmax: float,
    n_x: int,
    n_y: int,
    n_z: int,
    field: np.ndarray,
    cavity_length: float,
    tol: float = 1e-6,
    **validity_check_kwargs,
) -> bool:
    """Assert that the 3D field we loaded is valid.

    Parameters
    ----------
    n_x, n_y, n_z : int
        Number of steps along the three axis.
    xmacx, ymax, zmax : float
        Maximum z position.
    ymin : float
        Minimum y position.
    ymax : float
        Maximum y position.
    xmin : float
        Minimum x position.
    xmax : float
        Maximum x position.
    field : np.ndarray
        3D array holding field values.
    cavity_length_z : float
        Expected length along the z-axis.
    tol : float, optional
        Tolerance for length comparisons, by default 1e-6.

    Returns
    -------
    bool
        True if the field is valid, False otherwise.
    """
    if field.shape != (n_z + 1, n_y + 1, n_x + 1):
        logging.error(
            f"Field array shape {field.shape} does not match expected shape "
            f"({n_z + 1}, {n_y + 1}, {n_x + 1})."
        )
        return False

    if abs(zmax - cavity_length) > tol:
        logging.error(
            f"Mismatch between the z length of the field map {zmax = } and "
            f"{cavity_length = }."
        )
        return False
    return True


def get_number_of_cells(f_z: Collection[float]) -> int:
    """Count number of times the array of z-electric field changes sign.

    See `SO`_.

    .. _SO: https://stackoverflow.com/a/2936859/12188681

    """
    n_cell = len(list(itertools.groupby(f_z, lambda z: z > 0.0)))
    return n_cell


def field_values_on_axis(
    field_values: np.ndarray, n_x: int, n_y: int
) -> np.ndarray:
    """Give only values at ``x=y=0``.

    For now, we just hope that the n_x/2 and n_y/2 axis correspond to the axis.

    """
    n_x0 = int((n_x + 1) / 2)
    n_y0 = int((n_y + 1) / 2)
    return field_values[:, n_x0, n_y0]


FIELD_MAP_LOADERS = {".edz": load_field_1d}  #:
