"""Define parameters necessary to define a beam."""

import numpy as np

from lightwin.new_config.config_specs import KeyValConfSpec

BEAM_CONFIG = (
    KeyValConfSpec(
        key="e_mev",
        types=(float,),
        description=r"Energy of particle at entrance in :math:`\mathrm{MeV}",
        default_value=1.0,
    ),
    KeyValConfSpec(
        key="e_rest_mev",
        types=(float,),
        description=r"Rest energy of particle in :math:`\mathrm{MeV}`",
        default_value=0.0,
    ),
    KeyValConfSpec(
        key="f_bunch_mhz",
        types=(float,),
        description=r"Beam bunch frequency in :math:\mathrm{MHz}`",
        default_value=100.0,
    ),
    KeyValConfSpec(
        key="i_milli_a",
        types=(float,),
        description=r"Beam current in :math:`\mathrm{mA}`",
        default_value=0.0,
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="q_adim",
        types=(float,),
        description="Adimensioned charge of particle",
        default_value=1.0,
    ),
    KeyValConfSpec(
        key="sigma",
        types=(list, np.ndarray),
        description=r"Input :math:`\sigma` beam matrix in :math:`\mathrm{m}`;"
        + r" :math:`\mathrm{rad}`. Must be a list of lists of floats that can "
        + "be transformed to a 6*6 matrix.",
        default_value=[[0.0 for _ in range(6)] for _ in range(6)],
    ),
)
