"""Define various functions.

.. todo::
    Clean this, a lot of old things that may not be used.

.. todo::
    Ellipse plot could be better

"""

import logging
import os

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.util import helper


# TODO modernize
def compute_error_transfer_matrix(
    t_m: np.ndarray, t_m_ref: np.ndarray, output: bool = False
) -> tuple[np.ndarray, np.ndarray]:
    """Compute and output error between transfer matrix and ref."""
    n_z = t_m.shape[0]
    n_z_ref = t_m_ref.shape[0]

    # We calculate error by interpolating the tab with most points on the one
    # with least points.
    kind = "linear"
    bounds_error = False
    fill_value = "extrapolate"

    if n_z < n_z_ref:
        z_err = t_m[:, 0]
        err = np.full((n_z, 4), np.nan)
        for i in range(4):
            f_interp = interp1d(
                x=t_m_ref[:, 0],
                y=t_m_ref[:, i + 1],
                kind=kind,
                bounds_error=bounds_error,
                fill_value=fill_value,
            )
            err[:, i] = f_interp(z_err) - t_m[:, i + 1]

    else:
        z_err = t_m_ref[:, 0]
        err = np.full((n_z_ref, 4), np.nan)
        for i in range(4):
            f_interp = interp1d(
                x=t_m[:, 0],
                y=t_m[:, i + 1],
                kind=kind,
                bounds_error=bounds_error,
                fill_value=fill_value,
            )
            err[:, i] = t_m_ref[:, i + 1] - f_interp(z_err)

    if output:
        header = "Errors on transfer matrix"
        message = f"""
            Error matrix at end of line*1e3:
            {err[-1, 0:2] * 1e3}
            {err[-1, 2:4] * 1e3}

            Cumulated error:
            {np.linalg.norm(err, axis=0)[0:2]}
            {np.linalg.norm(err, axis=0)[2:4]}

            Cumulated error:
            {np.linalg.norm(err, axis=0)[0:2]}
            {np.linalg.norm(err, axis=0)[2:4]}

            Tot error:
            {np.linalg.norm(err)}
            """
        logging.info(helper.pd_output(message, header=header))
    return err, z_err


def load_phase_space(accelerator: Accelerator) -> list[np.ndarray]:
    """Load Partran phase-space data.

    Phase-space files are obtained with:
        Input data & Beam: Partran
        Phase spaces or beam distributions: Output at element n
        Then save all particle as ASCII.

    """
    folder = os.path.join(
        accelerator.get("project_folder"), "results/phase_space/"
    )
    file_type = ["txt"]
    file_list = []

    for file in os.listdir(folder):
        if file.split(".")[-1] in file_type:
            file_list.append(folder + file)
    file_list.sort()

    partran_data = []
    dtype = {
        "names": (
            "x(mm)",
            "x'(mrad)",
            "y(mm)",
            "y'(mrad)",
            "z(mm)",
            "z'(mrad)",
            "Phase(deg)",
            "Time(s)",
            "Energy(MeV)",
            "Loss",
        ),
        "formats": (
            "f8",
            "f8",
            "f8",
            "f8",
            "f8",
            "f8",
            "f8",
            "f8",
            "f8",
            "i4",
        ),
    }
    for file in file_list:
        partran_data.append(np.loadtxt(file, skiprows=3, dtype=dtype))

    return partran_data


def _create_output_fit_dicts() -> dict[str, dict]:
    col = ("Name", "Status", "Min.", "Max.", "Fixed", "Orig.", "(var %)")
    d_pd = {
        "phi_0_rel": pd.DataFrame(columns=col),
        "phi_0_abs": pd.DataFrame(columns=col),
        "k_e": pd.DataFrame(columns=col),
    }
    # Hypothesis: the first guesses for the phases are the phases of the
    # reference cavities
    d_x_lim = {
        "phi_0_rel": lambda f, i: [
            np.rad2deg(f.info["X_lim"][0][i]),
            np.rad2deg(f.info["X_lim"][1][i]),
        ],
        "phi_0_abs": lambda f, i: [
            np.rad2deg(f.info["X_lim"][0][i]),
            np.rad2deg(f.info["X_lim"][1][i]),
        ],
        "k_e": lambda f, i: [
            f.info["X_lim"][0][i + len(f.comp["l_cav"])],
            f.info["X_lim"][1][i + len(f.comp["l_cav"])],
        ],
    }

    all_dicts = {"d_pd": d_pd, "d_X_lim": d_x_lim}

    return all_dicts
