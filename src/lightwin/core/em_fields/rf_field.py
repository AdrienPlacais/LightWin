"""Hold parameters that are shared by all cavities of same type.

See Also
--------
:class:`.CavitySettings`

"""

import cmath
from functools import partial
from typing import Any

from lightwin.core.em_fields.helper import (
    FieldFuncComponent1D,
    null_field_1d,
    shifted_e_spat,
)


def compute_param_cav(integrated_field: complex) -> dict[str, float]:
    """Compute synchronous phase and accelerating field."""
    polar_itg = cmath.polar(integrated_field)
    cav_params = {"v_cav_mv": polar_itg[0], "phi_s": polar_itg[1]}
    return cav_params


class RfField:
    r"""Cos-like RF field.

    Warning, all phases are defined as:

    .. math::
        \phi = \omega_0^{rf} t

    While in the rest of the code it is defined as:

    .. math::
        \phi = \omega_0_^{bunch} t

    All phases are stored in radian.

    Parameters
    ----------
    e_spat : Callable[[float], float]
        Spatial component of the electric field. Needs to be multiplied by the
        :math:`\cos(\omega t)` to have the full electric field. Initialized to
        null function.
    n_cell : int
        Number of cells in the cavity.
    n_z : int | None
        Number of points in the file that gives ``e_spat``, the spatial
        component of the electric field.

    """

    def __init__(self, section_idx: int) -> None:
        """Instantiate object."""
        self._original_e_spat: FieldFuncComponent1D
        self.e_spat: FieldFuncComponent1D = null_field_1d
        self.n_cell: int
        self.n_z: int
        self.is_loaded = False
        self.starting_position: float
        self.section_idx: int = section_idx

    def has(self, key: str) -> bool:
        """Tell if the required attribute is in this class."""
        return hasattr(self, key)

    def get(self, *keys: str, **kwargs: bool | str | None) -> Any:
        """Shorthand to get attributes from this class or its attributes.

        Parameters
        ----------
        *keys : str
            Name of the desired attributes.
        **kwargs : bool | str | None
            Other arguments passed to recursive getter.

        Returns
        -------
        out : Any
            Attribute(s) value(s).

        """
        val: dict[str, Any] = {key: [] for key in keys}

        for key in keys:
            if not self.has(key):
                val[key] = None
                continue

            val[key] = getattr(self, key)

        out = [val[key] for key in keys]
        if len(keys) == 1:
            return out[0]
        return tuple(out)

    def set_e_spat(self, e_spat: FieldFuncComponent1D, n_cell: int) -> None:
        """Set the pos. component of electric field, set number of cells."""
        self.e_spat = e_spat
        self.n_cell = n_cell
        self.is_loaded = True

    def shift(self) -> None:
        """Shift the electric field map.

        .. warning::
            You must ensure that for ``z < 0`` and ``z > element.length_m`` the
            electric field is null. Interpolation can lead to funny results!

        """
        assert hasattr(
            self, "starting_position"
        ), "You need to set the starting_position attribute of the RfField."
        if not hasattr(self, "_original_e_spat"):
            self._original_e_spat = self.e_spat
        self.e_spat = partial(
            shifted_e_spat, e_spat=self.e_spat, z_shift=self.starting_position
        )
