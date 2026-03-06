"""Define the class |F|.

Its purpose is to hold information on a failure and to fix it.

.. todo::
    not clear what happens here. separate __init__ in several functions

.. todo::
    store DesignSpace as attribute rather than Variable Constraint
    compute_constraints

"""

import datetime
import logging
import time
from collections.abc import Sequence

from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.core.elements.element import Element
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.list_of_elements.helper import equivalent_elt
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.failures.set_of_cavity_settings import SetOfCavitySettings
from lightwin.optimisation.algorithms.algorithm import (
    OptimisationAlgorithm,
    OptiSol,
)
from lightwin.optimisation.objective.factory import PackedElements
from lightwin.optimisation.objective.objective import (
    Objective,
    str_objectives_solved,
)
from lightwin.util.typing import ALLOWED_STATUS, REFERENCE_PHASE_POLICY_T


class Fault:
    """Handle and fix a single failure."""

    def __init__(
        self,
        reference_elts: ListOfElements,
        broken_elts: ListOfElements,
        failed_elements: Sequence[Element],
        compensating_elements: Sequence[Element],
        skip_optimization: bool = False,
    ) -> None:
        """Create the Fault object.

        Parameters
        ----------
        reference_elts :
            Holds nominal linac elements.
        broken_elts :
            Holds nominal linac elements.
        failed_elements :
            List of failed cavities.
        compensating_elements :
            Holds the compensating elements.
        skip_optimization :
            Used when the fixed |A| was unpikcled and therefore already holds
            the fixed settings.

        """
        self.broken_elts = broken_elts
        assert all([element.can_be_retuned for element in failed_elements])
        self.failed_elements = tuple(failed_elements)
        assert all(
            [element.can_be_retuned for element in compensating_elements]
        )
        self.compensating_elements = tuple(compensating_elements)

        self.reference_elements = tuple(
            equivalent_elt(reference_elts, element)
            for element in self.compensating_elements
        )

        #: This attribute is set at the start of the optimization process in
        #: order to save information on the objectives, variables, best
        #: solution, etc.
        self.optimisation_algorithm: OptimisationAlgorithm | None = None
        #: This attribute is set at the start of the optimization process in
        #: order to keep information on the compensation zone.
        self.subset_elts: ListOfElements
        self._skip_optimization = skip_optimization

    def fix(
        self, optimisation_algorithm: OptimisationAlgorithm | None
    ) -> None:
        """Fix the |F|. Set ``self.optimized_cavity_settings``.

        Also display information on the parametrization of the optimization
        problem, the solution that was found.

        Parameters
        ----------
        optimisation_algorithm :
            The optimization algorithm to be used, already initialized.
        simulation_output :
            The most recent simulation, that includes the compensation settings
            of all |F| upstream of ``self``.

        """
        logging.info(
            "Starting resolution of optimization problem defined by:\n"
            f"{optimisation_algorithm}"
        )
        start_time = time.monotonic()

        if self._skip_optimization:
            logging.info("Skipped!")
            return

        assert optimisation_algorithm is not None
        self.optimisation_algorithm = optimisation_algorithm
        _ = optimisation_algorithm.optimize()

        assert self.opti_sol is not None
        delta_t = datetime.timedelta(seconds=time.monotonic() - start_time)
        info = (
            f"Finished! Solving this problem took {delta_t}. Results are:",
            str_objectives_solved(optimisation_algorithm.objectives),
            f"Additional info: {'\n'.join(self.opti_sol['info'])}",
        )
        logging.info("\n".join(info))

    def postprocess_fix(
        self,
        fix_acc: Accelerator,
        beam_calculator: BeamCalculator,
        ref_simulation_output: SimulationOutput,
        reference_phase_policy: REFERENCE_PHASE_POLICY_T,
    ) -> SimulationOutput:
        """Run post-optimization propagation and update elements status.

        Parameters
        ----------
        fix_acc :
            Holds accelerator being fixed.
        beam_calculator :
            Object performing propagation.
        ref_simulation_output :
            Reference simulation, obtained with ``beam_calculator``.
        reference_phase_policy :
            Which phase should be kept when the beam phase changes.

        Returns
        -------
            Most recent simulation, that includes the compensation settings of
            upstream |F| as well as of this one.

        """
        if self._skip_optimization:
            return fix_acc.simulation_outputs[beam_calculator.id]
        fix_elts = fix_acc.elts

        simulation_output = beam_calculator.post_optimisation_run_with_this(
            accelerator_id=fix_acc.id,
            optimized_cavity_settings=self.optimized_cavity_settings,
            full_elts=fix_elts,
        )
        simulation_output.compute_indirect_quantities(
            fix_elts, ref_simulation_output=ref_simulation_output
        )

        self._post_compensation_status(reference_phase_policy, fix_elts)
        fix_acc.keep(
            simulation_output,
            exported_phase=reference_phase_policy,
            beam_calculator_id=beam_calculator.id,
            skip_pickle=True,
        )
        return simulation_output

    def pre_compensation_status(self) -> None:
        """Mark failed and compensating cavities.

        Skipped if the optimization was already performed.

        """
        if self._skip_optimization:
            return
        status_are_valid = True
        allowed = ("nominal", "rephased (in progress)", "rephased (ok)")
        for elt in self.failed_elements:
            assert isinstance(elt, FieldMap)
            if elt.status not in allowed:
                status_are_valid = False
            elt.update_status("failed")

        for elt in self.compensating_elements:
            assert isinstance(elt, FieldMap)
            if elt.status not in allowed:
                status_are_valid = False
            elt.update_status("compensate (in progress)")

        if status_are_valid:
            return

        logging.error(
            "At least one compensating or failed element is already "
            "compensating or faulty, probably in another Fault object. Updated"
            " its status anyway..."
        )

    def _post_compensation_status(
        self,
        reference_phase_policy: REFERENCE_PHASE_POLICY_T,
        fix_elts: ListOfElements,
    ) -> None:
        """Update cavities status after compensation.

        Skipped if the optimization was already performed.

        Compensating cavities of the current fault are marked as retuned,
        meaning they should not be modified further. Their status changes from
        ``"compensate (in progress)"`` to either ``"compensate (ok)"`` or
        ``"compensate (not ok)"`` depending on the compensation success.

        If the reference phase policy does not preserve absolute phases, all
        cavities following the last altered one are marked as rephased. Their
        status changes from ``"rephased (in progress)"`` to ``"rephased (ok)"``
        , stopping at the first element belonging to the next failure (*i.e.*,
        a compensating or failed cavity).

        Parameters
        ----------
        success :
            Wether the compensation was successful.
        reference_phase_policy :
            Phase reference policy applied during compensation.
        fix_elts :
            *All* accelerator elements.

        """
        if self._skip_optimization:
            return
        new_status = f"compensate ({'ok' if self.success else 'not ok'})"
        assert new_status in ALLOWED_STATUS
        for cav in self.compensating_elements:
            cav.update_status(new_status)

        if reference_phase_policy == "phi_0_abs":
            return

        altered_elts = self.compensating_elements + self.failed_elements
        idx_last_altered = max(fix_elts.index(elt) for elt in altered_elts)

        for elt in fix_elts[idx_last_altered:]:
            if not isinstance(elt, FieldMap):
                continue
            if elt.status == "rephased (in progress)":
                elt.update_status("rephased (ok)")
            if "compensate" in elt.status or "failed" in elt.status:
                break

    @property
    def packed_elements(self) -> PackedElements:
        """Return arguments for :class:`.ObjectiveFactory`."""
        return PackedElements(
            self.broken_elts, self.failed_elements, self.compensating_elements
        )

    @property
    def opti_sol(self) -> OptiSol | None:
        if self.optimisation_algorithm is None:
            return
        return self.optimisation_algorithm.opti_sol

    @property
    def info(self) -> dict:
        """Return the dictionary holding information on the solution.

        .. deprecated :: 0.8.2
            Prefer using the ``opti_sol`` attribute.

        """
        if self.opti_sol is None:
            return {}
        info = dict(self.opti_sol)
        info["objectives_values"] = self.opti_sol["objectives"]
        return info

    @property
    def optimized_cavity_settings(self) -> SetOfCavitySettings:
        """Get the settings found by the optimizer.

        If optimization was already performed (unpickled |A|) , we return the
        settings stored in the compensating cavities.

        """
        if self.opti_sol is not None:
            return self.opti_sol.get("cavity_settings")
        if not self._skip_optimization:
            raise ValueError(
                "'self.opti_sol' attribute should be set unless we are dealing"
                " with an already fixed Fault."
            )
        cavity_settings = {
            cav: cav.cavity_settings
            for cav in self.compensating_elements
            if isinstance(cav, FieldMap)
        }
        return SetOfCavitySettings(cavity_settings)

    @property
    def success(self) -> bool:
        """Get the success status."""
        if self.opti_sol is None:
            raise ValueError
        return self.opti_sol["success"]

    @property
    def objectives(self) -> list[Objective]:
        """Get objectives that were tried for this failure."""
        if self.optimisation_algorithm is None:
            return []
        return self.optimisation_algorithm.objectives
