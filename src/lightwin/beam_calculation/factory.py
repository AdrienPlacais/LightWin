"""This module holds a factory to create the :class:`.BeamCalculator`."""

import logging
from pathlib import Path
from typing import Any, Literal, Self

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
    """A class to create :class:`.BeamCalculator` objects.

    Respects singleton pattern, so that only one factory can be created.

    """

    _instance: Self | None = None

    def __new__(cls, *args, **kwargs) -> Self:
        """Ensure that only one instance of object exists."""
        if cls._instance is None:
            logging.info("Creating new BeamCalculatorsFactory instance.")
            cls._instance = super().__new__(cls)
        else:
            logging.info("Re-using previous BeamCalculatorsFactory instance.")
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Allow creation of a new factry."""
        cls._instance = None

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
        if hasattr(self, "_initialized"):
            return

        self.all_beam_calculator_kw = (beam_calculator,)
        if beam_calculator_post is not None:
            self.all_beam_calculator_kw = (
                beam_calculator,
                beam_calculator_post,
            )
        self._beam_kwargs = beam
        self._initialized = True

        self._patch_to_remove_misunderstood_key()
        self._original_dat_dir: Path = files["dat_file"].parent
        self._cache: dict[int, BeamCalculator] = {}

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
        force_new: bool = False,
        **beam_calculator_kw,
    ) -> BeamCalculator:
        """Create a single :class:`.BeamCalculator`.

        If a :class:`.BeamCalculator` was already created with this factory
        and with the same arguments, we return it instead of instantiating a
        new one. Unless ``force_new`` is set to ``True``.

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
        force_true :
            To force creation of a new :class:`.BeamCalculator`.

        Returns
        -------
            An instance of the proper beam calculator.

        """
        cache_key = self._make_cache_key(
            reference_phase_policy=reference_phase_policy,
            tool=tool,
            export_phase=export_phase,
            flag_cython=flag_cython,
            **beam_calculator_kw,
        )
        if cache_key in self._cache and not force_new:
            beam_calculator = self._cache[cache_key]
            logging.info(
                f"Re-using existing BeamCalculator: {beam_calculator.id}"
            )
            return beam_calculator

        beam_calculator_class = _get_beam_calculator(
            tool, flag_cython=flag_cython, **beam_calculator_kw
        )
        beam_calculator = beam_calculator_class(
            reference_phase_policy=reference_phase_policy,
            default_field_map_folder=self._original_dat_dir,
            beam_kwargs=self._beam_kwargs,
            flag_cython=flag_cython,
            export_phase=export_phase,
            **beam_calculator_kw,
        )
        logging.info(f"Creating new BeamCalculator: {beam_calculator.id}")
        self._cache[cache_key] = beam_calculator
        return beam_calculator

    def _make_cache_key(
        self,
        reference_phase_policy: REFERENCE_PHASE_POLICY_T,
        tool: BEAM_CALCULATORS_T,
        export_phase: EXPORT_PHASES_T,
        flag_cython: bool = False,
        **beam_calculator_kw,
    ) -> int:
        """Create unique cache key to avoid re-creating BeamCalculators."""
        key_data = (
            reference_phase_policy,
            tool,
            export_phase,
            flag_cython,
            tuple(sorted(beam_calculator_kw.items())),
        )

        return hash(key_data)

    def run_all(self, force_new: bool = False) -> tuple[BeamCalculator, ...]:
        """Create all the beam calculators."""
        beam_calculators = [
            self.run(force_new=force_new, **beam_calculator_kw)
            for beam_calculator_kw in self.all_beam_calculator_kw
        ]
        return tuple(beam_calculators)
