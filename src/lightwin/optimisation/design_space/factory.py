"""Define factory and presets to handle variables, constraints, limits, etc..

.. note::
    If you add your own DesignSpaceFactory preset, do not forget to add it to
    the list of supported presets in :mod:`.optimisation.design_space_specs`.

"""

import logging
from abc import ABC
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from lightwin.core.elements.element import Element
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.list_of_elements.helper import equivalent_elt
from lightwin.optimisation.design_space.constraint import Constraint
from lightwin.optimisation.design_space.design_space import DesignSpace
from lightwin.optimisation.design_space.helper import (
    LIMITS_CALCULATORS,
    same_value_as_nominal,
)
from lightwin.optimisation.design_space.variable import Variable
from lightwin.util.typing import GETTABLE_FIELD_MAP, VARIABLES_T


@dataclass
class DesignSpaceFactory(ABC):
    """
    Base class to handle :class:`.Variable` and :class:`.Constraint` creation.

    Parameters
    ----------
    reference_elements :
       All the elements with the reference setting.
    compensating_elements :
        The elements from the linac under fixing that will be used for
        compensation.
    design_space_kw :
        The entries of ``[design_space]`` in ``TOML`` configuration file.

    """

    design_space_kw: dict[str, Path]

    def __post_init__(self):
        """Declare complementary variables."""
        self.variables_names: Sequence[VARIABLES_T]
        self.variables_filepath: Path
        if not hasattr(self, "variables_names"):
            raise ValueError("You must define at least one variable name.")

        self.constraints_names: Sequence[VARIABLES_T]
        self.constraints_filepath: Path
        if not hasattr(self, "constraints_names"):
            self.constraints_names = ()

        from_file = self.design_space_kw["from_file"]
        if from_file:
            self.use_files(**self.design_space_kw)

    def _check_can_be_retuned(
        self, compensating_elements: Collection[Element]
    ) -> None:
        """Check that given elements can be retuned."""
        assert all([elt.can_be_retuned for elt in compensating_elements])

    def _run_variables(
        self,
        compensating_elements: Collection[FieldMap],
        reference_elements: Collection[Element],
    ) -> list[Variable]:
        """Set up all the required variables."""
        variables = []
        for var_name in self.variables_names:
            for cav in compensating_elements:
                ref_cav = equivalent_elt(reference_elements, cav)
                variable = Variable(
                    name=var_name,
                    element_name=str(cav),
                    limits=self._get_limits_from_kw(
                        var_name, ref_cav, reference_elements
                    ),
                    x_0=self._get_initial_value_from_kw(var_name, ref_cav),
                )
                variables.append(variable)
        return variables

    def _run_constraints(
        self,
        compensating_elements: Collection[Element],
        reference_elements: Collection[Element],
    ) -> list[Constraint]:
        """Set up all the required constraints."""
        constraints = []
        for constraint_name in self.constraints_names:
            for cav in compensating_elements:
                ref_cav = equivalent_elt(reference_elements, cav)
                constraint = Constraint(
                    name=constraint_name,
                    element_name=str(cav),
                    limits=self._get_limits_from_kw(
                        constraint_name, ref_cav, reference_elements
                    ),
                )
                constraints.append(constraint)
        return constraints

    def create(
        self,
        compensating_elements: Sequence[Element],
        reference_elements: Sequence[Element],
    ) -> DesignSpace:
        """Set up variables and constraints."""
        self._check_can_be_retuned(compensating_elements)
        variables = self._run_variables(
            compensating_elements, reference_elements
        )
        constraints = self._run_constraints(
            compensating_elements, reference_elements
        )
        design_space = DesignSpace(variables, constraints)
        return design_space

    def _get_initial_value_from_kw(
        self, variable: VARIABLES_T, reference_element: FieldMap
    ) -> float:
        """Select initial value for given variable.

        The default behavior is to return the value of ``variable`` from
        ``reference_element``, which is a good starting point for optimisation.

        Parameters
        ----------
        variable :
            The variable from which you want the limits.
        reference_element :
            The element in its nominal tuning.

        Returns
        -------
            Initial value.

        """
        assert variable in GETTABLE_FIELD_MAP, (
            f"{variable = } does not belong to the FieldMap gettable "
            f"attributes:\n{GETTABLE_FIELD_MAP}"
        )
        return same_value_as_nominal(variable, reference_element)

    def _get_limits_from_kw(
        self,
        variable: VARIABLES_T,
        reference_element: Element,
        reference_elements: Collection[Element],
    ) -> tuple[float, float]:
        """Select limits for given variable.

        Call this method for classic limits.

        Parameters
        ----------
        variable :
            The variable from which you want the limits.
        reference_element :
            The element in its nominal tuning.
        reference_elements :
            List of reference elements.

        Returns
        -------
            Lower and upper limit for current variable.

        """
        limits_calculator = LIMITS_CALCULATORS[variable]
        return limits_calculator(
            reference_element=reference_element,
            reference_elements=reference_elements,
            **self.design_space_kw,
        )

    def use_files(
        self,
        variables_filepath: Path,
        constraints_filepath: Path | None = None,
        **design_space_kw: Path,
    ) -> Self:
        """Tell factory to generate design space from the provided files.

        Parameters
        ----------
        variables_filepath :
            Path to the ``variables.csv`` file.
        constraints_filepath :
            Path to the ``constraints.csv`` file.

        """
        self.variables_filepath = variables_filepath
        if constraints_filepath is not None:
            self.constraints_filepath = constraints_filepath
        self.create = self._create_from_file
        if design_space_kw:
            self.design_space_kw.update(design_space_kw)
        return self

    def _create_from_file(
        self,
        compensating_elements: list[Element],
        reference_elements: list[Element] | None = None,
    ) -> DesignSpace:
        """Use the :meth:`.DesignSpace.from_files` constructor.

        Parameters
        ----------
        variables_names :
            Name of the variables to create.
        constraints_names :
            Name of the constraints to create. The default is None.

        """
        self._check_can_be_retuned(compensating_elements)
        if not hasattr(self, "variables_filepath"):
            raise AttributeError(
                "variables_filepath must be defined before use."
            )
        constraints_filepath = getattr(self, "constraints_filepath", None)

        elements_names = tuple([str(elt) for elt in compensating_elements])
        design_space = DesignSpace.from_files(
            elements_names,
            self.variables_filepath,
            self.variables_names,
            constraints_filepath,
            self.constraints_names,
        )
        return design_space


