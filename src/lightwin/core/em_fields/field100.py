"""Define the rf field corresponding to ``FIELD_MAP 100``.

This is 1D longitudinal field along ``z``. The only one that is completely
implemented for now.

"""

from pathlib import Path

from lightwin.core.em_fields.field import Field
from lightwin.core.em_fields.field_helpers import (
    create_1d_field_func,
    e_1d,
    e_1d_complex,
    rescale_array,
    shifted_e_spat,
)
from lightwin.core.em_fields.types import (
    FieldFuncComplexTimedComponent1D,
    FieldFuncComponent1D,
    FieldFuncTimedComponent1D,
    Pos1D,
)
from lightwin.tracewin_utils.field_map_loaders import (
    is_a_valid_1d_electric_field,
    load_field_1d,
)


class Field100(Field):
    """Define a RF field, 1D longitudinal."""

    extensions = (".edz",)
    is_implemented = True

    def _load_fieldmap(
        self, path: Path, **validity_check_kwargs
    ) -> tuple[FieldFuncComponent1D, tuple[int], int]:
        r"""Load a 1D field (``EDZ`` extension).

        Parameters
        ----------
        path :
            The path to the ``EDZ`` file to load.

        Returns
        -------
        e_z :
            Function that takes in ``z`` position and returns corresponding
            field, at null phase, for amplitude of :math:`1\,\mathrm{MV/m}`.
        n_z :
            Number of interpolation points.
        n_cell :
            Number of cell for cavities.

        """
        n_z, zmax, norm, f_z, n_cell = load_field_1d(path)

        assert is_a_valid_1d_electric_field(
            n_z, zmax, f_z, self._length_m
        ), f"Error loading {path}'s field map."

        f_z = rescale_array(f_z, norm)
        e_z = create_1d_field_func(f_z, zmax, n_z)
        return e_z, (n_z,), n_cell

    def shift(self) -> None:
        """Shift the electric field map.

        .. warning::
            You must ensure that for ``z < 0`` and ``z > element.length_m`` the
            electric field is null. Interpolation can lead to funny results!

        """
        assert hasattr(
            self, "z_0"
        ), "You need to set the starting_position attribute of the Field."
        shifted = shifted_e_spat(self._e_z_spat_rf, z_shift=self.z_0)
        self._e_z_spat_rf = shifted

    def e_z_functions(
        self, amplitude: float, phi_0_rel: float
    ) -> tuple[FieldFuncComplexTimedComponent1D, FieldFuncTimedComponent1D]:
        """Generate a function for longitudinal transfer matrix calculation.

        .. warnign::
            Currently, if ``flag_cython`` is set to True, the returned
            functions

        """
        if self.flag_cython:
            from lightwin.core.em_fields.cy_field_helpers import (
                ComplexEzFuncCython,
                RealEzFuncCython,
            )

            return (
                ComplexEzFuncCython(
                    self._e_z_spat_rf.xp,
                    self._e_z_spat_rf.fp,
                    amplitude,
                    phi_0_rel,
                ),
                RealEzFuncCython(
                    self._e_z_spat_rf.xp,
                    self._e_z_spat_rf.fp,
                    amplitude,
                    phi_0_rel,
                ),
            )

        def compl(pos: Pos1D, phi: float) -> complex:
            return e_1d_complex(
                pos=pos,
                e_func=self._e_z_spat_rf,
                phi=phi,
                amplitude=amplitude,
                phi_0=phi_0_rel,
            )

        def rea(pos: Pos1D, phi: float) -> float:
            return e_1d(
                pos=pos,
                e_func=self._e_z_spat_rf,
                phi=phi,
                amplitude=amplitude,
                phi_0=phi_0_rel,
            )

        return compl, rea
