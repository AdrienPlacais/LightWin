"""Set a function to check validity of :class:`.SimulationOutput`."""

from typing import Literal

import numpy as np
from pytest import approx

from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)

_REFERENCE_RESULTS = {
    "w_kin": 502.24092,
    "phi_abs": 68510.456,
    "phi_s": -24.9933,  # with new definition
    # 'phi_s': -25.0014,   # with historical definition
    "v_cav_mv": 7.85631,
    "r_xx": np.array(
        [[+1.214036e00, -2.723429e00], [+2.090116e-01, -3.221306e-01]]
    ),
    "r_yy": np.array(
        [[-1.453483e-01, -1.022289e00], [+1.503132e-01, -1.684692e-01]]
    ),
    "r_zdelta": np.array(
        [[+4.509904e-01, -3.843910e-01], [+9.079210e-02, +3.176355e-01]]
    ),
    "r_xy": np.array([[0.0, 0.0], [0.0, 0.0]]),
    "r_xz": np.array([[0.0, 0.0], [0.0, 0.0]]),
    "r_yz": np.array([[0.0, 0.0], [0.0, 0.0]]),
    "acceptance_phi": 75.36359596,
    "acceptance_energy": 8.9766877522,
}


def wrap_approx(
    key: str,
    fix_so: SimulationOutput,
    ref_so: SimulationOutput | None = None,
    rel: float | None = None,
    abs: float | None = None,
    to_numpy: bool = False,
    to_deg: bool = True,
    elt: str | None = "last",
    pos: Literal["in", "out"] | None = "out",
    **get_kwargs,
) -> bool:
    """
    Compare ``key`` from 2 :class:`.SimulationOutput` using ``pytest.approx``.

    By default, will compare ``key`` at the exit of the last element of the
    linac.

    Parameters
    ----------
    key : str
        The name of the quantity to compare between the simulation results.
    fix_so : SimulationOutput
        The simulation results produced by the test.
    ref_so : SimulationOutput | None, optional
        The reference simulation output. If not provided, we will take ``key``
        from the reference dictionary.
    rel : float | None, optional
        Relative tolerance. The default is ``pytest.approx`` default.
    abs : float | None, optional
        Absolute tolerance. The default is ``pytest.approx`` default.
    to_numpy : bool, optional
        If the value should be converted to a numpy array. The default is
        False.
    to_deg : bool, optional
        If the value should be converted to degrees (note that this will be
        applied if ``"phi"`` is in ``key``). The default is True.
    elt : str | None, optional
        Where the comparison should be performed. If None, it will be checked
        on the whole array of values. The default is "last" (comparison on
        last element).
    pos : Literal["in", "out"] | None, optional
        Where to compare the values in the element. The default is exit of
        element.
    get_kwargs :
        Other keyword arguments passed to the ``get`` method of
        :class:`.SimulationOutput`.

    Returns
    -------
    bool
        The result of the ``pytest.approx``.

    """
    value = fix_so.get(
        key,
        to_numpy=to_numpy,
        to_deg=to_deg,
        elt=elt,
        pos=pos,
        **get_kwargs,
    )
    if ref_so is None:
        reference_value = _REFERENCE_RESULTS.get(key)
        return value == approx(reference_value, abs=abs, rel=rel)

    reference_value = ref_so.get(
        key, to_numpy=to_numpy, to_deg=to_deg, elt=elt, pos=pos, **get_kwargs
    )
    return value == approx(reference_value, abs=abs, rel=rel)
