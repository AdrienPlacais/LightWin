"""Define an object holding several :class:`.Field`."""

import functools
from collections.abc import Collection
from typing import Self

from lightwin.core.em_fields.field import Field
from lightwin.core.em_fields.types import (
    FieldFuncComplexTimedComponent,
    PosAnyDim,
)


class SuperposedFields(tuple[Field, ...]):
    """Gather several electromagnetic fields."""

    def __new__(cls, fields: Collection[Field]) -> Self:
        """Create the new instance."""
        return super().__new__(cls, tuple(fields))

    def e_z(
        self,
        pos: PosAnyDim,
        phi: float,
        amplitudes: Collection[float],
        phi_0_rels: Collection[float],
    ) -> complex:
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
    ) -> FieldFuncComplexTimedComponent:
        """Generate a function for a transfer matrix calculation."""
        return functools.partial(
            self.e_z, amplitudes=amplitudes, phi_0_rels=phi_0_rels
        )
