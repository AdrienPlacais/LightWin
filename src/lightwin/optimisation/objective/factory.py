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
from dataclasses import dataclass
from typing import Any, Literal

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
from lightwin.optimisation.objective.objective import (
    MinimizeDifferenceWithRef,
    MinimizeMismatch,
    Objective,
    QuantityIsBetween,
)
from lightwin.optimisation.objective.position import (
    POSITION_TO_INDEX_T,
    zone_to_recompute,
)
from lightwin.util.dicts_output import markdown


class ObjectiveFactory(ABC):
    """A base class to create all the :class:`.Objective` of a :class:`.Fault`.

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

    #: List of positions telling where objectives should be evaluated.
    objective_position_preset: list[POSITION_TO_INDEX_T]
    compensation_zone_override_settings = {
        "full_lattices": False,
        "full_linac": False,
        "start_at_beginning_of_linac": False,
    }  #:

    def __init__(
        self,
        reference_simulation_output: SimulationOutput,
        broken_elts: ListOfElements,
        failed_elements: Collection[Element],
        compensating_elements: Collection[Element],
        design_space_kw: dict[str, Any],
    ) -> None:
        """Create the object.

        Parameters
        ----------
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
        #: The reference simulation of the reference linac.
        self._reference_simulation_output = reference_simulation_output
        #: All the reference elements.
        self._reference_elts = reference_simulation_output.elts

        self._broken_elts = broken_elts
        #: Broken elements.
        self._failed_elements = tuple(failed_elements)
        self._compensating_elements = tuple(compensating_elements)

        self._design_space_kw = design_space_kw

        assert all([elt.can_be_retuned for elt in self._compensating_elements])
        #: List of elements were an objective is evaluated
        self._objective_elements: list[Element]
        self.elts_of_compensation_zone, self._objective_elements = (
            self._set_zone_to_recompute()
        )
        self.objectives = self.get_objectives()

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
            element.idx["elt_idx"] for element in self._failed_elements
        ]
        comp_idx = [
            element.idx["elt_idx"] for element in self._compensating_elements
        ]

        elts_of_compensation_zone, objective_elements = zone_to_recompute(
            self._broken_elts,
            self.objective_position_preset,
            fault_idx,
            comp_idx,
            **self.compensation_zone_override_settings,
        )
        return elts_of_compensation_zone, objective_elements

    def compute_residuals(
        self, simulation_output: SimulationOutput
    ) -> NDArray[np.float64]:
        """Compute residuals on objectives for a simulation."""
        residuals = [
            objective.evaluate(simulation_output)
            for objective in self.objectives
        ]
        return np.array(residuals)


