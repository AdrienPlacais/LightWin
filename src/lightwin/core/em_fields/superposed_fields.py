"""Define an object holding several :class:`.Field`."""

from collections.abc import Collection
from pathlib import Path
from typing import Any

from lightwin.core.em_fields.field import Field
from lightwin.core.em_fields.types import (
    FieldFuncComplexTimedComponent,
    FieldFuncTimedComponent,
)


class SuperposedFields(Field):
    """This object gathers several :class:`.Field` instances."""

    is_implemented = True
    extensions = ()

    def __init__(
        self,
        fields: Collection[Field],
        length_m: float = 0.0,
        z_0: float = 0.0,
    ) -> None:
        """Initialize the :class:`SuperposedFields`.

        Parameters
        ----------
        fields :
            A collection of :class:`.Field` instances.
        length_m :
            The total length of the field in meters.
        z_0 :
            The initial z-position.

        """
        folder, filename = Path("dummy"), "dummy"
        super().__init__(
            folder=folder, filename=filename, length_m=length_m, z_0=z_0
        )
        self._fields = tuple(fields)
        self.is_loaded = True  # No field maps to load in SuperposedField

    def _load_fieldmap(self, path: Path, **kwargs) -> tuple[Any, Any, int]:
        """Do not do anything."""
        pass

    def _params(
        self, amplitudes: Collection[float], phi_0_rels: Collection[float]
    ) -> zip:
        """Gather all the parameters for a field calculation."""
        return zip(self._fields, amplitudes, phi_0_rels, strict=True)

    def e_x(  # type: ignore
        self,
        pos: Any,
        phi: float,
        amplitudes: Collection[float],
        phi_0_rels: Collection[float],
    ) -> complex:
        """Sum the e_x components from all :class:`.Field` instances at position ``pos``."""
        return sum(
            field.e_x(pos, phi, amplitude, phi_0_rel)
            for field, amplitude, phi_0_rel in self._params(
                amplitudes, phi_0_rels
            )
        )

    def e_y(  # type: ignore
        self,
        pos: Any,
        phi: float,
        amplitudes: Collection[float],
        phi_0_rels: Collection[float],
    ) -> complex:
        """Sum the e_y components from all :class:`.Field` instances at position ``pos``."""
        return sum(
            field.e_y(pos, phi, amplitude, phi_0_rel)
            for field, amplitude, phi_0_rel in self._params(
                amplitudes, phi_0_rels
            )
        )

    def e_z(  # type: ignore
        self,
        pos: Any,
        phi: float,
        amplitudes: Collection[float],
        phi_0_rels: Collection[float],
        complex_output: bool = True,
    ) -> complex | float:
        """Sum the e_z components from all :class:`.Field` instances at position ``pos``."""
        return sum(
            field.e_z(
                pos,
                phi,
                amplitude,
                phi_0_rel,
                complex_output=complex_output,
            )
            for field, amplitude, phi_0_rel in self._params(
                amplitudes, phi_0_rels
            )
        )

    def b_x(  # type: ignore
        self,
        pos: Any,
        phi: float,
        amplitudes: Collection[float],
        phi_0_rels: Collection[float],
    ) -> complex:
        """Sum the b_x components from all :class:`.Field` instances at position ``pos``."""
        return sum(
            field.b_x(pos, phi, amplitude, phi_0_rel)
            for field, amplitude, phi_0_rel in self._params(
                amplitudes, phi_0_rels
            )
        )

    def b_y(  # type: ignore
        self,
        pos: Any,
        phi: float,
        amplitudes: Collection[float],
        phi_0_rels: Collection[float],
    ) -> complex:
        """Sum the b_y components from all :class:`.Field` instances at position ``pos``."""
        return sum(
            field.b_y(pos, phi, amplitude, phi_0_rel)
            for field, amplitude, phi_0_rel in self._params(
                amplitudes, phi_0_rels
            )
        )

    def b_z(  # type: ignore
        self,
        pos: Any,
        phi: float,
        amplitudes: Collection[float],
        phi_0_rels: Collection[float],
    ) -> complex:
        """Sum the b_z components from all :class:`.Field` instances at position ``pos``."""
        return sum(
            field.b_z(pos, phi, amplitude, phi_0_rel)
            for field, amplitude, phi_0_rel in self._params(
                amplitudes, phi_0_rels
            )
        )

    def partial_e_z(  # type: ignore
        self,
        amplitudes: Collection[float],
        phi_0_rels: Collection[float],
    ) -> tuple[FieldFuncComplexTimedComponent, FieldFuncTimedComponent]:
        """Generate functions for longitudinal transfer matrix calculation."""
        compl_funcs = []
        rea_funcs = []
        for field, amplitude, phi_0_rel in self._params(
            amplitudes, phi_0_rels
        ):
            compl, rea = field.partial_e_z(amplitude, phi_0_rel)
            compl_funcs.append(compl)
            rea_funcs.append(rea)

        # Combine the partial functions into one that sums all contributions
        def compl_combined(pos: Any, phase: float) -> complex:
            return sum(func(pos, phase) for func in compl_funcs)

        def rea_combined(pos: Any, phase: float) -> float:
            return sum(func(pos, phase) for func in rea_funcs)

        return compl_combined, rea_combined

    def shift(self) -> None:
        """Shift the field maps. Not applicable for :class:`SuperposedFields`."""
        pass
