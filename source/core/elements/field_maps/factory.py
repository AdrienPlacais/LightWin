"""Define a class to easily create :class:`.FieldMap` objects.

This element has its own factory as I expect that creating field maps will
become very complex in the future: 3D, superposed fields...

.. todo::
    This will be subclassed, as the different solvers do not have the same
    needs. :class:`.TraceWin` does not need to load the electromagnetic fields,
    so every ``FIELD_MAP`` is implemented.
    :class:`.Envelope1D` cannot support 3D.
    etc

"""

import logging
from abc import ABCMeta
from collections.abc import Collection, Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from core.elements.field_maps.cavity_settings_factory import (
    CavitySettingsFactory,
)
from core.elements.field_maps.field_map import FieldMap
from core.elements.field_maps.field_map_70 import FieldMap70
from core.elements.field_maps.field_map_100 import FieldMap100
from core.elements.field_maps.field_map_1100 import FieldMap1100
from core.elements.field_maps.field_map_7700 import FieldMap7700
from core.elements.field_maps.superposed_field_map import (
    SuperposedFieldMap,
    SuperposedPlaceHolderCmd,
    SuperposedPlaceHolderElt,
)
from core.instruction import Instruction
from tracewin_utils.line import DatLine

IMPLEMENTED_FIELD_MAPS = {
    70: FieldMap70,
    100: FieldMap100,
    1100: FieldMap1100,
    7700: FieldMap7700,
}  #:


@lru_cache(100)
def warn_once(geometry: int):
    """Raise this warning only once.

    https://stackoverflow.com/questions/31953272/logging-print-message-only-once

    """
    logging.warning(
        f"3D field maps ({geometry = }) not implemented yet. If solver is "
        "Envelope1D or Envelope3D, only the longitudinal rf electric field "
        "will be used (equivalent of 'FIELD_MAP 100')."
    )


class FieldMapFactory:
    """An object to create :class:`.FieldMap` objects."""

    def __init__(
        self,
        default_field_map_folder: Path,
        freq_bunch_mhz: float,
        default_absolute_phase_flag: Literal["0", "1"] = "0",
        **factory_kw: Any,
    ) -> None:
        """Save the default folder for field maps."""
        self.default_field_map_folder = default_field_map_folder
        self.default_absolute_phase_flag = default_absolute_phase_flag

        self.cavity_settings_factory = CavitySettingsFactory(freq_bunch_mhz)

    def run(
        self, line: DatLine, dat_idx: int | None = None, **kwargs
    ) -> FieldMap:
        """Call proper constructor."""
        if line.n_args == 9:
            line.append_argument(self.default_absolute_phase_flag)

        field_map_class = self._get_proper_field_map_subclass(
            int(line.splitted[1])
        )

        cavity_settings = self.cavity_settings_factory.from_line_in_dat_file(
            line,
            set_sync_phase=False,
        )

        field_map = field_map_class(
            line,
            dat_idx=dat_idx,
            default_field_map_folder=self.default_field_map_folder,
            cavity_settings=cavity_settings,
            **kwargs,
        )
        return field_map

    def _get_proper_field_map_subclass(self, geometry: int) -> ABCMeta:
        """Determine the proper field map subclass.

        .. warning::
            As for now, it always raises an error or return the rf electric
            field 1D class :class:`.FieldMap100`.

        """
        if geometry not in IMPLEMENTED_FIELD_MAPS:
            raise NotImplementedError(f"{geometry = } not supported")

        if geometry == 7700:
            warn_once(geometry)
            return FieldMap100

        return IMPLEMENTED_FIELD_MAPS[geometry]
