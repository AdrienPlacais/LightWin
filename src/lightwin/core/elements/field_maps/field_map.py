"""Hold a ``FIELD_MAP``.

.. todo::
    Handle the different kind of field_maps...

.. todo::
    Completely handle the SET_SYNCH_PHASE command

.. todo::
    Hande phi_s fitting with :class:`.TraceWin`.

.. note::
    When subclassing field_maps, do not forget to update the transfer matrix
    selector in:
    - :class:`.Envelope3D`
    - :class:`.ElementEnvelope3DParameters`
    - :class:`.SetOfCavitySettings`
    - the ``run_with_this`` methods

"""

import math
from pathlib import Path
from typing import Any

import numpy as np

from lightwin.core.elements.element import Element
from lightwin.core.elements.field_maps.cavity_settings import CavitySettings
from lightwin.core.elements.field_maps.util import set_full_field_map_path
from lightwin.core.em_fields.field import Field
from lightwin.core.em_fields.rf_field import RfField
from lightwin.tracewin_utils.line import DatLine
from lightwin.util.helper import recursive_getter
from lightwin.util.typing import (
    ALLOWED_STATUS,
    EXPORT_PHASES_T,
    GETTABLE_FIELD_MAP_T,
    REFERENCE_PHASES_T,
    STATUS_T,
)


