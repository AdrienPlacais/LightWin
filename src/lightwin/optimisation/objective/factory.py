"""Define a factory to create :class:`.Objective` objects.

When you implement a new objective preset, also add it to the list of
implemented presets in :data:`.OBJECTIVE_PRESETS` and
:mod:`.optimisation.wtf_specs`.

.. todo::
    decorator to auto output the variables and constraints?

"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Collection
from functools import partial
from pathlib import Path
from typing import Any, Callable

import numpy as np
from numpy.typing import NDArray

from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.elements.element import Element
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.list_of_elements.helper import equivalent_elt
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.experimental.test import assert_are_field_maps
from lightwin.optimisation.design_space.helper import phi_s_limits
from lightwin.optimisation.objective.minimize_difference_with_ref import (
    MinimizeDifferenceWithRef,
)
from lightwin.optimisation.objective.minimize_mismatch import MinimizeMismatch
from lightwin.optimisation.objective.objective import Objective
from lightwin.optimisation.objective.position import (
    POSITION_TO_INDEX_T,
    zone_to_recompute,
)
from lightwin.optimisation.objective.quantity_is_between import (
    QuantityIsBetween,
)
from lightwin.util.dicts_output import markdown


class ObjectiveFactory(ABC):
    """A base class to create :class:`.Objective`.

    It is intended to be sub-classed to make presets. Look at
    :class:`EnergyPhaseMismatch` or :class:`EnergySyncPhaseMismatch` for
    examples.

    Parameters
    ----------
    objective_position_preset :
        List of keys to dynamically select where the objectives should be
        matched.
    compensation_zone_override_settings :
        Keyword arguments that are passed to :func:`.zone_to_recompute`. By
        default, the list of elements in which we propagate the beam is as
        small as possible, but you may want to override this behavior.

    """

    objective_position_preset: list[POSITION_TO_INDEX_T]  #:
    compensation_zone_override_settings = {
        "full_lattices": False,
        "full_linac": False,
        "start_at_beginning_of_linac": False,
    }  #:

    def __init__(
        self,
        reference_elts: ListOfElements,
        reference_simulation_output: SimulationOutput,
        broken_elts: ListOfElements,
        failed_elements: list[Element],
        compensating_elements: list[Element],
        design_space_kw: dict[str, Any],
    ) -> None:
        """Create the object.

        Parameters
        ----------
        reference_elts :
            All the reference elements.
        reference_simulation_output :
            The reference simulation of the reference linac.
        broken_elts :
            List containing all the elements of the broken linac.
        failed_elements :
            Cavities that failed.
        compensating_elements :
            Cavities that will be used for the compensation.
        design_space_kw :
            Holds information on variables/constraints limits/initial values.
            Used to compute the limits that ``phi_s`` must respect when the
            synchronous phase is defined as an objective.

        """
        self.reference_elts = reference_elts
        self.reference_simulation_output = reference_simulation_output

        self.broken_elts = broken_elts
        self.failed_elements = failed_elements
        self.compensating_elements = compensating_elements

        self.design_space_kw = design_space_kw

        assert all([elt.can_be_retuned for elt in self.compensating_elements])
        self.elts_of_compensation_zone, self.objective_elements = (
            self._set_zone_to_recompute()
        )

    @abstractmethod
    def get_objectives(self) -> list[Objective]:
        """Create the :class:`.Objective` instances."""

    def _set_zone_to_recompute(
        self, **wtf: Any
    ) -> tuple[list[Element], list[Element]]:
        """Determine which (sub)list of elements should be recomputed.

        Also determine the elements where objectives are evaluated. You can
        override this method for your specific preset.

        """
        fault_idx = [
            element.idx["elt_idx"] for element in self.failed_elements
        ]
        comp_idx = [
            element.idx["elt_idx"] for element in self.compensating_elements
        ]

        elts_of_compensation_zone, objective_elements = zone_to_recompute(
            self.broken_elts,
            self.objective_position_preset,
            fault_idx,
            comp_idx,
            **self.compensation_zone_override_settings,
        )
        return elts_of_compensation_zone, objective_elements

    @staticmethod
    def _output_objectives(objectives: list[Objective]) -> None:
        """Print information on the objectives that were created."""
        info = [str(objective) for objective in objectives]
        info.insert(0, "Created objectives:")
        info.insert(1, "=" * 100)
        info.insert(2, Objective.str_header())
        info.insert(3, "-" * 100)
        info.append("=" * 100)
        logging.info("\n".join(info))


class EnergyMismatch(ObjectiveFactory):
    """A set of two objectives: energy and mismatch.

    We try to match the kinetic energy and the mismatch factor at the end of
    the last altered lattice (the last lattice with a compensating or broken
    cavity).

    This set of objectives is adapted when you do not need to retrieve the
    absolute beam phase at the exit of the compensation zone, ie when rephasing
    all downstream cavities is not an issue.

    """

    objective_position_preset = ["end of last altered lattice"]

    def get_objectives(self) -> list[Objective]:
        """Give objects to match kinetic energy, phase and mismatch factor."""
        last_element = self.objective_elements[0]
        objectives = [
            self._get_w_kin(elt=last_element),
            self._get_mismatch(elt=last_element),
        ]
        self._output_objectives(objectives)
        return objectives

    def _get_w_kin(self, elt: Element) -> Objective:
        """Return object to match energy."""
        objective = MinimizeDifferenceWithRef(
            name=markdown["w_kin"],
            weight=1.0,
            get_key="w_kin",
            get_kwargs={"elt": elt, "pos": "out", "to_numpy": False},
            reference=self.reference_simulation_output,
            descriptor="""Minimize diff. of w_kin between ref and fix at the
            end of the compensation zone.
            """,
        )
        return objective

    def _get_mismatch(self, elt: Element) -> Objective:
        """Return object to keep mismatch as low as possible."""
        objective = MinimizeMismatch(
            name=r"$M_{z\delta}$",
            weight=1.0,
            get_key="twiss",
            get_kwargs={
                "elt": elt,
                "pos": "out",
                "to_numpy": True,
                "phase_space_name": "zdelta",
            },
            reference=self.reference_simulation_output,
            descriptor="""Minimize mismatch factor in the [z-delta] plane.""",
        )
        return objective


class EnergyPhaseMismatch(ObjectiveFactory):
    """A set of three objectives: energy, absolute phase, mismatch.

    We try to match the kinetic energy, the absolute phase and the mismatch
    factor at the end of the last altered lattice (the last lattice with a
    compensating or broken cavity).
    With this preset, it is recommended to set constraints on the synchrous
    phase to help the optimisation algorithm to converge.

    This set of objectives is robust and rapid for ADS.

    """

    objective_position_preset = ["end of last altered lattice"]

    def get_objectives(self) -> list[Objective]:
        """Give objects to match kinetic energy, phase and mismatch factor."""
        last_element = self.objective_elements[0]
        objectives = [
            self._get_w_kin(elt=last_element),
            self._get_phi_abs(elt=last_element),
            self._get_mismatch(elt=last_element),
        ]
        self._output_objectives(objectives)
        return objectives

    def _get_w_kin(self, elt: Element) -> Objective:
        """Return object to match energy."""
        objective = MinimizeDifferenceWithRef(
            name=markdown["w_kin"],
            weight=1.0,
            get_key="w_kin",
            get_kwargs={"elt": elt, "pos": "out", "to_numpy": False},
            reference=self.reference_simulation_output,
            descriptor="""Minimize diff. of w_kin between ref and fix at the
            end of the compensation zone.
            """,
        )
        return objective

    def _get_phi_abs(self, elt: Element) -> Objective:
        """Return object to match phase."""
        objective = MinimizeDifferenceWithRef(
            name=markdown["phi_abs"].replace("deg", "rad"),
            weight=1.0,
            get_key="phi_abs",
            get_kwargs={
                "elt": elt,
                "pos": "out",
                "to_numpy": False,
                "to_deg": False,
            },
            reference=self.reference_simulation_output,
            descriptor="""Minimize diff. of phi_abs between ref and fix at the
            end of the compensation zone.
            """,
        )
        return objective

    def _get_mismatch(self, elt: Element) -> Objective:
        """Return object to keep mismatch as low as possible."""
        objective = MinimizeMismatch(
            name=r"$M_{z\delta}$",
            weight=1.0,
            get_key="twiss",
            get_kwargs={
                "elt": elt,
                "pos": "out",
                "to_numpy": True,
                "phase_space_name": "zdelta",
            },
            reference=self.reference_simulation_output,
            descriptor="""Minimize mismatch factor in the [z-delta] plane.""",
        )
        return objective


class EnergySyncPhaseMismatch(ObjectiveFactory):
    """Match the synchronous phase, the energy and the mismatch factor.

    It is very similar to :class:`EnergyPhaseMismatch`, except that synchronous
    phases are declared as objectives.
    Objective will be 0 when synchronous phase is within the imposed limits.

    .. note::
        Do not set synchronous phases as constraints when using this preset.

    This set of objectives is slower than :class:`.EnergyPhaseMismatch`.
    However, it can help keeping the acceptance as high as possible.

    """

    objective_position_preset = ["end of last altered lattice"]

    def get_objectives(self) -> list[Objective]:
        """Give objects to match kinetic energy, phase and mismatch factor."""
        last_element = self.objective_elements[0]
        objectives = [
            self._get_w_kin(elt=last_element),
            self._get_phi_abs(elt=last_element),
            self._get_mismatch(elt=last_element),
        ]

        working_and_tunable_elements_in_compensation_zone = list(
            filter(
                lambda element: (
                    element.can_be_retuned
                    and element not in self.failed_elements
                ),
                self.elts_of_compensation_zone,
            )
        )

        assert_are_field_maps(
            working_and_tunable_elements_in_compensation_zone,
            detail="accessing phi_s property of a non field map",
        )

        objectives += [
            self._get_phi_s(element)
            for element in working_and_tunable_elements_in_compensation_zone
            if isinstance(element, FieldMap)
        ]

        self._output_objectives(objectives)
        return objectives

    def _get_w_kin(self, elt: Element) -> Objective:
        """Return object to match energy."""
        objective = MinimizeDifferenceWithRef(
            name=markdown["w_kin"],
            weight=1.0,
            get_key="w_kin",
            get_kwargs={"elt": elt, "pos": "out", "to_numpy": False},
            reference=self.reference_simulation_output,
            descriptor="""Minimize diff. of w_kin between ref and fix at the
            end of the compensation zone.
            """,
        )
        return objective

    def _get_phi_abs(self, elt: Element) -> Objective:
        """Return object to match phase."""
        objective = MinimizeDifferenceWithRef(
            name=markdown["phi_abs"].replace("deg", "rad"),
            weight=1.0,
            get_key="phi_abs",
            get_kwargs={
                "elt": elt,
                "pos": "out",
                "to_numpy": False,
                "to_deg": False,
            },
            reference=self.reference_simulation_output,
            descriptor="""Minimize diff. of phi_abs between ref and fix at the
            end of the compensation zone.
            """,
        )
        return objective

    def _get_mismatch(self, elt: Element) -> Objective:
        """Return object to keep mismatch as low as possible."""
        objective = MinimizeMismatch(
            name=r"$M_{z\delta}$",
            weight=1.0,
            get_key="twiss",
            get_kwargs={
                "elt": elt,
                "pos": "out",
                "to_numpy": True,
                "phase_space_name": "zdelta",
            },
            reference=self.reference_simulation_output,
            descriptor="""Minimize mismatch factor in the [z-delta] plane.""",
        )
        return objective

    def _get_phi_s(self, cavity: FieldMap) -> Objective:
        """
        Objective to have sync phase within bounds.

        .. todo::
            Allow ``from_file``.

        """
        reference_cavity = equivalent_elt(self.reference_elts, cavity)

        if self.design_space_kw["from_file"]:
            raise OSError(
                "For now, synchronous phase cannot be taken from the variables"
                " or constraints.csv files when used as objectives."
            )
        limits = phi_s_limits(reference_cavity, **self.design_space_kw)

        objective = QuantityIsBetween(
            name=markdown["phi_s"].replace("deg", "rad"),
            weight=50.0,
            get_key="phi_s",
            get_kwargs={
                "elt": cavity,
                "pos": "out",
                "to_numpy": False,
                "to_deg": False,
            },
            limits=limits,
            descriptor="""Synchronous phase should be between limits.""",
        )
        return objective


class EnergySeveralMismatches(ObjectiveFactory):
    """Match energy and mismatch (the latter on several periods).

    Experimental.

    """

    objective_position_preset = [
        "end of last altered lattice",
        "one lattice after last altered lattice",
    ]

    def get_objectives(self) -> list[Objective]:
        """Give objects to match kinetic energy and mismatch factor."""
        last_element = self.objective_elements[-1]
        one_lattice_before = self.objective_elements[-2]
        objectives = [
            self._get_w_kin(elt=one_lattice_before),
            self._get_mismatch(elt=one_lattice_before),
            self._get_mismatch(elt=last_element),
        ]
        self._output_objectives(objectives)
        return objectives

    def _get_w_kin(self, elt: Element) -> Objective:
        """Return object to match energy."""
        objective = MinimizeDifferenceWithRef(
            name=markdown["w_kin"],
            weight=1.0,
            get_key="w_kin",
            get_kwargs={"elt": elt, "pos": "out", "to_numpy": False},
            reference=self.reference_simulation_output,
            descriptor="""Minimize diff. of w_kin between ref and fix at the
            end of the compensation zone.
            """,
        )
        return objective

    def _get_mismatch(self, elt: Element) -> Objective:
        """Return object to keep mismatch as low as possible."""
        objective = MinimizeMismatch(
            name=r"$M_{z\delta}$",
            weight=1.0,
            get_key="twiss",
            get_kwargs={
                "elt": elt,
                "pos": "out",
                "to_numpy": True,
                "phase_space_name": "zdelta",
            },
            reference=self.reference_simulation_output,
            descriptor="Minimize mismatch factor in the [z-delta] plane.",
        )
        return objective


class Spiral2(ObjectiveFactory):
    """Try something."""

    objective_position_preset = ["end of every altered lattice"]
    compensation_zone_override_settings = {
        "full_lattices": True,
        "full_linac": False,
        "start_at_beginning_of_linac": False,
    }

    def get_objectives(self) -> list[Objective]:
        """Return twiss and energy at end of lattices after failure."""
        objectives = []
        for elt in self.objective_elements:
            objectives += [
                self._get_twiss_alpha(elt),
                self._get_twiss_beta(elt),
                self._get_w_kin(elt),
            ]
        self._output_objectives(objectives)
        return objectives

    def _get_twiss_alpha(self, elt: Element) -> Objective:
        """Return object to match spread."""
        objective = MinimizeDifferenceWithRef(
            name=markdown["alpha_zdelta"],
            weight=1.0,
            get_key="alpha_zdelta",
            get_kwargs={"elt": elt, "pos": "out", "to_numpy": False},
            reference=self.reference_simulation_output,
            descriptor="""Minimize diff. of alpha between ref and fix at the
            end of the lattice.
            """,
        )
        return objective

    def _get_twiss_beta(self, elt: Element) -> Objective:
        """Return object to match envelope."""
        objective = MinimizeDifferenceWithRef(
            name=markdown["beta_zdelta"],
            weight=1.0,
            get_key="beta_zdelta",
            get_kwargs={"elt": elt, "pos": "out", "to_numpy": False},
            reference=self.reference_simulation_output,
            descriptor="""Minimize diff. of envelope between ref and fix at the
            end of the lattice.
            """,
        )
        return objective

    def _get_w_kin(self, elt: Element) -> Objective:
        """Return object to keep energy reasonable."""
        get_key = "w_kin"
        get_kwargs = {"elt": elt, "pos": "out", "to_numpy": False}
        ref = self.reference_simulation_output.get(get_key, **get_kwargs)
        objective = QuantityIsBetween(
            name=markdown["w_kin"],
            weight=1.0,
            get_key=get_key,
            get_kwargs=get_kwargs,
            limits=(ref - 5.0, ref + 5.0),
            descriptor="Energy stays within +/- 5MeV wrt nominal tuning.",
        )
        return objective


# =============================================================================
# Interface with LightWin
# =============================================================================
#: Maps the ``objective_preset`` key in ``TOML`` ``wtf`` subsection with actual
#: objects in LightWin
OBJECTIVE_PRESETS = {
    "EnergyMismatch": EnergyMismatch,
    "EnergyPhaseMismatch": EnergyPhaseMismatch,
    "EnergySeveralMismatches": EnergySeveralMismatches,
    "EnergySyncPhaseMismatch": EnergySyncPhaseMismatch,
    "experimental": Spiral2,
    "rephased_ADS": EnergyMismatch,
    "simple_ADS": EnergyPhaseMismatch,
    "sync_phase_as_objective_ADS": EnergySyncPhaseMismatch,
}


def get_objectives_and_residuals_function(
    objective_preset: str,
    reference_elts: ListOfElements,
    reference_simulation_output: SimulationOutput,
    broken_elts: ListOfElements,
    failed_elements: list[Element],
    compensating_elements: list[Element],
    design_space_kw: dict[str, float | bool | str | Path],
    objective_factory_class: type[ObjectiveFactory] | None = None,
) -> tuple[
    list[Element], list[Objective], Callable[[SimulationOutput], NDArray]
]:
    """Instantiate objective factory and create objectives.

    Parameters
    ----------
    reference_elts :
        All the reference elements.
    reference_simulation_output :
        The reference simulation of the reference linac.
    broken_elts :
        The elements of the broken linac.
    failed_elements :
        Elements that failed.
    compensating_elements :
        Elements that will be used for the compensation.
    design_space_kw :
        Used when we need to determine the limits for ``phi_s``. Those limits
        are defined in the ``INI`` configuration file.
    objective_factory_class :
        If provided, will override the ``objective_preset``. Used to let user
        define it's own :class:`.ObjectiveFactory` without altering the source
        code.

    Returns
    -------
    elts_of_compensation_zone : list[Element]
        Portion of the linac that will be recomputed during the optimisation
        process.
    objectives : list[Objective]
        Objectives that the optimisation algorithm will try to match.
    compute_residuals : Callable[[SimulationOutput], NDArray]
        Function that converts a :class:`.SimulationOutput` to a plain numpy
        array of residuals.

    """
    assert isinstance(objective_preset, str)

    if objective_factory_class is None:
        objective_factory_class = OBJECTIVE_PRESETS[objective_preset]
    else:
        logging.info(
            "A user-defined ObjectiveFactory was provided, so the key "
            f"{objective_preset = } will be disregarded.\n"
            f"{objective_factory_class = }"
        )
    assert objective_factory_class is not None

    objective_factory = objective_factory_class(
        reference_elts=reference_elts,
        reference_simulation_output=reference_simulation_output,
        broken_elts=broken_elts,
        failed_elements=failed_elements,
        compensating_elements=compensating_elements,
        design_space_kw=design_space_kw,
    )

    elts_of_compensation_zone = objective_factory.elts_of_compensation_zone
    objectives = objective_factory.get_objectives()
    compute_residuals = partial(_compute_residuals, objectives=objectives)
    return elts_of_compensation_zone, objectives, compute_residuals


def _compute_residuals(
    simulation_output: SimulationOutput, objectives: Collection[Objective]
) -> NDArray:
    """Compute residuals on given `Objectives` for given `SimulationOutput`."""
    residuals = [
        objective.evaluate(simulation_output) for objective in objectives
    ]
    return np.array(residuals)
