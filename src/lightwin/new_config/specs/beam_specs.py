"""Define parameters necessary to define a beam.

.. note::
    Several parameters hold the ``derived`` flag. It means that these
    quantities are calculated from other parameters by LightWin, and should not
    be handled by the user.

"""

import numpy as np

from lightwin.new_config.key_val_conf_spec import KeyValConfSpec
from lightwin.new_config.table_spec import TableConfSpec

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
    KeyValConfSpec(
        key="q_over_m",
        types=(float,),
        description="Adimensioned charge over rest mass in :unit:`MeV`",
        default_value=1.0,
        is_mandatory=False,
        derived=True,
    ),
)


class BeamTableConfSpec(TableConfSpec):
    """Set the specifications for the beam.

    We subclass :class:`.TableConfSpec` to define some keys requiring a
    specific treatment.

    """