# =============================================================================
# Unconstrained design spaces
# =============================================================================
@dataclass
class AbsPhaseAmplitude(DesignSpaceFactory):
    r"""Optimise over :math:`\phi_{0,\,\mathrm{abs}}` and :math:`k_e`."""

    variables_names = ("phi_0_abs", "k_e")


@dataclass
class RelPhaseAmplitude(DesignSpaceFactory):
    r"""Optimise over :math:`\phi_{0,\,\mathrm{rel}}` and :math:`k_e`.

    The same as :class:`AbsPhaseAmplitude`, but the phase variable is
    :math:`\phi_{0,\,\mathrm{rel}}` instead of :math:`\phi_{0,\,\mathrm{abs}}`.
    It may be better for convergence, because it makes cavities more
    independent.

    """

    variables_names = ("phi_0_rel", "k_e")


@dataclass
class SyncPhaseAmplitude(DesignSpaceFactory):
    r"""Optimise over :math:`\phi_s` and :math:`k_e`.

    Synchronous phases outside of the bounds will not ocurr, without setting
    any :class:`.Constraint`. This kind of optimisation takes more time as we
    need, for every iteration of the :class:`.OptimisationAlgorithm`, to find
    the :math:`\phi_{0,\,\mathrm{rel}}` that corresponds to the desired
    :math:`\phi_s`.

    """

    variables_names = ("phi_s", "k_e")


# =============================================================================
# Design spaces with constraints; OptimisationAlgorithm must support it!
# =============================================================================
@dataclass
class AbsPhaseAmplitudeWithConstrainedSyncPhase(DesignSpaceFactory):
    r"""
    Optimise :math:`\phi_{0,\,\mathrm{abs}}`, :math:`k_e`. :math:`\phi_s` is constrained.

    .. warning::
        The selected :class:`.OptimisationAlgorithm` must support the
        constraints.

    """

    variables_names = ("phi_0_abs", "k_e")
    constraints_names = ("phi_s",)


@dataclass
class RelPhaseAmplitudeWithConstrainedSyncPhase(DesignSpaceFactory):
    r"""
    Optimise :math:`\phi_{0,\,\mathrm{rel}}`, :math:`k_e`. :math:`\phi_s` is constrained.

    .. warning::
        The selected :class:`.OptimisationAlgorithm` must support the
        constraints.

    """

    variables_names = ("phi_0_rel", "k_e")
    constraints_names = ("phi_s",)


# =============================================================================
# To create ``variables.csv`` and ``constraints.csv``
# =============================================================================
@dataclass
class Everything(DesignSpaceFactory):
    """This class creates all possible variables and constraints.

    This is not to be used in an optimisation problem, but rather to save in a
    ``CSV`` all the limits and initial values for every variable/constraint.

    """

    variables_names = (
        "k_e",
        "phi_s",
        "phi_0_abs",
        "phi_0_rel",
    )
    constraints_names = ("phi_s",)

    def run(self, *args, **kwargs) -> DesignSpace:
        """Launch normal run but with an info message."""
        logging.info(
            "Creating DesignSpace with all implemented variables and "
            f"constraints, i.e. {self.variables_names = } and "
            f"{self.constraints_names = }."
        )
        return super().create(*args, **kwargs)


# =============================================================================
# Deprecated aliases
# =============================================================================
@dataclass
class Unconstrained(AbsPhaseAmplitude):
    """Deprecated alias to :class:`AbsPhaseAmplitude`.

    .. deprecated:: 0.6.16
        Prefer :class:`AbsPhaseAmplitude`.

    """


@dataclass
class UnconstrainedRel(RelPhaseAmplitude):
    """Deprecated alias to :class:`RelPhaseAmplitude`.

    .. deprecated:: 0.6.16
        Prefer :class:`RelPhaseAmplitude`.

    """


@dataclass
class SyncPhaseAsVariable(SyncPhaseAmplitude):
    """Deprecated alias to :class:`SyncPhaseAmplitude`.

    .. deprecated:: 0.6.16
        Prefer :class:`SyncPhaseAmplitude`.

    """


@dataclass
class ConstrainedSyncPhase(AbsPhaseAmplitudeWithConstrainedSyncPhase):
    """Deprecated alias to :class:`AbsPhaseAmplitudeWithConstrainedSyncPhase`.

    .. deprecated:: 0.6.16
        Prefer :class:`AbsPhaseAmplitudeWithConstrainedSyncPhase`.

    """


DESIGN_SPACE_FACTORY_PRESETS = {
    "abs_phase_amplitude": AbsPhaseAmplitude,
    "rel_phase_amplitude": RelPhaseAmplitude,
    "sync_phase_amplitude": SyncPhaseAmplitude,
    "abs_phase_amplitude_with_constrained_sync_phase": AbsPhaseAmplitudeWithConstrainedSyncPhase,
    "rel_phase_amplitude_with_constrained_sync_phase": RelPhaseAmplitudeWithConstrainedSyncPhase,
    "everything": Everything,
    # Deprecated
    "unconstrained": AbsPhaseAmplitude,
    "unconstrained_rel": RelPhaseAmplitude,
    "constrained_sync_phase": AbsPhaseAmplitudeWithConstrainedSyncPhase,
    "sync_phase_as_variable": SyncPhaseAmplitude,
}  #:


def get_design_space_factory(
    design_space_preset: str, **design_space_kw: Path
) -> DesignSpaceFactory:
    """Select proper factory, instantiate it and return it.

    Parameters
    ----------
    design_space_preset :
        design_space_preset
    design_space_kw :
        design_space_kw

    """
    design_space_factory_class = DESIGN_SPACE_FACTORY_PRESETS[
        design_space_preset
    ]
    design_space_factory = design_space_factory_class(
        design_space_kw=design_space_kw,
    )
    return design_space_factory
