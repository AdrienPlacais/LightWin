"""Define a field map with 3D rf electro-magnetic field."""

from lightwin.core.elements.field_maps.field_map import FieldMap


class FieldMap7700(FieldMap):
    """3D rf electro-magnetic field.

    It is not implemented yet. It will never be supported by
    :class:`.Envelope1D`, but :class:`.Envelope3D` should be able to support it
    (one day).

    As for now, it only inherits from the :class:`.FieldMap` and does not bring
    anything new. Apart from raising a ``NotImplementedError``.

    """
