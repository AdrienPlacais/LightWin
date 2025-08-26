"""Define an equivalent to TraceWin's FIELD_MAP.

.. note::
    For now, we expect that coordinates are always cartesian.

.. todo::
    Define a FieldMapLoader function to easily choose between binary/ascii file
    format.

.. todo::
    Should have a omega0_rf attribute

See Also
--------
:class:`.CavitySettings`

"""

import functools
import logging
import math
from abc import ABC, abstractmethod
from collections.abc import Callable, Collection
from pathlib import Path
from typing import Any, Literal, overload

from lightwin.core.em_fields.field_helpers import null_field_1d
from lightwin.core.em_fields.types import (
    FieldFuncComplexTimedComponent,
    FieldFuncPhisFit,
)

EXTENSION_TO_COMPONENT = {
    ".edx": "_e_x_spat_rf",
    ".edy": "_e_y_spat_rf",
    ".edz": "_e_z_spat_rf",
    ".bdx": "_b_x_spat_rf",
    ".bdy": "_b_y_spat_rf",
    ".bdz": "_b_z_spat_rf",
    ".esx": "_e_x_dc",
    ".esy": "_e_y_dc",
    ".esz": "_e_z_dc",
    ".bsx": "_b_x_dc",
    ".bsy": "_b_y_dc",
    ".bsz": "_b_z_dc",
}


