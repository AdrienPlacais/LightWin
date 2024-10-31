"""Define functions to load field maps."""

import itertools
import logging
from collections.abc import Collection
from pathlib import Path

import numpy as np


def electric_field_1d(path: Path) -> tuple[int, float, float, np.ndarray, int]:
    """Load a 1D electric field (``.edz`` extension).

    Parameters
    ----------
    path : pathlib.Path
        The path to the ``.edz`` file to load.

    Returns
    -------
    n_z : int
        Number of steps in the array.
    zmax : float
        z position of the filemap end.
    norm : float
        Electric field normalisation factor. It is different from k_e (6th
        argument of the FIELD_MAP command). Electric fields are normalised by
        k_e/norm, hence norm should be unity by default.
    f_z : numpy.ndarray
        Array of electric field in MV/m.
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
    n_cell = _get_number_of_cells(f_z)
    return n_z, zmax, norm, np.array(f_z), n_cell


def _get_number_of_cells(f_z: Collection[float]) -> int:
    """Count number of times the array of z-electric field changes sign.

    See `SO`_.

    .. _SO: https://stackoverflow.com/a/2936859/12188681

    """
    n_cell = len(list(itertools.groupby(f_z, lambda z: z > 0.0)))
    return n_cell


FIELD_MAP_LOADERS = {".edz": electric_field_1d}  #:
