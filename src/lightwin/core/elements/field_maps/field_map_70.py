"""Define a field map with 3D dc magnetic field."""

from typing import override

from lightwin.core.elements.field_maps.field_map import FieldMap


class FieldMap70(FieldMap):
    """3D static magnetic field.

    It is not implemented yet. It will never be supported by
    :class:`.Envelope1D`, but :class:`.Envelope3D` should be able to support it
    (one day).

    As for now, it should behave like a :class:`.Drift` for
    :class:`.Envelope1D`.

    """

    def __init__(self, *args, **kwargs) -> None:
        """Instantiate super class."""
        super().__init__(*args, **kwargs)
        self._can_be_retuned = False

    @property
    @override
    def is_accelerating(self) -> bool:
        """Tell that this cavity does not accelerate."""
        return False
