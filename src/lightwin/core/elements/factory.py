"""Define a class to easily create :class:`.Element` objects."""

from pathlib import Path
from typing import Any

from lightwin.core.elements.aperture import Aperture
from lightwin.core.elements.bend import Bend
from lightwin.core.elements.diagnostic import (
    DiagAchromat,
    DiagBeta,
    DiagCurrent,
    DiagDBeta,
    DiagDCurrent,
    DiagDDivergence,
    DiagDEnergy,
    DiagDivergence,
    DiagDPhase,
    DiagDPosition,
    DiagDPSize2,
    DiagDSize,
    DiagDSize2,
    DiagDSize2FWHM,
    DiagDSize3,
    DiagDSize4,
    DiagDSizeFWHM,
    DiagDTwiss,
    DiagDTwiss2,
    DiagEmit,
    DiagEmit99,
    DiagEnergy,
    DiagHalo,
    DiagLuminosity,
    DiagPhase,
    DiagPhaseAdv,
    DiagPosition,
    DiagSeparation,
    DiagSetMatrix,
    DiagSize,
    DiagSizeFWHM,
    DiagSizeMax,
    DiagSizeMin,
    DiagSizeP,
    DiagTwiss,
    DiagWaist,
)
from lightwin.core.elements.drift import Drift
from lightwin.core.elements.dummy import DummyElement
from lightwin.core.elements.edge import Edge
from lightwin.core.elements.element import Element
from lightwin.core.elements.field_maps.factory import FieldMapFactory
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.elements.quad import Quad
from lightwin.core.elements.solenoid import Solenoid
from lightwin.core.elements.thin_steering import ThinSteering
from lightwin.tracewin_utils.line import DatLine

implemented_elements = {
    "APERTURE": Aperture,
    "BEND": Bend,
    "DIAG_CURRENT": DiagCurrent,
    "DIAG_DCURRENT": DiagDCurrent,
    "DIAG_POSITION": DiagPosition,
    "DIAG_DPOSITION": DiagDPosition,
    "DIAG_DIVERGENCE": DiagDivergence,
    "DIAG_DDIVERGENCE": DiagDDivergence,
    "DIAG_SIZE_FWHM": DiagSizeFWHM,
    "DIAG_SIZE": DiagSize,
    "DIAG_SIZEP": DiagSizeP,
    "DIAG_DSIZE__FWHM": DiagDSizeFWHM,
    "DIAG_DSIZE": DiagDSize,
    "DIAG_DSIZE2_FWHM": DiagDSize2FWHM,
    "DIAG_DSIZE2": DiagDSize2,
    "DIAG_DSIZE3": DiagDSize3,
    "DIAG_DSIZE4": DiagDSize4,
    "DIAG_DPSIZE2": DiagDPSize2,
    "DIAG_PHASE": DiagPhase,
    "DIAG_ENERGY": DiagEnergy,
    "DIAG_DENERGY": DiagDEnergy,
    "DIAG_DPHASE": DiagDPhase,
    "DIAG_LUMINOSITY": DiagLuminosity,
    "DIAG_WAIST": DiagWaist,
    "DIAG_ACHROMAT": DiagAchromat,
    "DIAG_EMIT": DiagEmit,
    "DIAG_EMIT_99": DiagEmit99,
    "DIAG_HALO": DiagHalo,
    "DIAG_SET_MATRIX": DiagSetMatrix,
    "DIAG_TWISS": DiagTwiss,
    "DIAG_DTWISS": DiagDTwiss,
    "DIAG_DTWISS2": DiagDTwiss2,
    "DIAG_SEPARATION": DiagSeparation,
    "DIAG_SIZE_MAX": DiagSizeMax,
    "DIAG_SIZE_MIN": DiagSizeMin,
    "DIAG_PHASE_ADV": DiagPhaseAdv,
    "DIAG_BETA": DiagBeta,
    "DIAG_DBETA": DiagDBeta,
    "DRIFT": Drift,
    "DUMMY_ELEMENT": DummyElement,
    "EDGE": Edge,
    "FIELD_MAP": FieldMap,  # replaced in ElementFactory initialisation
    "QUAD": Quad,
    "SOLENOID": Solenoid,
    "THIN_STEERING": ThinSteering,
}  #:


class ElementFactory:
    """An object to create :class:`.Element` objects."""

    def __init__(
        self,
        default_field_map_folder: Path,
        freq_bunch_mhz: float,
        **factory_kw: Any,
    ) -> None:
        """Create a factory for the field maps."""
        field_map_factory = FieldMapFactory(
            default_field_map_folder, freq_bunch_mhz, **factory_kw
        )
        self.field_map_factory = field_map_factory
        implemented_elements["FIELD_MAP"] = field_map_factory.run

    def run(
        self, line: DatLine, dat_idx: int | None = None, **kwargs
    ) -> Element:
        """Call proper constructor."""
        if dat_idx is None:
            dat_idx = line.idx
        element_constructor = _get_constructor(line.instruction, dat_idx)
        element = element_constructor(line, dat_idx, **kwargs)
        return element


def _get_constructor(instruction: str, dat_idx: int) -> type:
    """Get the proper constructor."""
    if instruction in implemented_elements:
        return implemented_elements[instruction]
    raise OSError(
        f"No Element matching {instruction} at line {dat_idx + 1} was found."
    )