class Field(ABC):
    r"""Generic electro-magnetic field.

    This object can be shared by several :class:`.Element` and we create as few
    as possible.

    """

    extensions: Collection[str]
    is_implemented: bool

    def __init__(
        self, field_map_path: Path, length_m: float, z_0: float = 0.0
    ) -> None:
        """Instantiate object."""
        self.field_map_path = field_map_path
        self._length_m = length_m
        self.n_cell: int
        self.n_z: int
        self.is_loaded = False

        # Used in SUPERPOSED_MAP to shift a field
        self.z_0: float = z_0

        # Where we store interpolated field maps (to multiply by cos phi)
        self._e_x_spat_rf: Callable[[Any], float] = null_field_1d
        self._e_y_spat_rf: Callable[[Any], float] = null_field_1d
        self._e_z_spat_rf: Callable[[Any], float] = null_field_1d
        self._b_x_spat_rf: Callable[[Any], float] = null_field_1d
        self._b_y_spat_rf: Callable[[Any], float] = null_field_1d
        self._b_z_spat_rf: Callable[[Any], float] = null_field_1d

        # Where we store static field maps (no phase anyway)
        self._e_x_dc: Callable[[Any], float] = null_field_1d
        self._e_y_dc: Callable[[Any], float] = null_field_1d
        self._e_z_dc: Callable[[Any], float] = null_field_1d
        self._b_x_dc: Callable[[Any], float] = null_field_1d
        self._b_y_dc: Callable[[Any], float] = null_field_1d
        self._b_z_dc: Callable[[Any], float] = null_field_1d

        if not self.is_implemented:
            logging.warning(
                "Initializing a non-implemented Field. Not loading anything."
            )
            return

        self.load_fieldmaps()
        if self.z_0:
            self.shift()

    def __repr__(self) -> str:
        """Print out class name and associated field map path."""
        return f"{self.__class__.__name__:>10} | {self.field_map_path.name}"

    def load_fieldmaps(self) -> None:
        """Load all field components for class :attr:`extensions`."""
        for ext in self.extensions:
            path = self.field_map_path.parent / (
                self.field_map_path.name + ext
            )
            func, n_interp, n_cell = self._load_fieldmap(path)
            attribute_name = EXTENSION_TO_COMPONENT[ext]
            setattr(self, attribute_name, func)

            if ext == ".edz":
                self._patch_to_keep_consistency(n_interp, n_cell)
        self.is_loaded = True

    @abstractmethod
    def _load_fieldmap(
        self,
        path: Path,
        **validity_check_kwargs,
    ) -> tuple[Callable[..., float], Any, int]:
        """Generate field function corresponding to a single field file.

        Parameters
        ----------
        path :
            Path to a field map file.

        Returns
        -------
        func :
            Give field at a given position, position being a tuple of 1, 2 or 3
            floats.
        n_interp :
            Number of interpolation points in the various directions (tuple of
            1, 2 or 3 integers).
        n_cell :
            Number of cells (makes sense only for .edz as for now).

        """
        ...

    @overload
    def _calculate_field(
        self,
        component_func: Callable[..., float],
        pos: Any,
        phi: float,
        amplitude: float,
        phi_0_rel: float,
        *,
        complex_output: Literal[True],
    ) -> complex: ...

    @overload
    def _calculate_field(
        self,
        component_func: Callable[..., float],
        pos: Any,
        phi: float,
        amplitude: float,
        phi_0_rel: float,
        *,
        complex_output: Literal[False],
    ) -> float: ...

    def _calculate_field(
        self,
        component_func: Callable[..., float],
        pos: Any,
        phi: float,
        amplitude: float,
        phi_0_rel: float,
        *,
        complex_output: bool = True,
    ) -> complex | float:
        """Calculate the field component value.

        Parameters
        ----------
        component_func :
            The spatial field component function (e.g., self._e_x_spat_rf).
            Must accept a tuple of 1 to 3 floats (position) and return a float.
        pos :
            The position at which to evaluate the field.
        phi :
            The phase angle.
        amplitude :
            The amplitude of the field.
        phi_0_rel :
            The relative phase offset.
        complex_output :
            Whether to return a complex value. Defaults to True.

        Returns
        -------
            The calculated field value.

        """
        field_value = amplitude * component_func(pos)
        phase = phi + phi_0_rel
        if complex_output:
            return field_value * (math.cos(phase) + 1j * math.sin(phase))

        return field_value * math.cos(phase)

    def shift(self) -> None:
        """Shift the field maps. Used in SUPERPOSE_MAP."""
        raise NotImplementedError("Not yet implemented!")

    def e_x(
        self, pos: Any, phi: float, amplitude: float, phi_0_rel: float
    ) -> complex:
        """Give transverse x electric field value."""
        return self._calculate_field(
            self._e_x_spat_rf,
            pos,
            phi,
            amplitude,
            phi_0_rel,
            complex_output=True,
        )

    def e_y(
        self, pos: Any, phi: float, amplitude: float, phi_0_rel: float
    ) -> complex:
        """Give transverse y electric field value."""
        return self._calculate_field(
            self._e_y_spat_rf,
            pos,
            phi,
            amplitude,
            phi_0_rel,
            complex_output=True,
        )

    def e_z(
        self, pos: Any, phi: float, amplitude: float, phi_0_rel: float
    ) -> complex:
        """Give longitudinal electric field value."""
        return self._calculate_field(
            self._e_z_spat_rf,
            pos,
            phi,
            amplitude,
            phi_0_rel,
            complex_output=True,
        )

    def b_x(
        self, pos: Any, phi: float, amplitude: float, phi_0_rel: float
    ) -> complex:
        """Give transverse x magnetic field value."""
        return self._calculate_field(
            self._b_x_spat_rf,
            pos,
            phi,
            amplitude,
            phi_0_rel,
            complex_output=True,
        )

    def b_y(
        self, pos: Any, phi: float, amplitude: float, phi_0_rel: float
    ) -> complex:
        """Give transverse y magnetic field value."""
        return self._calculate_field(
            self._b_y_spat_rf,
            pos,
            phi,
            amplitude,
            phi_0_rel,
            complex_output=True,
        )

    def b_z(
        self, pos: Any, phi: float, amplitude: float, phi_0_rel: float
    ) -> complex:
        """Give longitudinal magnetic field value."""
        return self._calculate_field(
            self._b_z_spat_rf,
            pos,
            phi,
            amplitude,
            phi_0_rel,
            complex_output=True,
        )

    def partial_e_z(
        self, amplitude: float, phi_0_rel: float
    ) -> FieldFuncComplexTimedComponent:
        """Generate a function for longitudinal transfer matrix calculation."""
        return functools.partial(
            self.e_z, amplitude=amplitude, phi_0_rel=phi_0_rel
        )

    def partial_e_z_phis_fit(self, amplitude: float) -> FieldFuncPhisFit:
        """Generate a function for longitudinal transfer matrix calculation."""
        return functools.partial(self.e_z, amplitude=amplitude)

    def _patch_to_keep_consistency(self, n_interp: Any, n_cell: int) -> None:
        """Save ``n_cell`` and ``n_z``. Temporary solution."""
        if not (isinstance(n_interp, tuple) and len(n_interp) == 1):
            raise ValueError(f"{n_interp = } but should be a 1D tuple.")
        self.n_z = n_interp[0]
        self.n_cell = n_cell
