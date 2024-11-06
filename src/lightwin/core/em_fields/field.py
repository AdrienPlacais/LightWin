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
from typing import Any

import numpy as np
import pandas as pd

from lightwin.core.em_fields.field_helpers import null_field_1d
from lightwin.core.em_fields.types import (
    FieldFuncComplexTimedComponent,
    FieldFuncTimedComponent,
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
        self, folder: Path, filename: str, length_m: float, z_0: float = 0.0
    ) -> None:
        """Instantiate object.

        Parameters
        ----------
        folder : Path
            Where the field map files are.
        filename : str
            The base name of the field map file(s), without extension (as
            in the ``FIELD_MAP`` command).
        length_m : float
            Length of the field map.
        z_0 : float
            Position of the field map. Used with superpose.

        """
        self.folder = folder
        self.filename = filename
        self._length_m = length_m
        self.n_cell: int = 1
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
            logging.info(
                "Initializing a non-implemented Field. Not loading anything.\n"
                f"{repr(self)}"
            )
            return

        self.load_fieldmaps()
        if self.z_0:
            self.shift()

    def __repr__(self) -> str:
        """Print out class name and associated field map path."""
        return f"{self.__class__.__name__:>10} | {self.folder.name}"

    def load_fieldmaps(self) -> None:
        """Load all field components for class :attr:`extensions`."""
        for ext in self.extensions:
            filepath = self.folder / (self.filename + ext)
            func, n_interp, n_cell = self._load_fieldmap(filepath)
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
        path : pathlib.Path
            Path to a field map file.

        Returns
        -------
        func : Callable[..., float]
            Give field at a given position, position being a tuple of 1, 2 or 3
            floats.
        n_interp : Any
            Number of interpolation points in the various directions (tuple of
            1, 2 or 3 integers).
        n_cell : int
            Number of cells (makes sense only for .edz as for now).

        """
        ...

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
        component_func : Callable[..., float]
            The spatial field component function (e.g., self._e_x_spat_rf).
            Must accept a tuple of 1 to 3 floats (position) and return a float.
        pos : Any
            The position at which to evaluate the field.
        phi : float
            The phase angle.
        amplitude : float
            The amplitude of the field.
        phi_0_rel : float
            The relative phase offset.
        complex_output : bool, optional
            Whether to return a complex value. Defaults to True.

        Returns
        -------
        complex | float
            The calculated field value.
        """
        phase = phi + phi_0_rel
        field_value = amplitude * component_func(pos) * math.cos(phase)
        if complex_output:
            return field_value * (1.0 + 1j * math.tan(phase))
        return field_value

    def shift(self) -> None:
        """Shift the field maps. Used in SUPERPOSE_MAP."""
        raise NotImplementedError(
            "This should be implemented for every Field object. The idea is "
            "simply to offset the z variable, which depends on the length of "
            "the ``pos`` vector."
        )

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
        self,
        pos: Any,
        phi: float,
        amplitude: float,
        phi_0_rel: float,
        complex_output: bool = True,
    ) -> complex | float:
        """Give longitudinal electric field value."""
        return self._calculate_field(
            self._e_z_spat_rf,
            pos,
            phi,
            amplitude,
            phi_0_rel,
            complex_output=complex_output,
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
    ) -> tuple[FieldFuncComplexTimedComponent, FieldFuncTimedComponent]:
        """Generate a function for longitudinal transfer matrix calculation."""
        compl = functools.partial(
            self.e_z,
            amplitude=amplitude,
            phi_0_rel=phi_0_rel,
            complex_output=True,
        )
        rea = functools.partial(
            self.e_z,
            amplitude=amplitude,
            phi_0_rel=phi_0_rel,
            complex_output=False,
        )
        return compl, rea

    def _patch_to_keep_consistency(self, n_interp: Any, n_cell: int) -> None:
        """Save ``n_cell`` and ``n_z``. Temporary solution."""
        if not (isinstance(n_interp, tuple) and len(n_interp) == 1):
            raise ValueError(f"{n_interp = } but should be a 1D tuple.")
        self.n_z = n_interp[0]
        self.n_cell = n_cell

    def plot(self, amplitude: float = 1.0, phi_0_rel: float = 0.0) -> None:
        """Plot the profile of the electric field."""
        positions = np.linspace(0, self._length_m, self.n_z + 1)
        field_func = self.partial_e_z(
            amplitude=amplitude, phi_0_rel=phi_0_rel
        )[1]
        field_values = [field_func(pos, 0.0) for pos in positions]
        df = pd.DataFrame({"pos": positions, "field": field_values})
        df.plot(x="pos", grid=True)
