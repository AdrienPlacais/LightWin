"""Define :class:`Diagnostic`.

As for now, diagnostics are not used by LightWin. However, LightWin can add
diagnostics (as well as ADJUST) to the final ``.dat`` in order to perform a
"pass beauty".

.. note::
    Functionalities still under implementation. In particular, the number of
    attributes were not checked.

.. note::
    This is TraceWin's equivalent of :class:`.Objective`.

"""

from typing import override

from core.elements.element import Element
from tracewin_utils.line import DatLine


class Diagnostic(Element):
    """A dummy object."""

    base_name = "D"
    increment_lattice_idx = False
    is_implemented = False

    def __init__(
        self,
        line: DatLine,
        dat_idx: int | None = None,
        **kwargs: str,
    ) -> None:
        """Force an element with null-length, with no index."""
        super().__init__(line, dat_idx, **kwargs)
        self.weight = 1.0
        if line.weight is not None:
            self.weight = line.weight

        self.length_m = 0.0
        self.number = int(line.splitted[1])


class DiagCurrent(Diagnostic):
    """Measure current."""


class DiagDCurrent(Diagnostic):
    """Measure delta current."""


class DiagPosition(Diagnostic):
    """Measure position."""

    is_implemented = True
    n_attributes = 4


class DiagDPosition(Diagnostic):
    """Measure delta position."""


class DiagDivergence(Diagnostic):
    """Measure divergences."""


class DiagDDivergence(Diagnostic):
    """Measure delta divergences."""


class DiagSizeFWHM(Diagnostic):
    """Measure full width at half maximum."""


class DiagSize(Diagnostic):
    """Measure sizes."""


class DiagSizeP(Diagnostic):
    """Measure divergences."""


class DiagDSizeFWHM(Diagnostic):
    """Measure delta full width at half maximum."""


class DiagDSize(Diagnostic):
    """Measure delta size."""


class DiagDSize2FWHM(Diagnostic):
    """Measure delta full width at half maximum between two positions."""


class DiagDSize2(Diagnostic):
    """Measure delta size between two positions."""

    is_implemented = True
    n_attributes = (3, 4)

    def __init__(
        self,
        line: DatLine,
        dat_idx: int | None = None,
        **kwargs: str,
    ) -> None:
        """Force an element with null-length, with no index."""
        super().__init__(line, dat_idx, **kwargs)
        self.x_rms_beam_delta_size = float(line.splitted[2])
        self.y_rms_beam_delta_size = float(line.splitted[3])

        if line.n_args == 4:
            self.accuracy = float(line.splitted[4])


class DiagDSize3(Diagnostic):
    """Measure delta phase spread between two positions."""

    is_implemented = True
    n_attributes = (3, 4)

    def __init__(
        self,
        line: DatLine,
        dat_idx: int | None = None,
        **kwargs: str,
    ) -> None:
        """Force an element with null-length, with no index."""
        super().__init__(line, dat_idx, **kwargs)
        self.rms_delta_phase_spread = float(line.splitted[2])
        self.accuracy = float(line.splitted[3])

        if line.n_args == 4:
            self.low_pass_filter_frequency = float(line.splitted[4])

    @classmethod
    @override
    def _args_to_line(
        cls,
        number: int,
        rms_delta_phase_spread: float = 0.0,
        accuracy: float = 0.0,
        low_pass_filter_frequency: float | None = None,
    ) -> str:
        """Convert list of arguments to corresponding line of dat file."""
        line = f"DIAG_DSIZE3 {number} {rms_delta_phase_spread} {accuracy}"
        if low_pass_filter_frequency is not None:
            line += " " + str(low_pass_filter_frequency)
        return line


class DiagDSize4(Diagnostic):
    """Measure something?"""


class DiagDPSize2(Diagnostic):
    """Measure delta divergence between two positions."""


class DiagPhase(Diagnostic):
    """Measure phase."""

    n_attributes = 2


class DiagEnergy(Diagnostic):
    """Measure energy."""

    n_attributes = 3


class DiagDEnergy(Diagnostic):
    """Measure difference between beam energy and perfect linac energy."""

    n_attributes = 3


class DiagDPhase(Diagnostic):
    """Measure difference between beam phase and perfect linac phase."""

    n_attributes = 2


class DiagLuminosity(Diagnostic):
    """Measure luminosity."""

    n_attributes = 3


class DiagWaist(Diagnostic):
    """Measure waist setting."""

    n_attributes = 4


class DiagAchromat(Diagnostic):
    """Measure achromat setting."""

    n_attributes = 5


class DiagEmit(Diagnostic):
    """Measure RMS emittance setting."""

    n_attributes = 4


class DiagEmit99(Diagnostic):
    """Measure 99% emittance setting."""

    n_attributes = 4


class DiagHalo(Diagnostic):
    """Measure halo setting."""

    n_attributes = 4


class DiagSetMatrix(Diagnostic):
    """Measure transfer matrix setting."""

    n_attributes = 6


class DiagTwiss(Diagnostic):
    """Measure beam Twiss parameters settings."""

    n_attributes = 7


class DiagDTwiss(Diagnostic):
    """Make equal two beam Twiss parameters between two positions or more."""

    n_attributes = 7


class DiagDTwiss2(Diagnostic):
    """Make equal transverse Twiss parameters at diagnostic position."""

    n_attributes = 3


class DiagSeparation(Diagnostic):
    """Measure beam separation setting."""

    n_attributes = 6


class DiagSizeMax(Diagnostic):
    """Limit beam size max."""

    n_attributes = 6


class DiagSizeMin(DiagSizeMax):
    """Limit beam size min."""


class DiagPhaseAdv(Diagnostic):
    """Measure beam phase advance."""

    n_attributes = 4


class DiagBeta(Diagnostic):
    """Measure beam beta."""

    n_attributes = 6


class DiagDBeta(Diagnostic):
    """Measure delta beam beta."""

    n_attributes = 4
