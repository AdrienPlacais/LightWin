"""Define parameters necessary to define a beam.

.. note::
    Several parameters hold the ``derived`` flag. It means that these
    quantities are calculated from other parameters by LightWin, and should not
    be handled by the user.

"""

import logging
from typing import Any

import numpy as np

from lightwin.constants import c
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
    # ========================= derived =======================================
    KeyValConfSpec(
        key="inv_e_rest_mev",
        types=(float,),
        description="Inverse of rest mass in :unit:`MeV`",
        default_value=1.0,
        is_mandatory=False,
        derived=True,
    ),
    KeyValConfSpec(
        key="gamma_init",
        types=(float,),
        description=r"Initial Lorentz :math:`\gamma` factor",
        default_value=1.0,
        is_mandatory=False,
        derived=True,
    ),
    KeyValConfSpec(
        key="omega_0_bunch",
        types=(float,),
        description=r"Bunch pulsation in :unit:`rad/s`",
        default_value=1.0,
        is_mandatory=False,
        derived=True,
    ),
    KeyValConfSpec(
        key="lambda_bunch",
        types=(float,),
        description=r"Bunch wavelength in :unit:`m`",
        default_value=1.0,
        is_mandatory=False,
        derived=True,
    ),
    KeyValConfSpec(
        key="q_over_m",
        types=(float,),
        description="Adimensioned charge over rest mass in :unit:`MeV`",
        default_value=1.0,
        is_mandatory=False,
        derived=True,
    ),
    KeyValConfSpec(
        key="m_over_q",
        types=(float,),
        description="Rest mass in :unit:`MeV` over adimensioned charge ",
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

    def _pre_treat(self, toml_subdict: dict[str, Any]) -> None:
        """Edit some values, create new ones."""
        super()._pre_treat(toml_subdict)
        if not hasattr(self, "specs_as_dict"):
            raise AttributeError(
                "You must call the _set_specs_as_dict method before calling "
                "this."
            )

        toml_subdict["sigma"] = np.array(toml_subdict["sigma"])
        toml_subdict["inv_e_rest_mev"] = 1.0 / toml_subdict["e_rest_mev"]
        toml_subdict["gamma_init"] = (
            1.0 + toml_subdict["e_mev"] / toml_subdict["e_rest_mev"]
        )
        toml_subdict["omega_0_bunch"] = (
            2e6 * np.pi * toml_subdict["f_bunch_mhz"]
        )
        toml_subdict["lambda_bunch"] = c / toml_subdict["f_bunch_mhz"]
        toml_subdict["q_over_m"] = (
            toml_subdict["q_adim"] * toml_subdict["inv_e_rest_mev"]
        )
        toml_subdict["m_over_q"] = (
            toml_subdict["e_rest_mev"] / toml_subdict["q_adim"]
        )

    def validate(self, toml_subdict: dict[str, Any], **kwargs) -> bool:
        """Add some other validations to the default ones."""
        self._pre_treat(toml_subdict)
        default_tests = super().validate(toml_subdict, **kwargs)

        if i_milli_a := toml_subdict["i_milli_a"] > 1e-10:
            logging.warning(
                f"You asked a non-null beam current {i_milli_a = }mA. You "
                "should ensure that the desired BeamCalculator supports "
                "space-charge."
            )

        sigma_shape_is_ok = True
        sigma_shape = toml_subdict["sigma"].shape
        if sigma_shape != (6, 6):
            sigma_shape_is_ok = False
            logging.error(
                "The sigma matrix should have shape (6, 6), but has "
                f"{sigma_shape}"
            )

        return default_tests and sigma_shape_is_ok
