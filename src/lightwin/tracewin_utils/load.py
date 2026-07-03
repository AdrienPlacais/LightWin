"""Define functions to load and preprocess the TraceWin files."""

from pathlib import Path

import numpy as np
from numpy.typing import NDArray


def transfer_matrices(
    path: Path,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
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


def _transfer_matrix(lines: list[str]) -> NDArray[np.float64]:
    """Load a single element transfer matrix."""
    transfer_matrix = np.empty((6, 6), dtype=float)
    for i, line in enumerate(lines):
        transfer_matrix[i] = np.array(line.split(), dtype=float)
    return transfer_matrix
