"""Module to test the ``beam`` configuration entries."""

import logging

import numpy as np

from lightwin.config.helper import check_type
from lightwin.constants import c


def test(
    e_rest_mev: float,
    q_adim: float,
    e_mev: float,
    f_bunch_mhz: float,
    i_milli_a: float,
    sigma: list[list[float]],
    **kwargs,
) -> None:
    """Ensure that ``beam`` has the proper arguments with proper types."""
    check_type(
        float, "beam", e_rest_mev, q_adim, e_mev, f_bunch_mhz, i_milli_a
    )

    if abs(i_milli_a) > 1e-10:
        logging.warning(
            f"You asked a non-null beam current {i_milli_a = }mA. "
            "You should ensure that the desired BeamCalculator "
            "supports it."
        )

    check_type(
        list,
        "beam",
        sigma,
        sigma[0],
        sigma[1],
        sigma[2],
        sigma[3],
        sigma[4],
        sigma[5],
    )
    n_lines = len(sigma)
    assert n_lines == 6, f"sigma entry should have 6 lines but has {n_lines}"
    for i, col in enumerate(sigma):
        len_col = len(col)
        assert (
            len_col == 6
        ), f"sigma {i}th line should have 6 columns but has {len_col}"


def edit_configuration_dict_in_place(
    beam_kw: dict[str, float | list[list[float]]], **kwargs
) -> None:
    """Add useful values to the configuration ``beam`` dict."""
    beam_kw["sigma"] = np.array(beam_kw["sigma"])
    beam_kw["inv_e_rest_mev"] = 1.0 / beam_kw["e_rest_mev"]
    beam_kw["gamma_init"] = 1.0 + beam_kw["e_mev"] / beam_kw["e_rest_mev"]
    beam_kw["omega_0_bunch"] = 2e6 * np.pi * beam_kw["f_bunch_mhz"]
    beam_kw["lambda_bunch"] = c / beam_kw["f_bunch_mhz"]
    beam_kw["q_over_m"] = beam_kw["q_adim"] * beam_kw["inv_e_rest_mev"]
    beam_kw["m_over_q"] = 1.0 / beam_kw["q_over_m"]
