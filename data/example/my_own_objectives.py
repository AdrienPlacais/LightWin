"""Showcase how you can define your own optimization objectives.

.. todo::
    Make this into a Jupyter Notebook and integrate to tutorials

.. todo::
    Find compensation objectives that will work.

"""

from typing import Any

from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.elements.element import Element
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.optimisation.objective.factory import (
    EnergyPhaseMismatch,
    ObjectiveFactory,
)
from lightwin.optimisation.objective.minimize_difference_with_ref import (
    MinimizeDifferenceWithRef,
)
from lightwin.optimisation.objective.objective import Objective
from lightwin.optimisation.objective.position import POSITION_TO_INDEX_T
from lightwin.optimisation.objective.quantity_is_between import (
    QuantityIsBetween,
)
from lightwin.util.dicts_output import markdown


class MyObjectiveFactory(ObjectiveFactory):
    r"""Showcase how to define your own objectives.

    .. note::
        Here, the objectives are defined in a "static" way, meaning that
        whatever the provided failures are, the objectives will always be the
        same:
        - Match :math:`\beta_{z,\,\delta}` at the exit of FM14, FM16, FM18,
          FM20.
        - Keep delta energy wrt reference within +/- 2:unit:`MeV` at the exit
          of FM14 adn FM20.

    .. note::
        These objectives will not allow compensation of example failure.

    """

    objective_position_preset: list[POSITION_TO_INDEX_T]
    compensation_zone_override_settings = {
        "full_lattices": False,
        "full_linac": False,
        "start_at_beginning_of_linac": False,
    }

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

        In this example, the :meth:`__init__` does not bring anything, so you
        can just skip its definition.

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
        super().__init__(
            reference_elts=reference_elts,
            reference_simulation_output=reference_simulation_output,
            broken_elts=broken_elts,
            failed_elements=failed_elements,
            compensating_elements=compensating_elements,
            design_space_kw=design_space_kw,
        )

    def get_objectives(self) -> list[Objective]:
        r"""Create the :class:`.Objective` instances.

        It is mandatory to define this method. Here, we will try to keep the
        kinetic energy within +/- 2:unit:`MeV` at the FM14 and FM20, and try to
        match the :math:`\beta_{z,\,\delta}` at FM14, FM16, FM18 and FM20.

        """
        objectives_beta = [
            self._get_beta(elt) for elt in self._objective_elements
        ]
        objectives_energy = [
            self._keep_w_kin_reasonable(elt)
            for elt in self._objective_elements
            if elt.name in ("FM14", "FM20")
        ]

        return objectives_beta + objectives_energy

    def _set_zone_to_recompute(
        self, **wtf: Any
    ) -> tuple[list[Element], list[Element]]:
        """Determine which (sub)list of elements should be recomputed.

        Also gives the elements where objectives are evaluated. You can
        override this method for your specific preset.
        By default, it will call the :func:`.zone_to_recompute` to dynamically
        determine a zone as small as possible, but encompassing all the
        compensating and failed elements.

        This method is called at the object creation. It requires the
        ``objective_position_preset`` attribute to be defined.

        """
        # We want the zone to recompute to span from the first compensating
        # element, to FM20, where we will match the last objective
        idx_start = self._compensating_elements[0].idx["elt_idx"]
        idx_end = self._broken_elts.take("FM20", id_nature="name").idx[
            "elt_idx"
        ]
        elts_of_compensation_zone = self._broken_elts[idx_start : idx_end + 1]

        # We just take the second cavtity of the cryos after failed cav
        objective_elements = self._broken_elts.take(
            ["FM14", "FM16", "FM18", "FM20"], id_nature="name"
        )

        # With user-defined objective, it up to you to check that every failed,
        # compensating and objective elements are in the zone to recompute
        return elts_of_compensation_zone, objective_elements

    def _get_beta(self, elt: Element) -> Objective:
        """Create an objective to match nominal envelope."""
        objective = MinimizeDifferenceWithRef(
            name=markdown["beta_zdelta"],
            weight=1.0,
            get_key="beta_zdelta",
            get_kwargs={"elt": elt, "pos": "out", "to_numpy": False},
            reference=self._reference_simulation_output,
            descriptor="""Minimize diff. of envelope between ref and fix at the
            exit of provided element.
            """,
        )
        return objective

    def _keep_w_kin_reasonable(self, elt: Element) -> Objective:
        """Keep energy within +/- 2:unit:`MeV` wrt nominal tuning."""
        # Define arguments to ``get`` the kinetic energy at the exit of
        # provided element
        get_key = "w_kin"
        get_kwargs = {"elt": elt, "pos": "out", "to_numpy": False}

        # First, we get the nominal energy at ``elt``
        ref = self._reference_simulation_output.get(get_key, **get_kwargs)

        # Now we create the objective
        objective = QuantityIsBetween(
            name=markdown["w_kin"],
            weight=1.0,
            get_key=get_key,
            get_kwargs=get_kwargs,
            limits=(ref - 2.0, ref + 2.0),
            descriptor="Energy stays within +/- 5MeV wrt nominal tuning.",
        )
        # Of course, you can also define your own :class:`.Objective`.
        return objective


class EnergyPhaseMismatchMoreElements(EnergyPhaseMismatch):
    """Same objectives, but more elements in calculation."""

    def __init__(self, *args, **kwargs) -> None:
        """Override some defaults."""
        super().__init__(*args, **kwargs)
        last_element_to_compute = "FM18"
        self.elts_of_compensation_zone = []
        for elt in self._broken_elts:
            self.elts_of_compensation_zone.append(elt)
            if elt.name == last_element_to_compute:
                return
