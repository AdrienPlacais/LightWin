"""Hold the beam parameters in a single phase space.

For a list of the units associated with every parameter, see
:ref:`units-label`.

.. note::
    In this module, angles are stored in deg, not in rad!

"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Self

from numpy.typing import NDArray

from lightwin.core.beam_parameters.helper import (
    envelopes_from_sigma,
    envelopes_from_twiss_eps,
    eps_from_other_phase_space,
    eps_from_sigma,
    twiss_from_other_phase_space,
    twiss_from_sigma,
)
from lightwin.util.helper import range_vals_object
from lightwin.util.typing import PHASE_SPACE_T, PHASE_SPACES, BeamKwargs


@dataclass
class IPhaseSpaceBeamParameters(ABC):
    """Hold Twiss, emittance, envelopes of single phase-space @ single pos."""

    phase_space_name: PHASE_SPACE_T
    eps_no_normalization: NDArray | float
    eps_normalized: NDArray | float
    # _beam_kwargs: BeamKwargs
    envelopes: NDArray | None = None
    twiss: NDArray | None = None
    sigma: NDArray | None = None
    tm_cumul: NDArray | None = None
    mismatch_factor: NDArray | float | None = None

    def __post_init__(self) -> None:
        """Ensure that the phase space exists."""
        assert self.phase_space_name in PHASE_SPACES

    @classmethod
    def from_sigma(
        cls,
        phase_space_name: PHASE_SPACE_T,
        sigma: NDArray,
        gamma_kin: NDArray | float,
        beta_kin: NDArray | float,
        beam_kwargs: BeamKwargs,
        **kwargs: NDArray,
    ) -> Self:
        """Compute Twiss, eps, envelopes just from sigma matrix."""
        eps_no_normalization, eps_normalized = eps_from_sigma(
            phase_space_name,
            sigma,
            gamma_kin,
            beta_kin,
            beam_kwargs=beam_kwargs,
        )
        twiss = twiss_from_sigma(phase_space_name, sigma, eps_no_normalization)
        envelopes = envelopes_from_sigma(phase_space_name, sigma)
        phase_space = cls(
            phase_space_name=phase_space_name,
            eps_no_normalization=eps_no_normalization,
            eps_normalized=eps_normalized,
            sigma=sigma,
            twiss=twiss,
            envelopes=envelopes,
            # _beam_kwargs=beam_kwargs,
            **kwargs,
        )
        return phase_space

    @classmethod
    def from_other_phase_space(
        cls,
        other_phase_space: Self,
        phase_space_name: PHASE_SPACE_T,
        gamma_kin: NDArray | float,
        beta_kin: NDArray | float,
        beam_kwargs: BeamKwargs,
        **kwargs: NDArray,  # sigma, tm_cumul
    ) -> Self:
        """Fully initialize from another phase space."""
        other_phase_space_name = other_phase_space.phase_space_name
        eps_other = other_phase_space.eps_normalized
        twiss_other = other_phase_space.twiss
        assert twiss_other is not None

        eps_no_normalization, eps_normalized = eps_from_other_phase_space(
            other_phase_space_name=other_phase_space_name,
            phase_space_name=phase_space_name,
            eps_other=eps_other,
            gamma_kin=gamma_kin,
            beta_kin=beta_kin,
            **beam_kwargs,
        )
        twiss = twiss_from_other_phase_space(
            other_phase_space_name,
            phase_space_name,
            twiss_other,
            gamma_kin,
            beta_kin,
            **beam_kwargs,
        )

        eps_for_envelope = eps_no_normalization
        if phase_space_name == "phiw":
            eps_for_envelope = eps_normalized
        envelopes = envelopes_from_twiss_eps(twiss, eps_for_envelope)
        phase_space = cls(
            phase_space_name=phase_space_name,
            eps_no_normalization=eps_no_normalization,
            eps_normalized=eps_normalized,
            twiss=twiss,
            envelopes=envelopes,
            # _beam_kwargs=beam_kwargs,
            **kwargs,
        )
        return phase_space

    def __str__(self) -> str:
        """Show amplitude of some of the attributes."""
        out = f"\t\tPhase space {self.phase_space_name}:\n"
        for key in (
            "alpha",
            "beta",
            "eps",
            "envelope_pos",
            "envelope_energy",
            "mismatch_factor",
        ):
            out += "\t\t\t" + range_vals_object(self, key)
        return out

    def __repr__(self) -> str:
        """Give same information as str."""
        return self.__str__()

    @property
    @abstractmethod
    def alpha(self) -> NDArray | float | None:
        """Get first element/column of ``self.twiss``."""
        pass

    @alpha.setter
    @abstractmethod
    def alpha(self, value: NDArray | float) -> None:
        """Set first element/column of ``self.twiss``."""
        pass

    @property
    @abstractmethod
    def beta(self) -> NDArray | float | None:
        """Get second element/column of ``self.twiss``."""
        pass

    @beta.setter
    @abstractmethod
    def beta(self, value: NDArray | float) -> None:
        """Set second element/column of ``self.twiss``."""
        pass

    @property
    @abstractmethod
    def gamma(self) -> NDArray | float | None:
        """Get third element/column of ``self.twiss``."""
        pass

    @gamma.setter
    @abstractmethod
    def gamma(self, value: NDArray | float) -> None:
        """Set third element/column of ``self.twiss``."""
        pass

    @property
    @abstractmethod
    def envelope_pos(self) -> NDArray | float | None:
        """Get first element/column of ``self.envelopes``."""
        pass

    @envelope_pos.setter
    @abstractmethod
    def envelope_pos(self, value: NDArray | float) -> None:
        """Set first element/column of ``self.envelopes``."""
        pass

    @property
    @abstractmethod
    def envelope_energy(self) -> NDArray | float | None:
        """Get second element/column of ``self.envelopes``."""
        pass

    @envelope_energy.setter
    @abstractmethod
    def envelope_energy(self, value: NDArray | float) -> None:
        """Set second element/column of ``self.envelopes``."""
        pass

    @property
    @abstractmethod
    def eps(self) -> NDArray | float:
        """Return the normalized emittance."""
        pass

    @property
    @abstractmethod
    def non_norm_eps(self) -> NDArray | float:
        """Return the non-normalized emittance."""
        pass
