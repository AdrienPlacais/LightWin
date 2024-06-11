"""Hold a ``FIELD_MAP``.

.. todo::
    Handle the different kind of field_maps...

.. todo::
    Handle the SET_SYNCH_PHASE command

.. todo::
    Hande phi_s fitting with :class:`beam_calculation.tracewin.Tracewin`

.. todo::
    when subclassing field_maps, do not forget to update the transfer matrix
    selector in:
    - :class:`.Envelope3D`
    - :class:`.SingleElementEnvelope3DParameters`
    - :class:`.SetOfCavitySettings`
    - the ``run_with_this`` methods

"""

import math
from pathlib import Path
from typing import Any

import numpy as np

from core.elements.element import Element
from core.elements.field_maps.cavity_settings import CavitySettings
from core.elements.field_maps.util import set_full_field_map_path
from core.em_fields.rf_field import RfField
from tracewin_utils.line import DatLine
from util.helper import recursive_getter

# warning: doublon with cavity_settings.ALLOWED_STATUS
IMPLEMENTED_STATUS = (
    # Cavity settings not changed from .dat
    "nominal",
    # Cavity ABSOLUTE phase changed; relative phase unchanged
    "rephased (in progress)",
    "rephased (ok)",
    # Cavity norm is 0
    "failed",
    # Trying to fit
    "compensate (in progress)",
    # Compensating, proper setting found
    "compensate (ok)",
    # Compensating, proper setting not found
    "compensate (not ok)",
)  #:


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
        self.cavity_settings = cavity_settings

        self.field_map_folder = default_field_map_folder
        self.field_map_file_name = Path(line.splitted[9])

        self.rf_field: RfField
        self._can_be_retuned: bool = True

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
    def can_be_retuned(self) -> bool:
        """Tell if we can modify the element's tuning."""
        return self._can_be_retuned

    @can_be_retuned.setter
    def can_be_retuned(self, value: bool) -> None:
        """Forbid this cavity from being retuned (or re-allow it)."""
        self._can_be_retuned = value

    def update_status(self, new_status: str) -> None:
        """Change the status of the cavity.

        We use
        :meth:`.ElementBeamCalculatorParameters.re_set_for_broken_cavity`
        method.
        If ``k_e``, ``phi_s``, ``v_cav_mv`` are altered, this is performed in
        :meth:`.CavitySettings.status` ``setter``.

        """
        assert new_status in IMPLEMENTED_STATUS

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
        extensions : dict[str, list[str]]
            Keys are nature of the field, values are a list of extensions
            corresponding to it without a period.

        See Also
        --------
        :func:`tracewin_utils.electromagnetic_fields.file_map_extensions`

        """
        self.field_map_file_name = set_full_field_map_path(
            self.field_map_folder, self.field_map_file_name, extensions
        )

    def keep_cavity_settings(self, cavity_settings: CavitySettings) -> None:
        """Keep the cavity settings that were found."""
        assert cavity_settings is not None
        self.cavity_settings = cavity_settings

    def get(
        self,
        *keys: str,
        to_numpy: bool = True,
        none_to_nan: bool = False,
        **kwargs: bool | str | None,
    ) -> Any:
        """
        Shorthand to get attributes from this class or its attributes.

        Parameters
        ----------
        *keys: str
            Name of the desired attributes.
        to_numpy : bool, optional
            If you want the list output to be converted to a np.ndarray. The
            default is True.
        **kwargs : bool | str | None
            Other arguments passed to recursive getter.

        Returns
        -------
        out : Any
            Attribute(s) value(s).

        """
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
            out = [x if x is not None else np.NaN for x in out]

        if len(out) == 1:
            return out[0]
        return tuple(out)

    def to_line(
        self,
        which_phase: str = "phi_0_rel",
        *args,
        **kwargs,
    ) -> list[str]:
        r"""Convert the object back into a line in the ``.dat`` file.

        Parameters
        ----------
        which_phase : {'phi_0_abs', 'phi_0_rel', 'phi_s', 'as_in_settings',
                \ 'as_in_original_dat'}
            Which phase should be putted in the output ``.dat``.
        inplace : bool, optional
            To modify or not the :attr:`.Element` inplace. If False, we return
            a modified copy. The default is False.

        Returns
        -------
        list[str]
            The line in the ``.dat``, with updated amplitude and phase from
            current object.

        """
        line = super().to_line(*args, **kwargs)

        _phases = self._phase_for_line(which_phase)
        new_values = {
            3: _phases[0],
            6: self.cavity_settings.k_e,
            10: _phases[1],
        }
        for key, val in new_values.items():
            self.line.change_argument(val, key)
        return line

    def _phase_for_line(self, which_phase: str) -> tuple[float, int]:
        """Give the phase to put in ``.dat`` line, with abs phase flag."""
        settings = self.cavity_settings
        match which_phase:
            case "phi_0_abs" | "phi_0_rel":
                phase = getattr(settings, which_phase)
                abs_phase_flag = int(which_phase == "phi_0_abs")

            case "phi_s":
                raise NotImplementedError(
                    "Output of phi_s (SET_SYNC_PHASE) in the .dat not "
                    "implemented (yet)."
                )

            case "as_in_settings":
                assert (
                    settings.reference != "phi_s"
                ), "The SET_SYNC_PHASE is not implemented yet."
                phase = getattr(settings, "reference")
                abs_phase_flag = int(settings.reference == "phi_0_abs")

            case "as_in_original_dat":
                abs_phase_flag = int(self.line.splitted[-1])
                if abs_phase_flag == 0:
                    to_get = "phi_0_rel"
                elif abs_phase_flag == 1:
                    to_get = "phi_0_abs"
                else:
                    raise ValueError
                phase = getattr(settings, to_get)
            case _:
                raise IOError("{which_phase = } not understood.")
        assert phase is not None, (
            f"In {self}, the required phase ({which_phase = }) is not defined."
            " Maybe the particle entry phase is not defined?"
        )
        return (math.degrees(phase), abs_phase_flag)
