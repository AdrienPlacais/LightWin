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

    def __init__(
        self,
        fields: Collection[Field],
        length_m: float = 0.0,
        z_0: float = 0.0,
    ) -> None:
        """
        Initialize the :class:`SuperposedField`.

        Parameters
        ----------
        fields : Collection[Field]
            A collection of :class:`.Field` instances.
        length_m : float, optional
            The total length of the field in meters. Defaults to 0.0.
        z_0 : float, optional
            The initial z-position. Defaults to 0.0.

        """
        dummy_path = Path("dummy")
        super().__init__(field_map_path=dummy_path, length_m=length_m, z_0=z_0)
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
        pos: Any,
        phi: float,
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
        def compl_combined(*args, **kwargs):
            return sum(func(*args, **kwargs) for func in compl_funcs)

        def rea_combined(*args, **kwargs):
            return sum(func(*args, **kwargs) for func in rea_funcs)

        return compl_combined, rea_combined

    def shift(self) -> None:
        """Shift the field maps. Not applicable for :class:`SuperposedField`."""
        pass
