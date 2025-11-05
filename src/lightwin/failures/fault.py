"""Define the class :class:`Fault`.

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
from pathlib import Path
from typing import Any, Self

from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.core.elements.element import Element
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.list_of_elements.helper import equivalent_elt
from lightwin.core.list_of_elements.list_of_elements import (
    ListOfElements,
    sumup_cavities,
)
from lightwin.failures.set_of_cavity_settings import SetOfCavitySettings
from lightwin.optimisation.algorithms.algorithm import (
    OptimisationAlgorithm,
    OptiSol,
)
from lightwin.optimisation.objective.factory import (
    OBJECTIVE_PRESETS,
)
from lightwin.optimisation.objective.objective import str_objectives_solved
from lightwin.util.helper import pd_output
from lightwin.util.pickling import MyPickler
from lightwin.util.typing import ALLOWED_STATUS, REFERENCE_PHASE_POLICY_T


class Fault:
    """Handle and fix a single failure.

    Parameters
    ----------
    failed_elements :
        Holds the failed elements.
    compensating_elements :
        Holds the compensating elements.
    elts :
        Holds the portion of the linac that will be computed again and again in
        the optimization process. It is as short as possible, but must contain
        all ``failed_elements``, ``compensating_elements`` and
        ``elt_eval_objectives``.
    variables :
        Holds information on the optimization variables.
    constraints :
        Holds infomation on the optimization constraints.

    Methods
    -------
    compute_constraints :
        Compute the constraint violation for a given `SimulationOutput`.
    compute_residuals :
        A function that takes in a `SimulationOutput` and returns the residuals
        of every objective w.r.t the reference one.

    """

    def __init__(
        self,
        reference_elts: ListOfElements,
        wtf: dict[str, Any],
        broken_elts: ListOfElements,
        failed_elements: list[Element],
        compensating_elements: list[Element],
    ) -> None:
        """Create the Fault object.

        Parameters
        ----------
        wtf :
            What To Fit dictionary. Holds information on the fixing method.
        broken_elts :
            Contains all the elements of the broken linac.
        failed_elements :
            List of failed cavities.
        failed_elements :
            Holds the failed elements.
        compensating_elements :
            Holds the compensating elements.

        """
        assert all([element.can_be_retuned for element in failed_elements])
        self.broken_elts = broken_elts
        self.failed_elements = failed_elements
        assert all(
            [element.can_be_retuned for element in compensating_elements]
        )
        self.compensating_elements = compensating_elements

        self.reference_elements = [
            equivalent_elt(reference_elts, element)
            for element in self.compensating_elements
        ]

        objective_preset = wtf["objective_preset"]
        assert objective_preset in OBJECTIVE_PRESETS
        self._opti_sol: OptiSol
        return

    def fix(self, optimisation_algorithm: OptimisationAlgorithm) -> None:
        """Fix the :class:`Fault`. Set ``self.optimized_cavity_settings``.

        Also display information on the parametrization of the optimization
        problem, the solution that was found.

        Parameters
        ----------
        optimisation_algorithm :
            The optimization algorithm to be used, already initialized.
        simulation_output :
            The most recent simulation, that includes the compensation settings
            of all :class:`.Fault` upstream of ``self``.

        """
        logging.info(
            "Starting resolution of optimization problem defined by:\n"
            f"{optimisation_algorithm}"
        )
        start_time = time.monotonic()

        self._opti_sol = optimisation_algorithm.optimize()

        delta_t = datetime.timedelta(seconds=time.monotonic() - start_time)
        info = (
            f"Finished! Solving this problem took {delta_t}. Results are:",
            str_objectives_solved(optimisation_algorithm.objectives),
            "Additional info:",
            "\n".join(self._opti_sol["info"]),
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
            upstream :class:`.Fault` as well as of this one.

        """
        fix_elts = fix_acc.elts

        simulation_output = beam_calculator.post_optimisation_run_with_this(
            self.optimized_cavity_settings, fix_elts
        )
        simulation_output.compute_indirect_quantities(
            fix_elts, ref_simulation_output=ref_simulation_output
        )

        fix_acc.keep(
            simulation_output,
            exported_phase=reference_phase_policy,
            beam_calculator_id=beam_calculator.id,
        )
        self._post_compensation_status(reference_phase_policy, fix_elts)
        return simulation_output

    @property
    def info(self) -> dict:
        """Return the dictionary holding information on the solution.

        .. deprecated :: 0.8.2
            Prefer using the ``opti_sol`` attribute.

        """
        info = dict(self._opti_sol)
        info["objectives_values"] = self._opti_sol["objectives"]
        return info

    @property
    def optimized_cavity_settings(self) -> SetOfCavitySettings:
        """Get the best settings."""
        return self._opti_sol["cavity_settings"]

    @property
    def success(self) -> bool:
        """Get the success status."""
        return self._opti_sol["success"]

    def pre_compensation_status(self) -> None:
        """Mark failed and compensating cavities."""
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
            "its status anyway..."
        )

    def _post_compensation_status(
        self,
        reference_phase_policy: REFERENCE_PHASE_POLICY_T,
        fix_elts: ListOfElements,
    ) -> None:
        """Update cavities status after compensation.

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
