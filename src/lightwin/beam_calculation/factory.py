"""This module holds a factory to create the :class:`.BeamCalculator`."""

import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal

from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.beam_calculation.cy_envelope_1d.envelope_1d import CyEnvelope1D
from lightwin.beam_calculation.envelope_1d.envelope_1d import Envelope1D
from lightwin.beam_calculation.envelope_3d.envelope_3d import Envelope3D
from lightwin.beam_calculation.tracewin.tracewin import TraceWin
from lightwin.util.typing import (
    EXPORT_PHASES_T,
    REFERENCE_PHASE_POLICY_T,
    BeamKwargs,
)

BEAM_CALCULATORS = (
    "Envelope1D",
    "TraceWin",
    "Envelope3D",
)  #:
BEAM_CALCULATORS_T = Literal["Envelope1D", "TraceWin", "Envelope3D"]


def _get_beam_calculator(
    tool: BEAM_CALCULATORS_T, flag_cython: bool, **kwargs
) -> type:
    """Get the proper :class:`.BeamCalculator` constructor."""
    match tool, flag_cython:
        case "Envelope1D", False:
            return Envelope1D
        case "Envelope1D", True:
            return CyEnvelope1D
        case "Envelope3D", False:
            return Envelope3D
        case "Envelope3D", True:
            logging.warning(
                "No Cython implementation for Envelope3D. Using Python "
                "implementation."
            )
            return Envelope3D
        case "TraceWin", _:
            return TraceWin
        case _:
            raise ValueError(
                f"{tool = } and/or {flag_cython = } not understood."
            )


class BeamCalculatorsFactory:
    """A class to create :class:`.BeamCalculator` objects."""

    def __init__(
        self,
        beam_calculator: dict[str, Any],
        files: dict[str, Any],
        beam: BeamKwargs,
        beam_calculator_post: dict[str, Any] | None = None,
        **other_kw: dict,
    ) -> None:
        """
        Set up factory with arguments common to all :class:`.BeamCalculator`.

        Parameters
        ----------
        beam_calculator :
            Configuration entries for the first :class:`.BeamCalculator`, used
            for optimisation.
        files :
            Configuration entries for the input/output paths.
        beam :
            Configuration dictionary holding the initial beam parameters.
        beam_calculator_post :
            Configuration entries for the second optional
            :class:`.BeamCalculator`, used for a more thorough calculation of
            the beam propagation once the compensation settings are found.
        other_kw :
            Other keyword arguments, not used for the moment.

        """
        self.all_beam_calculator_kw = (beam_calculator,)
        if beam_calculator_post is not None:
            self.all_beam_calculator_kw = (
                beam_calculator,
                beam_calculator_post,
            )
        self._beam_kwargs = beam

        self.out_folders = self._set_out_folders(self.all_beam_calculator_kw)

        self.beam_calculators_id: list[str] = []
        self._patch_to_remove_misunderstood_key()
        self._original_dat_dir: Path = files["dat_file"].parent

    def _set_out_folders(
        self, all_beam_calculator_kw: Sequence[dict[str, Any]]
    ) -> list[Path]:
        """Set in which subfolder the results will be saved."""
        out_folders = [
            Path(f"{i}_{kw['tool']}")
            for i, kw in enumerate(all_beam_calculator_kw)
        ]
        return out_folders

    def _patch_to_remove_misunderstood_key(self) -> None:
        """Patch to remove a key not understood by TraceWin. Declare id list.

        .. todo::
            fixme

        """
        for beam_calculator_kw in self.all_beam_calculator_kw:
            if "simulation type" in beam_calculator_kw:
                del beam_calculator_kw["simulation type"]

    def run(
        self,
        reference_phase_policy: REFERENCE_PHASE_POLICY_T,
        tool: BEAM_CALCULATORS_T,
        export_phase: EXPORT_PHASES_T,
        flag_cython: bool = False,
        **beam_calculator_kw,
    ) -> BeamCalculator:
        """Create a single :class:`.BeamCalculator`.

        Parameters
        ----------
        reference_phase_policy :
            How reference phase of :class:`.CavitySettings` will be
            initialized.
        tool :
            The name of the beam calculator to construct.
        export_phase :
            The type of phase you want to export for your ``FIELD_MAP``.
        flag_cython :
            If the beam calculator involves loading cython field maps.

        Returns
        -------
            An instance of the proper beam calculator.

        """
        beam_calculator_class = _get_beam_calculator(
            tool, flag_cython=flag_cython, **beam_calculator_kw
        )
        beam_calculator = beam_calculator_class(
            reference_phase_policy=reference_phase_policy,
            out_folder=self.out_folders.pop(0),
            default_field_map_folder=self._original_dat_dir,
            beam_kwargs=self._beam_kwargs,
            flag_cython=flag_cython,
            export_phase=export_phase,
            **beam_calculator_kw,
        )
        self.beam_calculators_id.append(beam_calculator.id)
        return beam_calculator

    def run_all(self) -> tuple[BeamCalculator, ...]:
        """Create all the beam calculators."""
        beam_calculators = [
            self.run(**beam_calculator_kw)
            for beam_calculator_kw in self.all_beam_calculator_kw
        ]
        return tuple(beam_calculators)
