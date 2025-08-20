"""Define functions to load and preprocess the TraceWin files."""

import logging
import re
from collections.abc import Collection
from pathlib import Path
from pprint import pformat
from typing import Literal

import numpy as np

from lightwin.core.instruction import Instruction

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


def load_dat_file(
    dat_path: Path,
    *,
    keep: Literal["none", "comments", "empty lines", "all"] = "none",
    instructions_to_insert: Collection[Instruction] = (),
) -> list[list[str]]:
    """Load the dat file and convert it into a list of lines.

    Parameters
    ----------
    dat_path : pathlib.Path
        Filepath to the ``DAT`` file, as understood by TraceWin.
    keep : Literal["none", "comments", "empty lines", "all"], optional
        To determine which un-necessary lines in the dat file should be kept.
        The default is `'none'`.
    instructions_to_insert : Collection[Instruction], optional
        Some elements or commands that are not present in the ``DAT`` file but
        that you want to add. The default is an empty tuple.

    Returns
    -------
    dat_filecontent : list[list[str]]
        List containing all the lines of dat_path.

    """
    dat_filecontent = []

    with open(dat_path, encoding="utf-8") as file:
        for line in file:
            sliced = slice_dat_line(line)

            if len(sliced) == 0:
                if keep in ("empty lines", "all"):
                    dat_filecontent.append(sliced)
                continue
            if line[0] == ";":
                if keep in ("comments", "all"):
                    dat_filecontent.append(sliced)
                continue
            dat_filecontent.append(sliced)
    if not instructions_to_insert:
        return dat_filecontent
    logging.info(
        "Will insert following instructions:\n"
        f"{pformat(instructions_to_insert, width=120)}"
    )
    for i, instruction in enumerate(instructions_to_insert):
        instruction.insert_line(
            dat_filecontent=dat_filecontent, previously_inserted=i
        )
    return dat_filecontent


def _strip_comments(line: str) -> str:
    """Remove comments from a line."""
    return line.split(";", 1)[0].strip()


def _split_named_elements(line: str) -> list[str]:
    """Split named elements from a line."""
    pattern = re.compile(r"([A-Za-z0-9_\-]+)\s*:\s*(.*)")
    match = pattern.match(line)
    if match:
        return [match.group(1)] + match.group(2).split()
    return []


def _split_weighted_elements(line: str) -> list[str]:
    """Split elements with parentheses into separate parts."""
    pattern = re.compile(r"([A-Za-z0-9_]+)\((.*?)\)|(\S+)")
    matches = pattern.findall(line)

    result = []
    for match in matches:
        if match[0]:
            result.append(match[0])
            result.append(f"({match[1]})")
        else:
            result.append(match[2])
    return result


def slice_dat_line(line: str) -> list[str]:
    """Slice a .dat line into its components."""
    line = line.strip()
    if not line:
        return []

    if line.startswith(";"):
        return [";", line[1:].strip()]

    line = _strip_comments(line)

    named_elements = _split_named_elements(line)
    if named_elements:
        return [named_elements[0]] + _split_weighted_elements(
            " ".join(named_elements[1:])
        )

    return _split_weighted_elements(line)


def table_structure_file(
    path: Path,
) -> list[list[str]]:
    """Load the file produced by ``Data`` ``Save table to file``."""
    file_content = []
    with open(path, encoding="utf-8") as file:
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
    path : pathlib.Path
        Path to results file. It must be saved from TraceWin:
        ``Data`` > ``Save table to file``.
    prop : str
        Name of the desired property. Must be in d_property.

    Returns
    -------
    data_ref : numpy.ndarray
        Array containing the desired property.

    """
    if not path.is_file():
        logging.error("Filepath to results is incorrect.")
        raise FileNotFoundError()
        # Tk().withdraw()
        # path = Path(
        #     askopenfilename(filetypes=[("TraceWin energies file", ".txt")])
        # )

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
                new_data = np.nan
            data_ref.append(new_data)
    data_ref = np.array(data_ref).astype(float)
    return data_ref


def transfer_matrices(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load the transfer matrix as calculated by TraceWin."""
    transfer_matrices = []
    position_in_m = []
    elements_numbers = []

    with open(path, encoding="utf-8") as file:
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
