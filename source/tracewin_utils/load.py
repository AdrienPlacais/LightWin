"""Define functions to load and preprocess the TraceWin files."""

import itertools
import logging
from pathlib import Path
from tkinter import Tk
from tkinter.filedialog import askopenfilename

import numpy as np

# Dict of data that can be imported from TW's "Data" table.
# More info in results
TRACEWIN_IMPORT_DATA_TABLE = {
    "v_cav_mv": 6,
    "phi_0_rel": 7,
    "phi_s": 8,
    "w_kin": 9,
    "beta": 10,
    "z_abs": 11,
    "phi_abs_array": 12,
}


def table_structure_file(
    path: Path,
) -> list[list[str]]:
    """Load the file produced by ``Data`` ``Save table to file``."""
    file_content = []
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line_content = line.split()

            try:
                int(line_content[0])
            except ValueError:
                continue
            file_content.append(line_content)
    return file_content


def results(path: Path, prop: str) -> np.ndarray:
    """Load a property from TraceWin's "Data" table.

    Parameters
    ----------
    path : Path
        Path to results file. It must be saved from TraceWin:
        ``Data`` > ``Save table to file``.
    prop : str
        Name of the desired property. Must be in d_property.

    Returns
    -------
    data_ref: numpy array
        Array containing the desired property.

    """
    if not path.is_file():
        logging.warning(
            "Filepath to results is incorrect. Provide another one."
        )
        Tk().withdraw()
        path = Path(
            askopenfilename(filetypes=[("TraceWin energies file", ".txt")])
        )

    idx = TRACEWIN_IMPORT_DATA_TABLE[prop]

    data_ref = []
    with open(path, encoding="utf-8") as file:
        for line in file:
            try:
                int(line.split("\t")[0])
            except ValueError:
                continue
            splitted_line = line.split("\t")
            new_data = splitted_line[idx]
            if new_data == "-":
                new_data = np.NaN
            data_ref.append(new_data)
    data_ref = np.array(data_ref).astype(float)
    return data_ref


def load_1d_field(path: Path) -> tuple[int, float, float, np.ndarray, int]:
    """Load a 1D field (``.edz`` extension).

    Parameters
    ----------
    path : Path
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
    f_z : np.ndarray
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
                    norm = float(line)
                    continue

                f_z.append(float(line))
    except UnicodeDecodeError:
        logging.error(
            "File could not be loaded. Check that it is non-binary."
            "Returning nothing and trying to continue without it."
        )
        raise IOError()

    assert n_z is not None
    assert zmax is not None
    assert norm is not None
    n_cell = _get_number_of_cells(f_z)
    return n_z, zmax, norm, np.array(f_z), n_cell


def _get_number_of_cells(f_z: list[float]) -> int:
    """Count number of times the array of z-electric field changes sign.

    See `SO`_.

    .. _SO: https://stackoverflow.com/a/2936859/12188681

    """
    n_cell = len(list(itertools.groupby(f_z, lambda z: z > 0.0)))
    return n_cell


def transfer_matrices(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load the transfer matrix as calculated by TraceWin."""
    transfer_matrices = []
    position_in_m = []
    elements_numbers = []

    with open(path, "r", encoding="utf-8") as file:
        lines = []
        for i, line in enumerate(file):
            lines.append(line)
            if i % 7 == 6:
                elements_numbers.append(int(lines[0].split()[1]))
                position_in_m.append(float(lines[0].split()[3]))
                transfer_matrices.append(_transfer_matrix(lines[1:]))
                lines = []
    elements_numbers = np.array(elements_numbers)
    position_in_m = np.array(position_in_m)
    transfer_matrices = np.array(transfer_matrices)
    return elements_numbers, position_in_m, transfer_matrices


def _transfer_matrix(lines: list[str]) -> np.ndarray:
    """Load a single element transfer matrix."""
    transfer_matrix = np.empty((6, 6), dtype=float)
    for i, line in enumerate(lines):
        transfer_matrix[i] = np.array(line.split(), dtype=float)
    return transfer_matrix


FIELD_MAP_LOADERS = {".edz": load_1d_field}  #:
