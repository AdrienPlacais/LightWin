"""Define a class to hold optimisation objective with its ideal value."""

import logging
from abc import ABC, abstractmethod
from collections.abc import Collection
from typing import Any, Self

from numpy.typing import NDArray

from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.beam_parameters.helper import mismatch_from_arrays
from lightwin.util.typing import (
    GETTABLE_BEAM_PARAMETERS,
    GETTABLE_BEAM_PARAMETERS_T,
    GETTABLE_SIMULATION_OUTPUT,
    GETTABLE_SIMULATION_OUTPUT_T,
)


class Objective(ABC):
    """Hold an objective and methods to evaluate it."""

    #: List of authorized values for the ``get_key``. Checked by the
    #: :meth:`._check_get_arguments` method
    _gettable: Collection[str] = GETTABLE_SIMULATION_OUTPUT

    def __init__(
        self,
        name: str,
        weight: float,
        get_key: GETTABLE_SIMULATION_OUTPUT_T,
        get_kwargs: dict[str, Any],
        ideal_value: float | tuple[float, float],
        descriptor: str | None = None,
    ) -> None:
        """Hold an objective and methods to evaluate it.

        Parameters
        ----------
        name :
            A short string to describe the objective and access to it.
        weight :
            A scaling constant to set the weight of current objective.
        get_key :
            Name of the quantity to get.
        get_kwargs :
            Keyword arguments for the :meth:`.SimulationOutput.get` method. We
            do not enforce its validity, but in general you will want to define
            the keys ``elt`` and ``pos``. If objective concerns a phase, you
            may want to precise the ``to_deg`` key. You also should explicit
            the ``to_numpy`` key.
        ideal_value :
            The ideal value or range of values that we should tend to.
        descriptor :
            A longer string to explain the objective.

        """
        get_key, get_kwargs = self._check_get_arguments(get_key, get_kwargs)
        self.name: str = name
        self.weight: float = weight
        self.get_key: GETTABLE_SIMULATION_OUTPUT_T = get_key
        self.get_kwargs: dict[str, Any] = get_kwargs
        self.ideal_value: Any = ideal_value
        self.descriptor = " ".join((descriptor or "").split())

    def __str__(self) -> str:
        """Give objective information value."""
        message = self.base_str()
        if isinstance(self.ideal_value, float):
            message += f"{self.ideal_value:+.14e}"
            return message
        if isinstance(self.ideal_value, tuple):
            message += (
                f"{self.ideal_value[0]:+.2e} ~ {self.ideal_value[1]:+.2e}"
            )
            return message
        if self.ideal_value is None:
            message += f"{'None': ^21}"
            return message

        return message

    def base_str(self) -> str:
        """Tell nature and position of objective."""
        message = f"{self.get_key:>23}"

        elt = str(self.get_kwargs.get("elt", "NA"))
        message += f" @elt {elt:>5}"

        pos = str(self.get_kwargs.get("pos", "NA"))
        message += f" ({pos:>3}) | {self.weight:>5} | "
        return message

    def _value_getter(
        self,
        simulation_output: SimulationOutput,
        handle_missing_elt: bool = False,
    ) -> float:
        """Get desired value using :meth:`.SimulationOutput.get` method.

        .. seealso::
            :func:`.simulation_output.factory._element_to_index`

        Parameters
        ----------
        simulation_output :
            Object to ``get`` ``self.get_key`` from.
        handle_missing_elt :
            Automatically look for an equivalent :class:`.Element` when the
            current one is not in :class:`.SimulationOutput`. Set it to
            ``True`` when calculating reference value (reference
            :class:`.Element` is not in compensating list of elements).

        """
        return simulation_output.get(
            self.get_key,
            **self.get_kwargs,
            handle_missing_elt=handle_missing_elt,
        )

    def _check_get_arguments(
        self,
        get_key: GETTABLE_SIMULATION_OUTPUT_T,
        get_kwargs: dict[str, Any],
    ) -> tuple[GETTABLE_SIMULATION_OUTPUT_T, dict[str, Any]]:
        """Check validity of ``get_args``, ``get_kwargs``.

        In general, residuals evaluation relies on a
        :meth:`.SimulationOutput.get` method. This method uses ``get_args`` and
        ``get_kwargs``; we perform here some basic checks.

        """
        if get_key not in self._gettable:
            logging.warning(
                f"{get_key = } may not be gettable by SimulationOutput.get "
                f"method. Authorized values are:\n{self._gettable = }"
            )

        advised_keys = ["elt", "pos", "to_numpy"]
        if "phi" in get_key:
            advised_keys.append("to_deg")
        for key in advised_keys:
            if key in get_kwargs:
                continue
            logging.warning(
                f"{key = } is recommended to avoid undetermined behavior but "
                "was not found."
            )
        return get_key, get_kwargs

    @staticmethod
    def str_header() -> str:
        """Give a header to explain what :meth:`__str__` returns."""
        header = f"{'What, where, etc': ^40} | {'wgt.':>5} | "
        header += f"{'ideal value': ^21}"
        return header

    @abstractmethod
    def _compute_residuals(self, *args, **kwargs) -> float:
        """Compute residual (loss), for a given value.

        In general, you will want to call this function from
        :meth:`.Objective.evaluate`.

        """
        raise NotImplementedError

    def evaluate(self, simulation_output: SimulationOutput) -> float:
        """Compute residuals of this objective.

        Parameters
        ----------
        simulation_output :
            Object containing simulation results of the broken linac.

        Returns
        -------
            Difference between current evaluation and ``ideal_value`` value for
            ``self.name``, scaled by ``self.weight``.

        """
        value = self._value_getter(simulation_output)
        return self._compute_residuals(value)


class RetrieveArbitrary(Objective):
    """Retrieve arbitrary value given by user."""

    def __init__(
        self,
        name: str,
        weight: float,
        get_key: GETTABLE_SIMULATION_OUTPUT_T,
        get_kwargs: dict[str, Any],
        ideal_value: float,
        descriptor: str | None = None,
    ) -> None:
        """
        Set complementary :meth:`.SimulationOutput.get` flags, reference value.

        Parameters
        ----------
        name :
            A short string to describe the objective and access to it.
        weight :
            A scaling constant to set the weight of current objective.
        get_key :
            Name of the quantity to get.
        get_kwargs :
            Keyword arguments for the :meth:`.SimulationOutput.get` method. We
            do not check its validity, but in general you will want to define
            the keys ``elt`` and ``pos``. If objective concerns a phase, you
            may want to precise the ``to_deg`` key. You also should explicit
            the ``to_numpy`` key.
        ideal_value :
            The value to retrieve.
        descriptor :
            A longer string to explain the objective.

        """
        self.ideal_value: float
        super().__init__(
            name=name,
            weight=weight,
            get_key=get_key,
            get_kwargs=get_kwargs,
            descriptor=descriptor,
            ideal_value=ideal_value,
        )

    def _compute_residuals(self, value: float) -> float:
        """Compute residuals, that we want to minimize."""
        return self.weight * abs(value - self.ideal_value)


class MinimizeDifferenceWithRef(Objective):
    """A simple difference at a given point between ref and fix."""

    def __init__(
        self,
        name: str,
        weight: float,
        get_key: GETTABLE_SIMULATION_OUTPUT_T,
        get_kwargs: dict[str, Any],
        reference: SimulationOutput,
        descriptor: str | None = None,
    ) -> None:
        """
        Set complementary :meth:`.SimulationOutput.get` flags, reference value.

        Parameters
        ----------
        name :
            A short string to describe the objective and access to it.
        weight :
            A scaling constant to set the weight of current objective.
        get_key :
            Name of the quantity to get.
        get_kwargs :
            Keyword arguments for the :meth:`.SimulationOutput.get` method. We
            do not check its validity, but in general you will want to define
            the keys ``elt`` and ``pos``. If objective concerns a phase, you
            may want to precise the ``to_deg`` key. You also should explicit
            the ``to_numpy`` key.
        reference :
            The reference simulation output from which the ideal value will be
            taken.
        descriptor :
            A longer string to explain the objective.

        """
        self.ideal_value: float
        super().__init__(
            name=name,
            weight=weight,
            get_key=get_key,
            get_kwargs=get_kwargs,
            descriptor=descriptor,
            ideal_value=self._value_getter(reference, handle_missing_elt=True),
        )
        self._check_ideal_value()

    def _check_ideal_value(self) -> None:
        """Assert the the reference value is a float."""
        if not isinstance(self.ideal_value, float):
            logging.warning(
                f"Tried to get {self.get_key} with {self.get_kwargs}, which "
                f"returned {self.ideal_value} instead of a float."
            )

    def _compute_residuals(self, value: float) -> float:
        """Compute residuals, that we want to minimize."""
        return self.weight * abs(value - self.ideal_value)


class MinimizeMismatch(Objective):
    """Minimize a mismatch factor."""

    _gettable = GETTABLE_BEAM_PARAMETERS

    def __init__(
        self,
        name: str,
        weight: float,
        get_key: GETTABLE_BEAM_PARAMETERS_T,
        get_kwargs: dict[str, Any],
        reference: SimulationOutput,
        descriptor: str | None = None,
    ) -> None:
        """
        Set complementary :meth:`.SimulationOutput.get` flags, reference value.

        Parameters
        ----------
        name :
            A short string to describe the objective and access to it.
        weight :
            A scaling constant to set the weight of current objective.
        get_key :
            Must contain 'twiss' plus the name of a phase-space, or simply
            'twiss' and the phase-space is defined in ``get_kwargs``.
        get_kwargs :
            Keyword arguments for the :meth:`.SimulationOutput.get` method. We
            do not check its validity, but in general you will want to define
            the keys ``elt`` and ``pos``. You should also define the
            ``phase_space_name`` key if it is not defined in the ``get_key``.
        reference :
            The reference simulation output from which the Twiss parameters
            will be taken.
        descriptor :
            A longer string to explain the objective.

        """
        self.ideal_value: float
        self.get_key: GETTABLE_BEAM_PARAMETERS_T
        super().__init__(
            name=name,
            weight=weight,
            get_key=get_key,
            get_kwargs=get_kwargs,
            descriptor=descriptor,
            ideal_value=0.0,
        )
        self._twiss_ref = self._twiss_getter(reference)

    def _check_get_arguments(
        self, get_key: GETTABLE_SIMULATION_OUTPUT_T, get_kwargs: dict[str, Any]
    ) -> tuple[GETTABLE_SIMULATION_OUTPUT_T, dict[str, Any]]:
        """Add default values if necessary."""
        if "twiss" not in get_key:
            logging.warning(
                "The get_key should contain 'twiss'. Taking 'twiss' and "
                "setting phase space to zdelta."
            )
            get_key = "twiss"
            get_kwargs["phase_space_name"] = "zdelta"
        return super()._check_get_arguments(get_key, get_kwargs)

    def _twiss_getter(self, simulation_output: SimulationOutput) -> NDArray:
        """Get desired value using :meth:`.SimulationOutput.get` method."""
        return simulation_output.beam_parameters.get(
            self.get_key, **self.get_kwargs
        )

    def evaluate(self, simulation_output: SimulationOutput) -> float:
        twiss_fix = self._twiss_getter(simulation_output)
        return self._compute_residuals(twiss_fix)

    def _compute_residuals(self, twiss_fix: NDArray) -> float:
        """Compute residuals, that we want to minimize."""
        res = mismatch_from_arrays(self._twiss_ref, twiss_fix)[0]
        return self.weight * res


