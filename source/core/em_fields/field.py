"""Hold a field map; can be shared by several elements.

See Also
--------
CavitySettings


Not that for now, we expect that coordinates are always cartesian.

.. todo::
    Define a FieldMapLoader function to choose esaily between binary/ascii file
    format.

"""

import functools
import math
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np

from core.em_fields.helper import null_field_1d
from core.em_fields.types import (
    AnyDimFloat,
    AnyDimInt,
    FieldFuncComponent,
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
    r"""Generic electro-magnetic field."""

    extensions: tuple[str, ...]

    def __init__(self, field_map_path: Path) -> None:
        """Instantiate object."""
        self.field_map_path = field_map_path
        self.n_cell: int
        self.n_z: int
        self.is_loaded = False

        # Used in SUPERPOSED_MAP to shift a field
        self.z_0: float = 0.0

        # Where we store interpolated field maps (to multiply by cos phi)
        self._e_x_spat_rf: FieldFuncComponent = null_field_1d
        self._e_y_spat_rf: FieldFuncComponent = null_field_1d
        self._e_z_spat_rf: FieldFuncComponent = null_field_1d
        self._b_x_spat_rf: FieldFuncComponent = null_field_1d
        self._b_y_spat_rf: FieldFuncComponent = null_field_1d
        self._b_z_spat_rf: FieldFuncComponent = null_field_1d

        # Where we store static field maps (no phase anyway)
        self._e_x_dc: FieldFuncComponent = null_field_1d
        self._e_y_dc: FieldFuncComponent = null_field_1d
        self._e_z_dc: FieldFuncComponent = null_field_1d
        self._b_x_dc: FieldFuncComponent = null_field_1d
        self._b_y_dc: FieldFuncComponent = null_field_1d
        self._b_z_dc: FieldFuncComponent = null_field_1d

    def shift(self) -> None:
        """Shift the field maps."""
        raise NotImplementedError

    # in reality, override this
    @abstractmethod
    def e_z(
        self, pos: AnyDimFloat, phi: float, amplitude: float, phi_0_rel: float
    ) -> float:
        """Give longitudinal electric field value."""
        return amplitude * self._e_z_spat_rf(pos) * math.cos(phi + phi_0_rel)

    # in reality, override this
    def generate_e_z_with_settings(
        self, amplitude: float, phi_0_rel: float
    ) -> FieldFuncTimedComponent:
        """Generate a function for a transfer matrix calculation."""
        return functools.partial(
            self.e_z, amplitude=amplitude, phi_0_rel=phi_0_rel
        )

    def load_fieldmaps(self) -> None:
        """Load all field components for class :attr:`extensions`."""
        for ext in self.extensions:
            path = self.field_map_path.with_suffix(ext)
            func = self._load_fieldmap(path)
            attribute_name = EXTENSION_TO_COMPONENT[ext]
            setattr(self, attribute_name, func)
        self.is_loaded = True

    @abstractmethod
    def _load_fieldmap(
        self, path: Path
    ) -> tuple[FieldFuncComponent, AnyDimInt]:
        """Generate field function corresponding to a single field file.

        Parameters
        ----------
        path : Path
            Path to a field map file.

        Returns
        -------
        func : FieldFuncComponent
            Give field at a given position.
        n_points : AnyDimInt
            Number of interpolation points in the various directions.

        """
        pass
