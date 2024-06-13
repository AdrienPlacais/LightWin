"""Define an object holding several :class:`.Field`."""

import functools
from collections.abc import Collection

from core.em_fields.field import AnyDimFloat, Field, FieldFuncTimedComponent


class SuperposedFields(tuple[Field, ...]):
    """Gather several electromagnetic fields."""

    def __new__(cls, fields: Collection[Field]) -> None:
        """Create the new instance."""
        super().__new__(cls, tuple(fields))

    def __init__(self, fields: Collection[Field]) -> None:
        """Instantiate object.

        .. note::
            Do not call ``super().__init__`` as ``tuple`` are immutable.

        """
        pass

    def e_z(
        self,
        pos: AnyDimFloat,
        phi: float,
        amplitudes: Collection[float],
        phi_0_rels: Collection[float],
    ) -> float:
        """Give longitudinal electric field values."""
        all_e_z = (
            field.e_z(pos, phi, amplitude, phi_0_rel)
            for field, amplitude, phi_0_rel in zip(
                self, amplitudes, phi_0_rels, strict=True
            )
        )
        return sum(all_e_z)

    def generate_e_z_with_settings(
        self, amplitudes: Collection[float], phi_0_rels: Collection[float]
    ) -> FieldFuncTimedComponent:
        """Generate a function for a transfer matrix calculation."""
        return functools.partial(
            self.e_z, amplitudes=amplitudes, phi_0_rels=phi_0_rels
        )