class CorrectorAtExit(ObjectiveFactory):
    """Propagate beam up to final cavities, where an energy boost is given.

    The idea behind this strategy is the following:

    - Use ``n_compensating`` cavities around the failure to shape the beam and
      propagate it without losses.
    - Rephase downstream cavities to keep the beam as intact as possible.
    - Give an ultimate energy boost to the beam with the last ``n_correctors``
      cavities.

    This method is very similar to the one used at SNS :cite:`Shishlo2022`.
    In this paper however, there are no compensating cavities around the
    failure.

    See Also
    --------
    :func:`.strategy.corrector_at_exit`

    """

    objective_position_preset = ["end of last altered lattice"]

    def get_objectives(self) -> list[Objective]:
        """Give adapted objectives.

        We start by looking at the :attr:`.CorrectorAtExit._failed_elements`
        list:

        - If it has elements, we are around a failure and we will try to keep
          a kinetic energy not too far from the nominal energy. More
          importantly, we try to minimize the mismatch factor at the exit of
          the compensation zone.
        - If it is empty, it means that there is no nearby failed cavity. We
          are at the exit of the linac and will try to retrieve nominal energy
          at the end of the linac.

        """
        if len(self._failed_elements) > 0:
            last_element_of_zone = self._objective_elements[-1]
            return [
                self._preaccelerate(elt=last_element_of_zone),
                self._preshape(elt=last_element_of_zone),
            ]

        last_element_of_linac = self._compensating_elements[-1]
        return [self._retrieve_energy(last_element_of_linac)]

    def _preaccelerate(self, elt: Element) -> Objective:
        """Get reasonable energy at exit of compensation zone."""
        get_key = "w_kin"
        get_kwargs = {"elt": elt, "pos": "out", "to_numpy": False}
        ref = self._reference_simulation_output.get(get_key, **get_kwargs)
        objective = QuantityIsBetween.relative_to_reference(
            name=markdown["w_kin"],
            weight=1.0,
            get_key=get_key,
            get_kwargs=get_kwargs,
            relative_limits=(90.0, 101.0),
            reference_value=ref,
            descriptor="Energy stays within (-10%, +1%) wrt nominal tuning.",
        )
        return objective

    def _preshape(self, elt: Element) -> Objective:
        """Minimize mismatch factor at exit of compensation zone."""
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
            reference=self._reference_simulation_output,
            descriptor="""Minimize mismatch factor in the [z-delta] plane at
            exit of compensation zone.""",
        )
        return objective

    def _retrieve_energy(self, elt: Element) -> Objective:
        """Retrieve energy at the end of the linac."""
        objective = MinimizeDifferenceWithRef(
            name=markdown["w_kin"],
            weight=1.0,
            get_key="w_kin",
            get_kwargs={"elt": elt, "pos": "out", "to_numpy": False},
            reference=self._reference_simulation_output,
            descriptor="Retrieve nominal energy at the exit of the linac.",
        )
        return objective


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
        last_element = self._objective_elements[0]
        objectives = [
            self._get_w_kin(elt=last_element),
            self._get_mismatch(elt=last_element),
        ]
        return objectives

    def _get_w_kin(self, elt: Element) -> Objective:
        """Return object to match energy."""
        objective = MinimizeDifferenceWithRef(
            name=markdown["w_kin"],
            weight=1.0,
            get_key="w_kin",
            get_kwargs={"elt": elt, "pos": "out", "to_numpy": False},
            reference=self._reference_simulation_output,
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
            reference=self._reference_simulation_output,
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
        last_element = self._objective_elements[0]
        objectives = [
            self._get_w_kin(elt=last_element),
            self._get_phi_abs(elt=last_element),
            self._get_mismatch(elt=last_element),
        ]
        return objectives

    def _get_w_kin(self, elt: Element) -> Objective:
        """Return object to match energy."""
        objective = MinimizeDifferenceWithRef(
            name=markdown["w_kin"],
            weight=1.0,
            get_key="w_kin",
            get_kwargs={"elt": elt, "pos": "out", "to_numpy": False},
            reference=self._reference_simulation_output,
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
            reference=self._reference_simulation_output,
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
            reference=self._reference_simulation_output,
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
        last_element = self._objective_elements[0]
        objectives = [
            self._get_w_kin(elt=last_element),
            self._get_phi_abs(elt=last_element),
            self._get_mismatch(elt=last_element),
        ]

        working_and_tunable_elements_in_compensation_zone = list(
            filter(
                lambda element: (
                    element.can_be_retuned
                    and element not in self._failed_elements
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

        return objectives

    def _get_w_kin(self, elt: Element) -> Objective:
        """Return object to match energy."""
        objective = MinimizeDifferenceWithRef(
            name=markdown["w_kin"],
            weight=1.0,
            get_key="w_kin",
            get_kwargs={"elt": elt, "pos": "out", "to_numpy": False},
            reference=self._reference_simulation_output,
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
            reference=self._reference_simulation_output,
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
            reference=self._reference_simulation_output,
            descriptor="""Minimize mismatch factor in the [z-delta] plane.""",
        )
        return objective

    def _get_phi_s(self, cavity: FieldMap) -> Objective:
        """
        Objective to have sync phase within bounds.

        .. todo::
            Allow ``from_file``.

        """
        reference_cavity = equivalent_elt(self._reference_elts, cavity)

        if self._design_space_kw["from_file"]:
            raise OSError(
                "For now, synchronous phase cannot be taken from the variables"
                " or constraints.csv files when used as objectives."
            )
        limits = phi_s_limits(reference_cavity, **self._design_space_kw)

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
        last_element = self._objective_elements[-1]
        one_lattice_before = self._objective_elements[-2]
        objectives = [
            self._get_w_kin(elt=one_lattice_before),
            self._get_mismatch(elt=one_lattice_before),
            self._get_mismatch(elt=last_element),
        ]
        return objectives

    def _get_w_kin(self, elt: Element) -> Objective:
        """Return object to match energy."""
        objective = MinimizeDifferenceWithRef(
            name=markdown["w_kin"],
            weight=1.0,
            get_key="w_kin",
            get_kwargs={"elt": elt, "pos": "out", "to_numpy": False},
            reference=self._reference_simulation_output,
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
            reference=self._reference_simulation_output,
            descriptor="Minimize mismatch factor in the [z-delta] plane.",
        )
        return objective


class Spiral2(CorrectorAtExit):
    """Testing best SPIRAL2 compensation method.

    Tests on CMA06 compensation. Currently, CorrectorAtExit leads to the best
    results. First attempts to set CMA07 as buncher were not convincing.

    """


#: Maps the ``objective_preset`` key in ``TOML`` ``wtf`` subsection with actual
#: objects in LightWin
OBJECTIVE_PRESETS = {
    "CorrectorAtExit": CorrectorAtExit,
    "EnergyMismatch": EnergyMismatch,
    "EnergyPhaseMismatch": EnergyPhaseMismatch,
    "EnergySeveralMismatches": EnergySeveralMismatches,
    "EnergySyncPhaseMismatch": EnergySyncPhaseMismatch,
    "experimental": CorrectorAtExit,
    "rephased_ADS": EnergyMismatch,
    "simple_ADS": EnergyPhaseMismatch,
    "sync_phase_as_objective_ADS": EnergySyncPhaseMismatch,
}
OBJECTIVE_PRESETS_T = Literal[
    "CorrectorAtExit",
    "EnergyMismatch",
    "EnergyPhaseMismatch",
    "EnergySeveralMismatches",
    "EnergySyncPhaseMismatch",
    "experimental",
    "rephased_ADS",
    "simple_ADS",
]


@dataclass(frozen=True)
class PackedElements:
    """Pack :class:`.Element` info to instantiate :class:`.ObjectiveFactory`.

    See Also
    --------
    .Fault.packed_elements

    """

    #: Contains the full linac being fixed.
    broken_elts: ListOfElements
    #: The elements of ``broken_elts`` that failed.
    failed_elements: tuple[Element, ...]
    #: Elements of ``broken_elts`` used for compensation.
    compensating_elements: tuple[Element, ...]


class ObjectiveMetaFactory:
    """An object creating :class:`.ObjectiveFactory` for every :class:`.Fault`."""

    def __init__(self, reference_simulation_output: SimulationOutput) -> None:
        self._reference_simulation_output = reference_simulation_output

    def create(
        self,
        objective_preset: OBJECTIVE_PRESETS_T,
        design_space_kw: dict[str, Any],
        packed_elements: PackedElements,
        objective_factory_class: type[ObjectiveFactory] | None = None,
    ) -> ObjectiveFactory:
        """Create object that will create all the :class:`.Objective`."""
        objective_factory_class = self._factory_class(
            objective_preset, objective_factory_class
        )

        objective_factory = objective_factory_class(
            self._reference_simulation_output,
            packed_elements.broken_elts,
            packed_elements.failed_elements,
            packed_elements.compensating_elements,
            design_space_kw=design_space_kw,
        )
        return objective_factory

    def _factory_class(
        self,
        objective_preset: OBJECTIVE_PRESETS_T,
        objective_factory_class: type[ObjectiveFactory] | None = None,
    ) -> type[ObjectiveFactory]:
        """Determine type of :class:`.ObjectiveFactory` to use.

        This method does not instantiate the :class:`.ObjectiveFactory`.

        """
        if objective_factory_class:
            logging.info(
                "A user-defined ObjectiveFactory was provided, so the key "
                f"{objective_preset = } will be disregarded.\n"
                f"{objective_factory_class = }"
            )
            return objective_factory_class
        return OBJECTIVE_PRESETS[objective_preset]
