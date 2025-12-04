"""Store cavity settings that can change during an optimisation.

.. note::
    As for now, :class:`.FieldMap` is the only :class:`.Element` to have its
    properties in a dedicated object.

.. todo::
    Similar to synchronous phase, allow for V_cav to be "master" instead of
    k_e.

See Also
--------
:class:`.Field`

"""

from __future__ import annotations

import logging
import math
from collections.abc import Callable
from functools import partial
from typing import Any, NamedTuple, Self

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import minimize_scalar

from lightwin.core.em_fields.field import Field
from lightwin.physics.phases import (
    diff_angle,
    phi_0_abs_to_rel,
    phi_0_rel_to_abs,
    phi_bunch_to_phi_rf,
    phi_rf_to_phi_bunch,
)
from lightwin.physics.synchronous_phases import PHI_S_FUNC_T
from lightwin.util.typing import (
    ALLOWED_STATUS,
    GETTABLE_CAVITY_SETTINGS_T,
    REFERENCE_PHASES,
    REFERENCE_PHASES_T,
    STATUS_T,
)

#: A function that takes in the kinetic energy, the relative entry phase, the
#: cavity settings, other kwargs, and returns a dict containing propagation
#: info in the element.
TRANSF_MAT_FUNC_WRAPPER_T = Callable[
    [float, float, "CavitySettings", dict[str, Any]], dict[str, Any]
]


class CavityVars(NamedTuple):
    """Regroup main cavity settings variables."""

    k_e: float
    phi: float
    status: STATUS_T
    reference: REFERENCE_PHASES_T


class MissingAttributeError(RuntimeError):
    """Raised when a phase cannot be calculated because of missing info."""


