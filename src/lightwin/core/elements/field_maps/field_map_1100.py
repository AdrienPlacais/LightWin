"""Define a field map with 1D rf electro-magnetic field."""

from lightwin.core.elements.field_maps.field_map import FieldMap


class FieldMap1100(FieldMap):
    """1D rf electro-magnetic field.

    Just inherit from the classic :class:`.FieldMap`; we override the
    ``to_line`` to also update ``k_b`` (keep ``k_e == k_b``).

    """
