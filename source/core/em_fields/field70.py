"""Define the dc field corresponding to ``FIELD_MAP 70``.

This is 3D magnetic field along. Not really implemented as 3D field maps is not
implemented, but can serve as a place holder for non-accelerating fields.

"""

from core.em_fields.field import Field


class Field70(Field):
    """Define a RF field, 1D longitudinal."""

    extensions = (".bsx", ".bsy", ".bsz")
    is_implemented = False

    def b_x(
        self,
        pos: tuple[float, float, float],
        phi: float,
        amplitude: float,
        phi_0_rel: float,
    ) -> float:
        """Give magnetic field value."""
        return amplitude * self._b_x_dc(pos)

    def b_y(
        self,
        pos: tuple[float, float, float],
        phi: float,
        amplitude: float,
        phi_0_rel: float,
    ) -> float:
        """Give magnetic field value."""
        return amplitude * self._b_y_dc(pos)

    def b_z(
        self,
        pos: tuple[float, float, float],
        phi: float,
        amplitude: float,
        phi_0_rel: float,
    ) -> float:
        """Give magnetic field value."""
        return amplitude * self._b_z_dc(pos)