class FieldMap(Element):
    """A generic ``FIELD_MAP``."""

    base_name = "FM"
    n_attributes = 10

    def __init__(
        self,
        line: DatLine,
        default_field_map_folder: Path,
        cavity_settings: CavitySettings,
        dat_idx: int | None = None,
        **kwargs,
    ) -> None:
        """Set most of attributes defined in ``TraceWin``."""
        super().__init__(line, dat_idx, **kwargs)

        self.geometry = int(line.splitted[1])
        self.length_m = 1e-3 * float(line.splitted[2])
        self.aperture_flag = int(line.splitted[8])  # K_a

        self.field_map_folder = default_field_map_folder
        self.field_map_file_name: str | list[Path] = line.splitted[9]

        self._can_be_retuned: bool = True
        self.rf_field = RfField(section_idx=self.idx["section"])
        #: Stores the settings of the cavity, such as amplitude or phase.
        self.cavity_settings = cavity_settings
        self.cavity_settings.rf_field = self.rf_field
        #: Stores the field properties, such as interpolated field or
        #: frequency. This object is shared by all the caviities with the same
        #: geometry.
        self.field: Field

    @property
    def status(self) -> str:
        """Give the status from the :class:`.CavitySettings`."""
        return self.cavity_settings.status

    @property
    def is_accelerating(self) -> bool:
        """Tell if the cavity is working."""
        if self.status == "failed":
            return False
        return True

    @property
    def is_altered(self) -> bool:
        """Tell if cavity is altered, *i.e.* not in nominal settings."""
        return self.status != "nominal"

    @property
    def can_be_retuned(self) -> bool:
        """Tell if we can modify the element's tuning."""
        return self._can_be_retuned

    @can_be_retuned.setter
    def can_be_retuned(self, value: bool) -> None:
        """Forbid this cavity from being retuned (or re-allow it)."""
        self._can_be_retuned = value

    def update_status(self, new_status: STATUS_T) -> None:
        """Change the status of the cavity.

        We use
        :meth:`.ElementBeamCalculatorParameters.re_set_for_broken_cavity`
        method.
        If ``k_e``, ``phi_s``, ``v_cav_mv`` are altered, this is performed in
        :meth:`.CavitySettings.status` ``setter``.

        """
        assert new_status in ALLOWED_STATUS
        self.cavity_settings.status = new_status
        if new_status != "failed":
            return

        for solver_id, beam_calc_param in self.beam_calc_param.items():
            new_transf_mat_func = beam_calc_param.re_set_for_broken_cavity()
            self.cavity_settings.set_cavity_parameters_methods(
                solver_id,
                new_transf_mat_func,
            )
        return

    def set_full_path(self, extensions: dict[str, list[str]]) -> None:
        """Set absolute paths with extensions of electromagnetic files.

        Parameters
        ----------
        extensions :
            Keys are nature of the field, values are a list of extensions
            corresponding to it without a period.

        See Also
        --------
        :func:`.electromagnetic_fields._get_filemaps_extensions`

        """
        self.field_map_file_name = set_full_field_map_path(
            self.field_map_folder, self.field_map_file_name, extensions
        )

    def keep_cavity_settings(self, cavity_settings: CavitySettings) -> None:
        """Keep the cavity settings that were found."""
        assert cavity_settings is not None
        self.cavity_settings = cavity_settings

    def has(self, key: str) -> bool:
        """
        Tell if required attribute is in this object or its cavity settings.

        Parameters
        ----------
        key :
            Name of the attribute to check.

        Returns
        -------
        bool
            True if the key is found in ``self`` or ``self.cavity_settings``.

        """
        return super().has(key) or self.cavity_settings.has(key)

    def get(
        self,
        *keys: GETTABLE_FIELD_MAP_T,
        to_numpy: bool = True,
        none_to_nan: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Get attributes from this class or its attributes.

        Parameters
        ----------
        *keys :
            Name of the desired attributes.
        to_numpy :
            If you want the list output to be converted to a np.ndarray.
        **kwargs :
            Other arguments passed to recursive getter.

        Returns
        -------
            Attribute(s) value(s).

        """

        def resolve_key(key: str) -> Any:
            if key == "name":
                return self.name

            if self.cavity_settings.has(key):
                return self.cavity_settings.get(
                    key, to_numpy=to_numpy, none_to_nan=none_to_nan, **kwargs
                )

            if not self.has(key):
                return None
            return recursive_getter(key, vars(self), **kwargs)

        values = [resolve_key(key) for key in keys]

        if to_numpy:
            values = [
                (
                    np.array(np.nan)
                    if v is None and none_to_nan
                    else np.array(v) if isinstance(v, list) else v
                )
                for v in values
            ]
        else:
            values = [
                (
                    [np.nan]
                    if v is None and none_to_nan
                    else v.tolist() if isinstance(v, np.ndarray) else v
                )
                for v in values
            ]

        return values[0] if len(values) == 1 else tuple(values)

        # return super().get(
        #     *keys, to_numpy=to_numpy, none_to_nan=none_to_nan, **kwargs
        # )
        val = {key: [] for key in keys}

        for key in keys:
            if key == "name":
                val[key] = self.name
                continue

            if self.cavity_settings.has(key):
                val[key] = self.cavity_settings.get(key)
                continue

            if not self.has(key):
                val[key] = None
                continue

            val[key] = recursive_getter(key, vars(self), **kwargs)
            if not to_numpy and isinstance(val[key], np.ndarray):
                val[key] = val[key].tolist()

        out = [
            (
                np.array(val[key])
                if to_numpy and not isinstance(val[key], str)
                else val[key]
            )
            for key in keys
        ]
        if none_to_nan:
            out = [x if x is not None else np.nan for x in out]

        if len(out) == 1:
            return out[0]
        return tuple(out)

    def get_of_element_for_comparison(
        self,
        *keys: GETTABLE_FIELD_MAP_T,
        to_numpy: bool = True,
        **kwargs: bool | str | None,
    ) -> Any:
        """Get attributes from this class or its attributes.

        Parameters
        ----------
        *keys :
            Name of the desired attributes.
        to_numpy :
            If you want the list output to be converted to a np.ndarray.
        **kwargs :
            Other arguments passed to recursive getter.

        Returns
        -------
            Attribute(s) value(s).

        """
        val = {key: [] for key in keys}

        for key in keys:
            if key == "name":
                val[key] = self.name
                continue

            if not self.has(key):
                val[key] = None
                continue

            val[key] = recursive_getter(key, vars(self), **kwargs)
            if not to_numpy and isinstance(val[key], np.ndarray):
                val[key] = val[key].tolist()

        out = [
            (
                np.array(val[key])
                if to_numpy and not isinstance(val[key], str)
                else val[key]
            )
            for key in keys
        ]

        if len(out) == 1:
            return out[0]
        return tuple(out)

    def to_line(
        self,
        which_phase: EXPORT_PHASES_T,
        *args,
        round: int | None = None,
        **kwargs,
    ) -> list[str]:
        r"""Convert the object back into a line in the ``DAT`` file.

        Parameters
        ----------
        which_phase :
            Which phase should be put in the output ``DAT``.
        round :
            Rounding numbers in exported line.

        Returns
        -------
        list[str]
            The line in the ``DAT``, with updated amplitude and phase from
            current object.

        """
        phase, abs_phase_flag, reference = self._phase_for_line(which_phase)
        for value, position in zip(
            (phase, self.cavity_settings.k_e, abs_phase_flag), (3, 6, 10)
        ):
            if round:
                value = value.__round__(round)
            self.line.change_argument(value, position)

        line = super().to_line(*args, **kwargs)
        if reference == "phi_s":
            line.insert(0, "SET_SYNC_PHASE\n")
        return line

    # May be useless, depending on to_line implementation
    @property
    def _indexes_in_line(self) -> dict[str, int]:
        """Give the position of the arguments in the ``FIELD_MAP`` command."""
        indexes = {"phase": 3, "k_e": 6, "abs_phase_flag": 10}

        if not self._personalized_name:
            return indexes
        for key in indexes:
            indexes[key] += 1
        return indexes

    def _phase_for_line(
        self, which_phase: EXPORT_PHASES_T
    ) -> tuple[float, int, REFERENCE_PHASES_T]:
        """Give the phase to put in ``DAT`` line, with abs phase flag."""
        settings = self.cavity_settings
        match which_phase:
            case "phi_0_abs" | "phi_0_rel" | "phi_s":
                phase = getattr(settings, which_phase)
                abs_phase_flag = int(which_phase == "phi_0_abs")
                reference = which_phase

            case "as_in_settings":
                phase = settings.phi_ref
                abs_phase_flag = int(settings.reference == "phi_0_abs")
                reference = settings.reference

            case "as_in_original_dat":
                raise NotImplementedError
                abs_phase_flag = int(self.line.splitted[-1])
                if abs_phase_flag == 0:
                    to_get = "phi_0_rel"
                elif abs_phase_flag == 1:
                    to_get = "phi_0_abs"
                else:
                    raise ValueError
                phase = getattr(settings, to_get)
                reference = to_get
            case _:
                raise OSError("{which_phase = } not understood.")
        assert phase is not None, (
            f"In {self}, the required phase ({which_phase = }) is not defined."
            " Maybe the particle entry phase is not defined?"
        )
        return math.degrees(phase), abs_phase_flag, reference
