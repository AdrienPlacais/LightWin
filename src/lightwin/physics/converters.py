"""All functions to change units.

.. todo::
    The eps_phiw is not correct. Does not match TraceWin (even if what I
    compute seems right). Check the zdelta -> phiw conversion.

"""

import numpy as np
from numpy.typing import NDArray

from lightwin.constants import c


def position(
    pos_in: float | NDArray,
    beta: float | NDArray,
    key: str,
    omega_0_bunch: float,
    **beam_kwargs,
) -> float | NDArray:
    """Phase/position converters."""
    conversion_functions = {
        "z to phi": lambda pos, bet: -omega_0_bunch * pos / (bet * c),
        "phi to z": lambda pos, bet: -pos * bet * c / omega_0_bunch,
    }
    return conversion_functions[key](pos_in, beta)


def energy(
    energy_in: float | NDArray,
    key: str,
    q_over_m: float,
    m_over_q: float,
    e_rest_mev: float,
    **beam_kwargs,
) -> float | NDArray:
    """Convert energy or Lorentz factor into another related quantity.

    .. todo::
       ``q_over_m`` and ``m_over_q`` should not be mandatory arguments if they
       are not always used.

    """
    conversion_functions = {
        "v to kin": lambda x: 0.5 * m_over_q * x**2 * 1e-6,
        "kin to v": lambda x: np.sqrt(2e6 * q_over_m * x),
        "kin to gamma": lambda x: 1.0 + x / e_rest_mev,
        "gamma to kin": lambda x: e_rest_mev * (x - 1.0),
        "beta to gamma": lambda x: 1.0 / np.sqrt(1.0 - x**2),
        "gamma to beta": lambda x: np.sqrt(1.0 - x**-2),
        "kin to beta": lambda x: np.sqrt(
            1.0 - (e_rest_mev / (x + e_rest_mev)) ** 2
        ),
        "beta to kin": lambda _: None,
        "kin to p": lambda x: np.sqrt((x + e_rest_mev) ** 2 - e_rest_mev**2),
        "p to kin": lambda x: np.sqrt(x**2 + e_rest_mev**2) - e_rest_mev,
        "gamma to p": lambda x: x * np.sqrt(1.0 - x**-2) * e_rest_mev,
        "beta to p": lambda x: x / np.sqrt(1.0 - x**2) * e_rest_mev,
    }
    energy_out = conversion_functions[key](energy_in)
    return energy_out


def longitudinal(
    long_in: float | NDArray,
    ene: float | NDArray,
    key: str,
    e_rest_mev: float,
    **beam_kwargs,
) -> float | NDArray:
    """Convert energies between longitudinal phase spaces."""
    conversion_functions = {
        "zprime gamma to zdelta": lambda zp, gam: zp * gam**-2 * 1e-1,
        "zprime kin to zdelta": lambda zp, kin: zp
        * (1.0 + kin / e_rest_mev) ** -2
        * 1e-1,
    }
    return conversion_functions[key](long_in, ene)


# TODO may be possible to save some operations by using lambda func?
def emittance(
    eps_orig: float | NDArray,
    key: str,
    gamma_kin: float | NDArray,
    beta_kin: float | NDArray,
    lambda_bunch: float | NDArray,
    e_rest_mev: float | NDArray,
    **beam_kwargs,
) -> float | NDArray:
    """Convert emittance from a phase space to another, or handle norm."""
    k_1 = 360.0 * e_rest_mev / lambda_bunch
    k_2 = gamma_kin * beta_kin
    k_3 = k_2 * gamma_kin**2

    conversion_constants = {
        "z to zdelta": 0.1,
        "zdelta to z": 10.0,
        "phiw to z": 1.0 / k_1,
        "z to phiw": k_1,
        "phiw to zdelta": 0.1 / k_1,
        "zdelta to phiw": 10 * k_1,
        "normalize zdelta": k_2,
        "de-normalize zdelta": 1.0 / k_2,
        "normalize z": k_2,
        "de-normalize z": 1.0 / k_2,
        "normalize phiw": k_3,
        "de-normalize phiw": 1.0 / k_3,
        "normalize x": k_2,
        "de-normalize x": 1.0 / k_2,
        "normalize y": k_2,
        "de-normalize y": 1.0 / k_2,
        "normalize x99": k_2,
        "de-normalize x99": 1.0 / k_2,
        "normalize y99": k_2,
        "de-normalize y99": 1.0 / k_2,
    }
    eps_new = eps_orig * conversion_constants[key]
    return eps_new


def twiss(
    twiss_orig: NDArray,
    gamma_kin: float | NDArray,
    key: str,
    lambda_bunch: float | NDArray,
    e_rest_mev: float | NDArray,
    beta_kin: float | NDArray | None = None,
    **beam_kwargs,
) -> NDArray:
    """Convert Twiss array from a phase space to another."""
    if beta_kin is None:
        beta_kin = np.sqrt(1.0 - gamma_kin**-2)

    # Lighten the dict
    k_1 = e_rest_mev * (gamma_kin * beta_kin) * lambda_bunch / 360.0
    k_2 = k_1 * beta_kin**2
    k_3 = k_2 * gamma_kin**2

    conversion_constants = {
        "phiw to z": [-1.0, 1e-6 * k_3],
        "z to phiw": [-1.0, 1e6 / k_3],
        "phiw to zdelta": [-1.0, 1e-5 * k_2],
        "zdelta to phiw": [-1.0, 1e5 / k_2],
        "z to zdelta": [1.0, 1e1 * gamma_kin**-2],
        "zdelta to z": [1.0, 1e-1 * gamma_kin**2],
    }
    factors = conversion_constants[key]

    # New array of Twiss parameters in the desired phase space
    twiss_new = np.empty(twiss_orig.shape)
    twiss_new[:, 0] = twiss_orig[:, 0] * factors[0]
    twiss_new[:, 1] = twiss_orig[:, 1] * factors[1]
    twiss_new[:, 2] = twiss_orig[:, 2] / factors[1]
    return twiss_new