class QuantityIsBetween(Objective):
    """Quantity must be within some bounds."""

    def __init__(
        self,
        name: str,
        weight: float,
        get_key: GETTABLE_SIMULATION_OUTPUT_T,
        get_kwargs: dict[str, Any],
        limits: tuple[float, float],
        descriptor: str | None = None,
        loss_function: str | None = None,
    ) -> None:
        """
        Set complementary :meth:`.SimulationOutput.get` flags, reference value.

        Parameters
        ----------
        name :
            A short string to describe the objective and access to it.
        weight :
            A scaling constant to set the weight of current objective.
        get_key :
            Name of the quantity to get.
        get_kwargs :
            Keyword arguments for the :meth:`.SimulationOutput.get` method. We
            do not check its validity, but in general you will want to define
            the keys ``elt`` and ``pos``. If objective concerns a phase, you
            may want to precise the ``to_deg`` key. You also should explicit
            the ``to_numpy`` key.
        limits :
            Lower and upper bound for the value.
        loss_function :
            Indicates how the residuals are handled when the quantity is
            outside the limits. Currently not implemented.

        """
        self.ideal_value: tuple[float, float]
        super().__init__(
            name=name,
            weight=weight,
            get_key=get_key,
            get_kwargs=get_kwargs,
            ideal_value=limits,
            descriptor=descriptor,
        )
        if loss_function is not None:
            logging.warning("Loss functions not implemented.")

    @classmethod
    def relative_to_reference(
        cls,
        name: str,
        weight: float,
        get_key: GETTABLE_SIMULATION_OUTPUT_T,
        get_kwargs: dict[str, Any],
        relative_limits: tuple[float, float],
        reference_value: float,
        descriptor: str | None = None,
        loss_function: str | None = None,
    ) -> Self:
        r"""
        Set complementary :meth:`.SimulationOutput.get` flags, reference value.

        Parameters
        ----------
        name :
            A short string to describe the objective and access to it.
        weight :
            A scaling constant to set the weight of current objective.
        get_key :
            Name of the quantity to get.
        get_kwargs :
            Keyword arguments for the :meth:`.SimulationOutput.get` method. We
            do not check its validity, but in general you will want to define
            the keys ``elt`` and ``pos``. If objective concerns a phase, you
            may want to precise the ``to_deg`` key. You also should explicit
            the ``to_numpy`` key.
        relative_limits :
            Lower and upper bound for the value, in :unit:`\%` wrt
            ``reference_value``. First value should be lower than
            :math:`100\%`, second value higher than :math:`100\%`.
        reference_value :
            Ideal value.
        loss_function :
            Indicates how the residuals are handled when the quantity is
            outside the limits. Currently not implemented.

        """
        assert relative_limits[0] <= 100.0 and relative_limits[1] >= 100.0, (
            f"{relative_limits = } but should look like `(80, 135)` (which "
            "means: objective must be 80% and 135% of reference value."
        )
        limits: tuple[float, float]
        limits = (
            reference_value * 1e-2 * relative_limits[0],
            reference_value * 1e-2 * relative_limits[1],
        )
        if reference_value <= 0.0:
            logging.info(
                f"{reference_value = } is negative. Inverting bounds to keep "
                "limits[0] < limits[1]."
            )
            limits = (limits[1], limits[0])
        return cls(
            name=name,
            weight=weight,
            get_key=get_key,
            get_kwargs=get_kwargs,
            limits=limits,
            descriptor=descriptor,
            loss_function=loss_function,
        )

    def __str__(self) -> str:
        """Give objective information value."""
        message = self.base_str()
        message += f"{self.ideal_value[0]:+.2e} ~ {self.ideal_value[1]:+.2e}"  # type: ignore
        return message

    def _compute_residuals(self, value: float) -> float:
        """Compute residual for ``value`` with respect to the ideal interval.

        This method applies a quadratic penalty if the value lies outside the
        target interval defined by ``self.ideal_value``. No penalty is applied
        when the value is within the interval.

        The loss function is:

        - 0 if ``ideal_value[0] <= value <= ideal_value[1]``
        - ``weight * (value - bound)^2`` otherwise, where bound is the violated
          boundary.

        Parameters
        ----------
        value :
            The value to evaluate.

        Returns
        -------
            The computed residual (loss).

        """
        if value < self.ideal_value[0]:
            return self.weight * (value - self.ideal_value[0]) ** 2
        if value > self.ideal_value[1]:
            return self.weight * (value - self.ideal_value[1]) ** 2
        return 0.0
