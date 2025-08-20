"""Gather beam parameters at the entrance of a :class:`.ListOfElements`.

For a list of the units associated with every parameter, see
:ref:`units-label`.

"""

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

from lightwin.core.beam_parameters.helper import (
    phase_space_name_hidden_in_key,
    separate_var_from_phase_space,
)
from lightwin.tracewin_utils.interface import beam_parameters_to_command
from lightwin.util.helper import recursive_getter, recursive_items
from lightwin.util.typing import (
    GETTABLE_BEAM_PARAMETERS_T,
    PHASE_SPACE_T,
    PHASE_SPACES,
)

from .phase_space.initial_phase_space_beam_parameters import (
    InitialPhaseSpaceBeamParameters,
)


@dataclass
class InitialBeamParameters:
    r"""
    Hold all emittances, envelopes, etc in various planes at a single position.

    Parameters
    ----------
    z_abs :
        Absolute position in the linac in :unit:`m`.
    gamma_kin :
        Lorentz gamma factor.
    beta_kin :
        Lorentz beta factor.
    zdelta, z, phiw, x, y, t :
        Beam parameters respectively in the :math:`[z-z\delta]`,
        :math:`[z-z']`, :math:`[\phi-W]`, :math:`[x-x']`, :math:`[y-y']` and
        :math:`[t-t']` planes.
    phiw99, x99, y99 :
        99% beam parameters respectively in the :math:`[\phi-W]`,
        :math:`[x-x']` and :math:`[y-y']` planes. Only used with multiparticle
        simulations.

    """

    z_abs: float
    gamma_kin: float
    beta_kin: float

    def __post_init__(self) -> None:
        """Declare the phase spaces without initalizing them."""
        self.zdelta: InitialPhaseSpaceBeamParameters
        self.z: InitialPhaseSpaceBeamParameters
        self.phiw: InitialPhaseSpaceBeamParameters
        self.x: InitialPhaseSpaceBeamParameters
        self.y: InitialPhaseSpaceBeamParameters
        self.t: InitialPhaseSpaceBeamParameters
        self.phiw99: InitialPhaseSpaceBeamParameters
        self.x99: InitialPhaseSpaceBeamParameters
        self.y99: InitialPhaseSpaceBeamParameters

    def __str__(self) -> str:
        """Give compact information on the data that is stored."""
        out = "\tBeamParameters:\n"
        for phase_space_name in PHASE_SPACES:
            if not hasattr(self, phase_space_name):
                continue

            phase_space = getattr(self, phase_space_name)
            out += f"{phase_space}"
        return out

    def has(self, key: str) -> bool:
        """
        Tell if the attribute exists, either directly or within a phase space.

        Notes
        -----
        ``key = 'property_phasespace'`` will return True if ``'property'``
        exists in ``phasespace``. Hence, the following two commands will have
        the same return values:

            .. code-block:: python

                self.has('twiss_zdelta')
                self.zdelta.has('twiss')

        See Also
        --------
        get

        """
        if phase_space_name_hidden_in_key(key):
            key, phase_space_name = separate_var_from_phase_space(key)
            phase_space = getattr(self, phase_space_name, None)
            return hasattr(phase_space, key) if phase_space else False
        return key in recursive_items(vars(self))

    def get(
        self,
        *keys: GETTABLE_BEAM_PARAMETERS_T,
        to_numpy: bool = True,
        none_to_nan: bool = False,
        phase_space_name: PHASE_SPACE_T | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        Get attribute values from the beam or its nested phase space objects.

        This method supports flexible ways of accessing attributes such as
        ``alpha``, ``beta``, etc., which are common to all
        :class:`.InitialPhaseSpaceBeamParameters`. Attributes can be retrieved
        directly, from a specific phase space, or using a compound key like
        ``"alpha_zdelta"``.

        If a ``phase_space_name`` is provided, the method will first attempt to
        resolve all keys through that phase space. If a key is not found there,
        it will fall back to a recursive global search.

        Notes
        -----
        All phase space components (e.g., ``x``, ``y``, ``z``, ``zdelta``)
        share the same attribute names. To disambiguate, you can either:
        - Provide a ``phase_space_name`` argument, or
        - Use compound keys such as ``"alpha_zdelta"``.

        If neither method is used and ambiguity arises, a recursive search is
        performed.

        Examples
        --------
        >>> initial_beam_parameters.get("beta", phase_space_name="zdelta")
        >>> initial_beam_parameters.get("beta_zdelta")  # Alternative
        >>> initial_beam_parameters.get("beta")  # May fail or be ambiguous

        See Also
        --------
        :meth:`has`

        Parameters
        ----------
        *keys :
            One or more names of attributes to retrieve.
        to_numpy :
            Whether to convert list-like outputs to NumPy arrays.
        none_to_nan :
            Whether to convert ``None`` values to ``np.nan``.
        phase_space_name :
            If specified, restricts the search to the given phase space
            component before falling back.
        **kwargs :
            Additional keyword arguments passed to the internal recursive
            getter.

        Returns
        -------
        Any
            A single value if one key is provided, or a tuple of values if
            multiple keys are given.

        """

        def resolve_key(key: str) -> Any:
            # 1. Try resolving directly via a given phase space (if provided
            # and key is present)
            if phase_space_name:
                phase = getattr(self, phase_space_name, None)
                if phase and hasattr(phase, key):
                    return getattr(phase, key)

            # 2. Try resolving inferred phase space (e.g., "alpha_zdelta")
            if phase_space_name_hidden_in_key(key):
                short_key, ps_name = separate_var_from_phase_space(key)
                phase = getattr(self, ps_name, None)
                if phase and hasattr(phase, short_key):
                    return getattr(phase, short_key)

            # 3. Fallback: recursive global search
            return recursive_getter(key, vars(self), **kwargs)

        values = [resolve_key(k) for k in keys]
        if to_numpy:
            values = [
                (
                    np.array(np.nan)
                    if v is None and none_to_nan
                    else np.array(v) if isinstance(v, list) else v
                )
                for v in values
            ]

        return values[0] if len(values) == 1 else tuple(values)

    @property
    def tracewin_command(self) -> list[str]:
        """Return the proper input beam parameters command."""
        _tracewin_command = self._create_tracewin_command()
        return _tracewin_command

    @property
    def sigma(self) -> np.ndarray:
        """Give value of sigma.

        .. todo::
            Could be cleaner.

        """
        sigma = np.zeros((6, 6))

        sigma_x = np.zeros((2, 2))
        if self.has("x"):
            sigma_x = self.x.sigma

        sigma_y = np.zeros((2, 2))
        if self.has("y"):
            sigma_y = self.y.sigma

        sigma_zdelta = self.zdelta.sigma

        sigma[:2, :2] = sigma_x
        sigma[2:4, 2:4] = sigma_y
        sigma[4:, 4:] = sigma_zdelta
        return sigma

    def _create_tracewin_command(
        self, warn_missing_phase_space: bool = True
    ) -> list[str]:
        """
        Turn emittance, alpha, beta from the proper phase-spaces into command.

        When phase-spaces were not created, we return np.nan which will
        ultimately lead TraceWin to take this data from its ``INI`` file.

        """
        args = []
        for phase_space_name in ("x", "y", "z"):
            if not self.has(phase_space_name):
                eps, alpha, beta = np.nan, np.nan, np.nan
                phase_spaces_are_needed = self.z_abs > 1e-10
                if warn_missing_phase_space and phase_spaces_are_needed:
                    logging.warning(
                        f"{phase_space_name} phase space not defined, keeping "
                        "default inputs from the `INI`."
                    )
            else:
                phase_space = getattr(self, phase_space_name)
                eps = phase_space.eps
                alpha = phase_space.alpha
                beta = phase_space.beta

            args.extend((eps, alpha, beta))
        return beam_parameters_to_command(*args)