class CavitySettings:
    """Hold the cavity parameters that can vary during optimisation.

    .. todo::
        Which syntax for when I want to compute the value of a property but not
        return it? Maybe a ``_ = self.phi_0_abs``? Maybe this case should not
        appear here, appart for when I debug.

    .. note::
        In this routine, all phases are defined in radian and are rf phases.

    .. todo::
        Determine if status should be kept here or in the field map.

    .. todo::
        For TraceWin solver, I will also need the field map index.

    """

    def __init__(
        self,
        k_e: float,
        phi: float,
        reference: REFERENCE_PHASES_T,
        status: STATUS_T,
        freq_bunch_mhz: float,
        freq_cavity_mhz: float | None = None,
        transf_mat_func_wrappers: (
            dict[str, TRANSF_MAT_FUNC_WRAPPER_T] | None
        ) = None,
        phi_s_funcs: dict[str, PHI_S_FUNC_T] | None = None,
        field: Field | None = None,
    ) -> None:
        """Instantiate the object.

        Parameters
        ----------
        k_e :
            Amplitude of the electric field.
        phi :
            Input phase in radians. Must be absolute or relative entry phase,
            or synchronous phase.
        reference :
            Name of the phase used for reference. When a particle enters the
            cavity, this is the phase that is not recomputed.
        status :
            Cavity status.
        freq_bunch_mhz :
            Bunch frequency in :unit:`MHz`.
        freq_cavity_mhz :
            Frequency of the cavity in :unit:`MHz`. The default is None, which
            happens when the :class:`.ListOfElements` is under creation and we
            did not process the ``FREQ`` commands yet.
        transf_mat_func_wrappers :
            A dictionary which keys are the different :class:`.BeamCalculator`
            ids, and values are corresponding functions to compute propagation
            of the beam.
        phi_s_funcs :
            A dictionary which keys are the different :class:`.BeamCalculator`
            ids, and values are corresponding functions to compute synchronous
            phase and accelerating voltage from the ouput of corresponding
            ``transf_mat_func_wrapper``.
        field :
            Holds the parameters that are geometry-specific, such as
            interpolated field maps.

        """
        self._w_kin: float
        self.k_e = k_e
        self._reference: REFERENCE_PHASES_T
        self.set_reference(
            reference, phi_ref=phi, ensure_can_be_calculated=False
        )

        self._phi_0_abs: float
        self._phi_0_rel: float
        self._phi_s: float
        self._v_cav_mv: float
        self._phi_rf: float
        self._phi_bunch: float
        self._acceptance_phi: float
        self._acceptance_energy: float

        self._status: STATUS_T
        self.status = status

        #: All functions that can be used to compute beam propagation in
        #: current field map
        self._transf_mat_func_wrappers: dict[
            str, TRANSF_MAT_FUNC_WRAPPER_T
        ] = (transf_mat_func_wrappers or {})
        #: All functions that can be used to compute synchronous phase and
        #: accelerating field in current field map
        self._phi_s_funcs: dict[str, PHI_S_FUNC_T] = phi_s_funcs or {}

        self._freq_bunch_mhz = freq_bunch_mhz
        self.bunch_phase_to_rf_phase: Callable[[float], float]
        self.rf_phase_to_bunch_phase: Callable[
            [float | NDArray[np.float64]], float | NDArray[np.float64]
        ]
        self.freq_cavity_mhz: float
        self.omega0_rf: float
        self.set_bunch_to_rf_freq_func(freq_cavity_mhz)

        self.field: Field
        if field is not None:
            self.field = field

        #: The function to use with current solver to compute beam propagation
        self._transf_mat_func_wrapper: TRANSF_MAT_FUNC_WRAPPER_T
        #: The function to use with current solver to compute synchronous phase
        #: and accelerating field
        self._phi_s_func: PHI_S_FUNC_T
        self._transf_mat_kwargs: dict[str, Any]

    @property
    def w_kin(self) -> float:
        return self._w_kin

    @w_kin.setter
    def w_kin(self, value: float) -> None:
        self._w_kin = value

    def __str__(self) -> str:
        """Print out the different phases/k_e, and which one is the reference.

        .. note::
            ``None`` means that the phase was not calculated.

        """
        out = f"Status: {self.status:>10} | "
        out += f"Reference: {self.reference:>10} | "
        phases_as_string = [
            self._attr_to_str(phase_name)
            for phase_name in ("_phi_0_abs", "_phi_0_rel", "_phi_s", "k_e")
        ]
        return out + " | ".join(phases_as_string)

    def __repr__(self) -> str:
        """Return the same thing as str."""
        return str(self)

    def __eq__(self, other: Self) -> bool:  # type: ignore
        """Check if two cavity settings are identical."""
        check = (
            self.k_e == other.k_e
            and self.phi_ref == other.phi_ref
            and self.reference == other.reference
        )
        # also check for phi_bunch?
        return check

    @classmethod
    def copy(cls, base: Self, cavity_vars: CavityVars | None = None) -> Self:
        """Create cavity settings, based on ``base``.

        Parameters
        ----------
        base :
            The reference :class:`CavitySettings`. *A priori*, this is the
            nominal settings.
        cavity_vars :
            Amplitude, phase, status and reference to override the ones in
            ``base``. Provided during optimization process.

        Returns
        -------
        Self
            A new :class:`CavitySettings` with modified amplitude and phase.

        """
        if cavity_vars is not None:
            k_e, phi, status, reference = cavity_vars
        else:
            reference = base.reference
            k_e = base.k_e
            phi = getattr(base, reference)
            status = base.status

        settings = cls(
            k_e=k_e,
            phi=phi,
            reference=reference,
            status=status,
            freq_bunch_mhz=base._freq_bunch_mhz,
            freq_cavity_mhz=base.freq_cavity_mhz,
            transf_mat_func_wrappers=base._transf_mat_func_wrappers,
            phi_s_funcs=base._phi_s_funcs,
            # rf_field=base.rf_field,
            field=base.field,
        )

        return settings

    def _attr_to_str(self, attr_name: str, to_deg: bool = True) -> str:
        """Give the attribute as string."""
        attr_val = getattr(self, attr_name, None)
        if attr_val is None:
            return f"{attr_name}: {'None':>7}"
        if to_deg and "phi" in attr_name:
            attr_val = math.degrees(attr_val)
            if attr_val > 180.0:
                attr_val -= 360.0
        return f"{attr_name}: {attr_val:3.5f}"

    def has(self, key: str) -> bool:
        """Tell if the required attribute is in this class."""
        return hasattr(self, key)

    def get(
        self,
        *keys: GETTABLE_CAVITY_SETTINGS_T,
        to_deg: bool = False,
        **kwargs: Any,
    ) -> Any:
        r"""Get attributes from this class or its nested members.

        Parameters
        ----------
        *keys :
            Name of the desired attributes.
        to_deg :
            Wether keys with ``"phi"`` in their name should be multiplied by
            :math:`360 / 2\pi`.
        **kwargs :
            Other arguments passed to recursive getter.

        Returns
        -------
            Attribute(s) value(s).

        """
        values = [getattr(self, key, None) for key in keys]

        if to_deg:
            values = [
                math.degrees(v) if "phi" in key and v is not None else v
                for v, key in zip(values, keys)
            ]

        return values[0] if len(values) == 1 else tuple(values)

    def _check_consistency_of_status_and_reference(self) -> None:
        r"""Perform some tests on ``status`` and ``reference``.

        1. We check that if the cavity is rephased, its reference phase is
           not :math:`phi_{0,\,\mathrm{abs}}`
        2. If the cavity is broken, we check that its reference phase is not
           synchronous because it is not defined.

        """
        if "rephased" in self.status:
            assert self.reference in ("phi_0_rel", "phi_s"), (
                f"Reference of {self} is {self.reference}, which is not "
                "consistent with it's `rephased` status."
            )
            return
        if "failed" in self.status:
            assert (
                self.reference != "phi_s"
            ), "Failed cavities with synchronous phase ref leads to bugs."

    def set_bunch_to_rf_freq_func(
        self, freq_cavity_mhz: float | None = None
    ) -> None:
        """
        Set the rf frequency, and methods to switch between freq definitions.

        This method is called a first time at the instantiation of ``self``;
        it will be called once again if a :class:`.Freq` command is found.

        Parameters
        ----------
        freq_cavity_mhz :
            Frequency in the cavity in :unit:`MHz`. If it is not provided, we
            set it to the bunch frequency.

        """
        if freq_cavity_mhz is None:
            freq_cavity_mhz = self._freq_bunch_mhz

        self.freq_cavity_mhz = freq_cavity_mhz
        bunch_phase_to_rf_phase = partial(
            phi_bunch_to_phi_rf, freq_cavity_mhz / self._freq_bunch_mhz
        )
        self.bunch_phase_to_rf_phase = bunch_phase_to_rf_phase

        rf_phase_to_bunch_phase = partial(
            phi_rf_to_phi_bunch, self._freq_bunch_mhz / freq_cavity_mhz
        )
        self.rf_phase_to_bunch_phase = rf_phase_to_bunch_phase

        self.omega0_rf = 2e6 * math.pi * freq_cavity_mhz

    # =============================================================================
    # Reference
    # =============================================================================
    @property
    def reference(self) -> REFERENCE_PHASES_T:
        """Say what is the reference phase.

        .. list-table:: Equivalents of ``reference`` in TraceWin's \
                ``FIELD_MAP``
            :widths: 50, 50
            :header-rows: 1

            * - LightWin's ``reference``
              - TraceWin
            * - ``'phi_0_rel'``
              - ``P = 0``
            * - ``'phi_0_abs'``
              - ``P = 1``
            * - ``'phi_s'``
              - ``SET_SYNC_PHASE``

        """
        return self._reference

    @reference.setter
    def reference(self, value: REFERENCE_PHASES_T) -> None:
        """Set the nature of the reference phase.

        If we are updating a previously existing ``reference``, *ie* if we are
        not in the ``__init__``, we also check that the new reference phase can
        be created.

        .. deprecated:: 0.11.0
           Prefer using :meth:`.CavitySettings.set_reference`.

        """
        logging.warning(
            "Deprecated method, prefer using CavitySettings.set_reference"
        )
        return self.set_reference(value)

    def set_reference(
        self,
        reference: REFERENCE_PHASES_T,
        phi_ref: float | None = None,
        ensure_can_be_calculated: bool = True,
    ) -> None:
        """Change the reference phase.

        Parameters
        ----------
        reference :
            The name of the new reference.
        phi_ref :
            The new value for the reference phase in :unit:`rad`. Remember that
            when the value of the reference phase is updated, all other phases
            are invalidated.
        ensure_can_be_calculated :
            To check that the new reference phase is already set or can be
            calculated.

        Raises
        ------
        MissingAttributeError
            When ``ensure_can_be_calculated = True`` and the new reference
            phase cannot be calculated.

        """
        if reference not in REFERENCE_PHASES:
            raise ValueError(f"{reference = } not in {REFERENCE_PHASES = }")

        self._reference = reference

        if phi_ref is not None:
            self.phi_ref = phi_ref

        if not ensure_can_be_calculated:
            return

        try:
            self.phi_ref
        except MissingAttributeError as e:
            raise MissingAttributeError(
                f"The new reference phase ({reference}) cannot be "
                f"calculated."
            ) from e

    @property
    def phi_ref(self) -> float:
        """Give the reference phase."""
        phi = getattr(self, self.reference)
        assert isinstance(phi, float), f"Reference phase = {phi} is invalid."
        return phi

    @phi_ref.setter
    def phi_ref(self, value: float) -> None:
        """Update the value of the reference entry phase, delete other phases.

        We delete non-reference phase to force their re-calculation.

        """
        self._delete_non_reference_phases()
        setattr(self, self.reference, value)

    def _delete_non_reference_phases(self) -> None:
        """Reset the phases that are not the reference to None."""
        for phase in REFERENCE_PHASES:
            if phase == self.reference:
                continue
            delattr(self, phase)

    # =============================================================================
    # Status
    # =============================================================================
    @property
    def status(self) -> STATUS_T:
        """Give the status of the cavity under study.

        - :data:`.STATUS_T`
        - :obj:`.STATUS_T`

        """
        return self._status

    @status.setter
    def status(self, value: STATUS_T) -> None:
        """Check that new status is allowed, set it.

        Also checks consistency between the value of the new status and the
        value of the :attr:`.reference`.

        .. todo::
            Check that beam_calc_param is still updated. As in
            FieldMap.update_status

        .. todo::
            As for now: do not update the status directly, prefer calling the
            :meth:`.FieldMap.update_status`

        """
        assert value in ALLOWED_STATUS
        self._status = value
        if value == "failed":
            self.k_e = 0.0
            self.phi_s = np.nan
            self.v_cav_mv = np.nan
            if self.reference == "phi_s":
                self.set_reference("phi_0_rel", phi_ref=0.0)

        self._check_consistency_of_status_and_reference()

    # =============================================================================
    # Absolute phi_0
    # =============================================================================
    @property
    def phi_0_abs(self) -> float:
        """Get the absolute entry phase, compute if necessary."""
        if hasattr(self, "_phi_0_abs"):
            return self._phi_0_abs

        for key in ("phi_rf", "phi_0_rel"):
            if not hasattr(self, key):
                raise MissingAttributeError(
                    f"{self = }: cannot compute phi_0_abs from phi_0_rel if "
                    f"{key} is not defined."
                )

        self.phi_0_abs = phi_0_rel_to_abs(self.phi_0_rel, self._phi_rf)
        return self._phi_0_abs

    @phi_0_abs.setter
    def phi_0_abs(self, value: float) -> None:
        """Set the absolute entry phase."""
        self._phi_0_abs = value

    @phi_0_abs.deleter
    def phi_0_abs(self) -> None:
        """Delete attribute."""
        if not hasattr(self, "_phi_0_abs"):
            return
        del self._phi_0_abs

    # =============================================================================
    # Relative phi_0
    # =============================================================================
    @property
    def phi_0_rel(self) -> float:
        """Get the relative entry phase, compute it if necessary."""
        if hasattr(self, "_phi_0_rel"):
            return self._phi_0_rel

        if hasattr(self, "_phi_0_abs"):
            if not hasattr(self, "phi_rf"):
                raise MissingAttributeError(
                    f"{self = }: cannot compute phi_0_rel from phi_0_abs if "
                    "phi_rf is not defined."
                )
            self.phi_0_rel = phi_0_abs_to_rel(self._phi_0_abs, self._phi_rf)
            return self._phi_0_rel

        if not hasattr(self, "_phi_s"):
            raise MissingAttributeError(
                f"{self = }: phi_0_abs, phi_0_rel, phi_s are all "
                "uninitialized."
            )

        self.phi_0_rel = self._phi_s_to_phi_0_rel(self._phi_s)
        return self._phi_0_rel

    @phi_0_rel.setter
    def phi_0_rel(self, value: float) -> None:
        """Set the relative entry phase."""
        self._phi_0_rel = value

    @phi_0_rel.deleter
    def phi_0_rel(self) -> None:
        """Delete attribute."""
        if not hasattr(self, "_phi_0_rel"):
            return
        del self._phi_0_rel

    # =============================================================================
    # Synchronous phase, accelerating voltage
    # =============================================================================
    @property
    def phi_s(self) -> float:
        """Get the synchronous phase, and compute it if necessary.

        .. note::
           It is mandatory for the calculation of this quantity to compute
           propagation of the particle in the cavity.

        See Also
        --------
        set_cavity_parameters_methods

        """
        if hasattr(self, "_phi_s"):
            return self._phi_s

        for key in ("phi_rf", "phi_0_rel"):
            if not hasattr(self, key):
                raise MissingAttributeError(
                    f"{self}: cannot compute phi_s if {key} was not set."
                )

        self._phi_s = self._phi_0_rel_to_cavity_parameters(self.phi_0_rel)[1]
        return self._phi_s

    @phi_s.setter
    def phi_s(self, value: float) -> None:
        """Set the synchronous phase to desired value."""
        self._phi_s = value
        del self.acceptance_phi
        del self.acceptance_energy

    @phi_s.deleter
    def phi_s(self) -> None:
        """Delete the synchronous phase."""
        if not hasattr(self, "_phi_s"):
            return
        del self._phi_s
        del self.acceptance_phi
        del self.acceptance_energy

    def set_cavity_parameters_methods(
        self,
        solver_id: str,
        transf_mat_function_wrapper: Callable,
        phi_s_func: PHI_S_FUNC_T | None = None,
    ) -> None:
        """Set the generic methods to compute beam propagation, cavity params.

        This function is called within two contexts.

         * When initializing the :class:`.BeamCalculator` specific parameters
           (:class:`.ElementBeamCalculatorParameters`).
         * When re-initalizing the :class:`.ElementBeamCalculatorParameters`
           because the ``status`` of the cavity changed, and in particular when
           it switches to ``'failed'``. In this case, the ``_phi_s_func``
           is not altered.

        Parameters
        ----------
        solver_id :
            The name of the solver for which functions must be changed.
        transf_mat_function_wrapper :
            A function that compute the propagation of the beam.
        phi_s_func :
            A function that takes in the output of
            ``transf_mat_function_wrapper`` and returns the accelerating
            voltage in :unit:`MV` and the synchronous phase in :math:`rad`.
            The default is None, which happens when we break the cavity and
            only the ``transf_mat_function_wrapper`` needs to be updated. In
            this case, the synchronous phase function is left unchanged.

        See Also
        --------
        set_cavity_parameters_arguments

        """
        self._transf_mat_func_wrappers[solver_id] = transf_mat_function_wrapper
        if phi_s_func is None:
            return
        self._phi_s_funcs[solver_id] = phi_s_func

    def set_cavity_parameters_arguments(
        self, solver_id: str, w_kin: float, **kwargs
    ) -> None:
        r"""Adapt the cavity parameters methods to beam with ``w_kin``.

        This function must be called:

        * When the kinetic energy at the entrance of the cavity is changed
          (like this occurs during optimisation process)
        * When the synchronous phase must be calculated with another solver.

        Parameters
        ----------
        solver_id :
            Name of the solver that will compute :math:`V_\mathrm{cav}` and
            :math:`\phi_s`.
        w_kin :
            Kinetic energy of the synchronous particle at the entry of the
            cavity.
        kwargs :
            Other keyword arguments that will be passed to the function that
            will compute propagation of the beam in the :class:`.FieldMap`.
            Note that you should check that ``phi_0_rel`` key is removed in
            your :class:`.BeamCalculator`, to avoid a clash in the
            `_phi_0_rel_to_cavity_parameters` function.

        See Also
        --------
        set_cavity_parameters_methods

        """
        self._transf_mat_func_wrapper = self._transf_mat_func_wrappers[
            solver_id
        ]
        self._phi_s_func = self._phi_s_funcs[solver_id]
        self.w_kin = w_kin
        self._transf_mat_kwargs = kwargs

    def _phi_0_rel_to_cavity_parameters(
        self, phi_0_rel: float
    ) -> tuple[float, float]:
        """Compute cavity parameters based on relative entry phase.

        Parameters
        ----------
        phi_0_rel :
            Relative entry phase in radians.

        Returns
        -------
            A tuple containing (V_cav, phi_s).

        Raises
        ------
        MissingAttributeError
            If the transfer matrix function or phi_s function is not set.

        """
        for key in ("_transf_mat_func_wrapper", "_phi_s_func"):
            if hasattr(self, key):
                continue
            raise MissingAttributeError(
                f"Cannot compute cavity parameters from phi_0_rel if {key} is "
                "not set."
            )
        results = self._transf_mat_func_wrapper(
            w_kin=self.w_kin,
            phi_0_rel=phi_0_rel,
            cavity_settings=self,
            **self._transf_mat_kwargs,
        )
        cavity_parameters = self._phi_s_func(**results)
        return cavity_parameters

    def _residual_func(self, phi_0_rel: float, phi_s: float) -> float:
        """Calculate the squared difference between target and computed phi_s.

        Parameters
        ----------
        phi_0_rel :
            Relative entry phase in radians.
        phi_s :
            Target synchronous phase in radians.

        Returns
        -------
            The squared difference between the target and computed phi_s.

        """
        calculated_phi_s = self._phi_0_rel_to_cavity_parameters(phi_0_rel)[1]
        residual = diff_angle(phi_s, calculated_phi_s)
        return residual**2

    def _phi_s_to_phi_0_rel(self, phi_s: float) -> float:
        """Find the relative entry phase that yields the target sync phase.

        Parameters
        ----------
        phi_s :
            Target synchronous phase in radians.

        Returns
        -------
            Relative entry phase in radians that achieves the target phi_s.

        Raises
        ------
        RuntimeError
            If the optimization fails to find a solution.

        """
        out = minimize_scalar(
            self._residual_func, bounds=(0.0, 2.0 * math.pi), args=(phi_s,)
        )
        if not out.success:
            logging.error("Synch phase not found")
        return out.x

    @property
    def v_cav_mv(self) -> float | None:
        """Get the accelerating voltage, and compute it if necessary.

        .. note::
            It is mandatory for the calculation of this quantity to compute
            propagation of the particle in the cavity.

        See Also
        --------
        set_cavity_parameters_methods

        """
        if hasattr(self, "_v_cav_mv"):
            return self._v_cav_mv
        try:
            self.phi_s
            return self._v_cav_mv
        except MissingAttributeError as e:
            raise MissingAttributeError(
                "Calculating phi_s should set self.v_cav_mv as well, but this"
                " operation failed with error:"
            ) from e

    @v_cav_mv.setter
    def v_cav_mv(self, value: float) -> None:
        """Set accelerating voltage to desired value."""
        self._v_cav_mv = value

    # =============================================================================
    # Phase of synchronous particle
    # =============================================================================
    @property
    def phi_rf(self) -> float:
        """Get the rf phase of synch particle at entrance of cavity."""
        return self._phi_rf

    @phi_rf.setter
    def phi_rf(self, value: float) -> None:
        """Set the new synch particle entry phase, remove value to update.

        We also remove the synchronous phase. In most of the situations, we
        also remove ``phi_0_rel`` and keep ``phi_0_abs`` (we must ensure that
        ``phi_0_abs`` was previously set).
        The exception is when the cavity has the ``'rephased'`` status. In this
        case, we keep the relative ``phi_0`` and absolute ``phi_0`` will be
        recomputed when/if it is called.

        Parameters
        ----------
        value :
            New rf phase of the synchronous particle at the entrance of the
            cavity.

        """
        self._phi_rf = value
        self._phi_bunch = self.rf_phase_to_bunch_phase(value)
        self._delete_non_reference_phases()

        # if self.status == 'rephased (in progress)':
        #     self.phi_0_rel
        #     self._phi_0_abs = None
        #     return
        # self.phi_0_abs
        # self._phi_0_rel = None

    @property
    def phi_bunch(self) -> float:
        """Return the entry phase of the synchronous particle (bunch ref)."""
        return self._phi_bunch

    @phi_bunch.setter
    def phi_bunch(self, value: float) -> None:
        """Convert bunch to rf frequency."""
        self._phi_bunch = value
        self._phi_rf = self.bunch_phase_to_rf_phase(value)
        self._delete_non_reference_phases()

    def shift_phi_bunch(
        self, delta_phi_bunch: float, check_positive: bool = False
    ) -> None:
        """Shift the synchronous particle entry phase by ``delta_phi_bunch``.

        This is mandatory when the reference phase is changed. In particular,
        it is the case when studying a sub-list of elements with
        :class:`.TraceWin`. With this solver, the entry phase in the first
        element of the sub-:class:`.ListOfElements` is always 0.0, even if is
        not the first element of the linac.

        Parameters
        ----------
        delta_phi_bunch :
            Phase difference between the new first element of the linac and the
            previous first element of the linac.

        Examples
        --------
        >>> phi_in_1st_element = 0.
        >>> phi_in_20th_element = 55.
        >>> 25th_element: FieldMap
        >>> 25th_element.cavity_settings.shift_phi_bunch(
        >>> ... phi_in_20th_element - phi_in_1st_element
        >>> )  # now phi_0_abs and phi_0_rel are properly understood

        """
        self.phi_bunch = self._phi_bunch - delta_phi_bunch
        if not check_positive:
            return
        assert (
            self.phi_bunch >= 0.0
        ), "The phase of the synchronous particle should never be negative."

    # =============================================================================
    # Acceptances
    # =============================================================================
    @property
    def acceptance_phi(self) -> float | None:
        """Get the phase acceptance."""
        return getattr(self, "_acceptance_phi", None)

    @acceptance_phi.setter
    def acceptance_phi(self, value: float) -> None:
        """Set the phase acceptance to the desired value."""
        self._acceptance_phi = value

    @acceptance_phi.deleter
    def acceptance_phi(self):
        """Delete the phase acceptance."""
        if hasattr(self, "_acceptance_phi"):
            del self._acceptance_phi

    @property
    def acceptance_energy(self) -> float | None:
        """Get the energy acceptance."""
        return getattr(self, "_acceptance_energy", None)

    @acceptance_energy.setter
    def acceptance_energy(self, value: float) -> None:
        """Set the energy acceptance to the desired value."""
        self._acceptance_energy = value

    @acceptance_energy.deleter
    def acceptance_energy(self):
        """Delete the energy acceptance."""
        if hasattr(self, "_acceptance_energy"):
            del self._acceptance_energy

    def plot(self) -> None:
        """Plot the profile of the electric field."""
        return self.field.plot(self.k_e, self.phi_0_rel)


def _get_valid_func(obj: object, func_name: str, solver_id: str) -> Callable:
    """Get the function in ``func_name`` for ``solver_id``."""
    all_funcs = getattr(obj, func_name, None)
    assert isinstance(all_funcs, dict), (
        f"Attribute {func_name} of {object} should be a dict[str, Callable] "
        f"but is {all_funcs}. "
        "Check CavitySettings.set_cavity_parameters_methods and"
        "CavitySettings.set_cavity_parameters_arguments"
    )
    func = all_funcs.get(solver_id, None)
    assert isinstance(func, Callable), (
        f"No Callable {func_name} was found in {object} for {solver_id = }"
        "Check CavitySettings.set_cavity_parameters_methods and"
        "CavitySettings.set_cavity_parameters_arguments"
    )
    return func
