"""Define a list-based class holding all the :class:`.Fault` to fix.

We also define :func:`fault_scenario_factory`, a factory function creating all
the required :class:`FaultScenario` objects.

"""

import datetime
import logging
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Self

from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.beam_calculation.tracewin.tracewin import TraceWin
from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.core.elements.element import Element
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.list_of_elements.list_of_elements import sumup_cavities
from lightwin.evaluator.list_of_simulation_output_evaluators import (
    FaultScenarioSimulationOutputEvaluators,
)
from lightwin.failures import strategy
from lightwin.failures.fault import Fault
from lightwin.optimisation.algorithms.factory import (
    OptimisationAlgorithmFactory,
)
from lightwin.optimisation.design_space.factory import (
    DesignSpaceFactory,
    get_design_space_factory,
)
from lightwin.optimisation.objective.factory import (
    ObjectiveFactory,
    ObjectiveMetaFactory,
)
from lightwin.util.helper import pd_output
from lightwin.util.pickling import MyPickler
from lightwin.util.typing import (
    REFERENCE_PHASE_POLICY_T,
    REFERENCE_PHASES,
    REFERENCE_PHASES_T,
)


class FaultScenario(list[Fault]):
    """A class to hold all fault related data."""

    def __init__(
        self,
        ref_acc: Accelerator,
        fix_acc: Accelerator,
        beam_calculator: BeamCalculator,
        wtf: dict[str, Any],
        design_space_factory: DesignSpaceFactory,
        fault_idx: list[int] | list[list[int]],
        comp_idx: list[list[int]] | None = None,
        info_other_sol: list[dict] | None = None,
        objective_factory_class: type[ObjectiveFactory] | None = None,
        **kwargs,
    ) -> None:
        """Create the :class:`FaultScenario` and the :class:`.Fault` objects.

        .. todo::
            Could be cleaner.

        Parameters
        ----------
        ref_acc :
            The reference linac (nominal or baseline).
        fix_acc :
            The broken linac to be fixed.
        beam_calculator :
            The solver that will be called during the optimisation process.
        wtf :
            What To Fit dictionary. Holds information on the fixing method.
        design_space_factory :
            An object to easily create the proper :class:`.DesignSpace`.
        fault_idx :
            List containing the position of the errors. If ``strategy`` is
            manual, it is a list of lists (faults already gathered).
        comp_idx :
            List containing the position of the compensating cavities. If
            ``strategy`` is manual, it must be provided.
        info_other_sol :
            Contains information on another fit, for comparison purposes.
        objective_factory_class :
            If provided, will override the ``objective_preset``. Used to let
            user define it's own :class:`.ObjectiveFactory` without altering
            the source code.

        """
        self.ref_acc = ref_acc
        self.fix_acc = fix_acc
        self.beam_calculator = beam_calculator
        self._transfer_phi0_from_ref_to_broken()

        self.wtf = wtf
        self.info_other_sol = info_other_sol
        self.info = {}
        self.optimisation_time: datetime.timedelta

        self._design_space_factory = design_space_factory
        self._list_of_elements_factory = (
            beam_calculator.list_of_elements_factory
        )
        self._objective_factory_class = objective_factory_class
        self._objective_meta_factory = ObjectiveMetaFactory(
            self._reference_simulation_output
        )

        cavities = strategy.failed_and_compensating(
            fix_acc.elts, failed=fault_idx, compensating_manual=comp_idx, **wtf
        )
        faults = self._create_faults(*cavities)
        super().__init__(faults)

        self._mark_cavities_to_rephase()
        for fault in self:
            fault.pre_compensation_status()

        self._optimisation_algorithm_factory = OptimisationAlgorithmFactory(
            opti_method=wtf["optimisation_algorithm"],
            beam_calculator=beam_calculator,
            reference_simulation_output=self._reference_simulation_output,
            **wtf,
        )
        self._objective_factories: list[ObjectiveFactory] = []

    def _create_faults(
        self, *cavities: Sequence[Sequence[FieldMap]]
    ) -> list[Fault]:
        """Create the :class:`.Fault` objects.

        Parameters
        ----------
        *cavities :
            First if the list of gathered failed cavities. Second is the list
            of corresponding compensating cavities.

        """
        faults = [
            Fault(
                reference_elts=self.ref_acc.elts,
                wtf=self.wtf,
                broken_elts=self.fix_acc.elts,
                failed_elements=faulty_cavities,
                compensating_elements=compensating_cavities,
            )
            for faulty_cavities, compensating_cavities in zip(
                *cavities, strict=True
            )
        ]
        return faults

    @property
    def _reference_simulation_output(self) -> SimulationOutput:
        """Determine wich :class:`.SimulationOutput` is the reference."""
        solvers_already_used = list(self.ref_acc.simulation_outputs.keys())
        assert len(solvers_already_used) > 0, (
            "You must compute propagation of the beam in the reference linac "
            "prior to create a FaultScenario"
        )
        solv1 = solvers_already_used[0]
        reference_simulation_output = self.ref_acc.simulation_outputs[solv1]
        return reference_simulation_output

    def fix_all(self) -> None:
        """Fix all the :class:`.Fault` objects in self."""
        start_time = time.monotonic()

        simulation_output = self._reference_simulation_output
        for fault in self:
            simulation_output = self._wrap_fix(fault, simulation_output)

        delta_t = datetime.timedelta(seconds=time.monotonic() - start_time)
        logging.info(f"Solving all the optimization problems took {delta_t}")
        self.optimisation_time = delta_t

        successes = [fault.success for fault in self]
        self.fix_acc.name = (
            f"Fixed ({successes.count(True)} of {len(successes)})"
        )

        self._evaluate_fit_quality(save=True)

        exported_phase = self.wtf.get("exported_phase", "phi_0_abs")
        self.fix_acc.elts.store_settings_in_dat(
            self.fix_acc.elts.files_info["dat_file"],
            exported_phase=exported_phase,
            save=True,
        )

    def _wrap_fix(
        self, fault: Fault, simulation_output: SimulationOutput
    ) -> SimulationOutput:
        """Fix the and recompute propagation with new settings.

        Parameters
        ----------
        fault :
            The fault to fix.
        simulation_output :
            The most recent simulation, that includes the compensation settings
            of all :class:`.Fault` upstream of ``fault``.

        Returns
        -------
            Most recent simulation, that includes the compensation settings of
            upstream :class:`.Fault` as well as of this one.

        """
        # Per-fault objects
        design_space = self._design_space_factory.run(
            fault.compensating_elements, fault.reference_elements
        )
        objective_factory = self._objective_meta_factory.create(
            fault,
            self.wtf["objective_preset"],
            self._design_space_factory.design_space_kw,
            self._objective_factory_class,
        )
        self._objective_factories.append(objective_factory)

        subset_elts = self._list_of_elements_factory.subset_list_run(
            objective_factory.elts_of_compensation_zone,
            simulation_output,
            self.fix_acc.elts.files_info,
        )

        # Create optimisation algorithm, that uses above objects
        optimisation_algorithm = self._optimisation_algorithm_factory.create(
            fault.compensating_elements,
            objective_factory,
            design_space,
            subset_elts,
        )

        # Execute optimisation and update accelerator
        fault.fix(optimisation_algorithm)
        simulation_output = fault.postprocess_fix(
            self.fix_acc,
            self.beam_calculator,
            self._reference_simulation_output,
            self._reference_phase_policy,
        )

        # TODO clean following
        df_altered = sumup_cavities(
            subset_elts, filter=lambda cav: cav.is_altered
        )
        logging.info(f"Retuned cavities:\n{pd_output(df_altered)}")
        subset_elts.store_settings_in_dat(
            subset_elts.files_info["dat_file"],
            exported_phase=self.beam_calculator.reference_phase_policy,
            save=True,
        )
        return simulation_output

    def _evaluate_fit_quality(
        self,
        save: bool = True,
        id_solver_ref: str | None = None,
        id_solver_fix: str | None = None,
    ) -> None:
        """Compute some quantities on the whole linac to see if fit is good.

        Parameters
        ----------
        save :
            To tell if you want to save the evaluation.
        id_solver_ref :
            Id of the solver from which you want reference results. The default
            is None. In this case, the first solver is taken
            (``beam_calc_param``).
        id_solver_fix :
            Id of the solver from which you want fixed results. The default is
            None. In this case, the solver is the same as for reference.

        """
        simulations = self._simulations_that_should_be_compared(
            id_solver_ref, id_solver_fix
        )

        quantities_to_evaluate = (
            "w_kin",
            "phi_abs",
            "envelope_pos_phiw",
            "envelope_energy_phiw",
            "eps_phiw",
            "mismatch_factor_zdelta",
        )
        my_evaluator = FaultScenarioSimulationOutputEvaluators(
            quantities_to_evaluate, self._objective_factories, simulations
        )
        my_evaluator.run(output=True)

        # if save:
        #     fname = 'evaluations_differences_between_simulation_output.csv'
        #     out = os.path.join(self.fix_acc.get('beam_calc_path'), fname)
        #     df_eval.to_csv(out)

    def _set_evaluation_elements(
        self,
        additional_elt: list[Element] | None = None,
    ) -> dict[str, Element]:
        """Set a the proper list of where to check the fit quality."""
        evaluation_elements = [fault.elts[-1] for fault in self]
        if additional_elt is not None:
            evaluation_elements += additional_elt
        evaluation_elements.append(self.fix_acc.elts[-1])
        return evaluation_elements

    def _simulations_that_should_be_compared(
        self, id_solver_ref: str | None, id_solver_fix: str | None
    ) -> tuple[SimulationOutput, SimulationOutput]:
        """Get proper :class:`.SimulationOutput` for comparison."""
        if id_solver_ref is None:
            id_solver_ref = list(self.ref_acc.simulation_outputs.keys())[0]

        if id_solver_fix is None:
            id_solver_fix = id_solver_ref

        if id_solver_ref != id_solver_fix:
            logging.warning(
                "You are trying to compare two SimulationOutputs created by "
                "two different solvers. This may lead to errors, as "
                "interpolations in this case are not implemented yet."
            )

        ref_simu = self.ref_acc.simulation_outputs[id_solver_ref]
        fix_simu = self.fix_acc.simulation_outputs[id_solver_fix]
        return ref_simu, fix_simu

    def pickle(
        self, pickler: MyPickler, path: Path | str | None = None
    ) -> Path:
        """Pickle (save) the object.

        This is useful for debug and temporary saves; do not use it for long
        time saving.

        """
        if path is None:
            path = self.fix_acc.accelerator_path / "fault_scenario.pkl"
        assert isinstance(path, Path)
        pickler.pickle(self, path)

        if isinstance(path, str):
            path = Path(path)
        return path

    @classmethod
    def from_pickle(cls, pickler: MyPickler, path: Path | str) -> Self:
        """Instantiate object from previously pickled file."""
        fault_scenario = pickler.unpickle(path)
        return fault_scenario  # type: ignore

    def _mark_cavities_to_rephase(self) -> None:
        """Change the status of cavities after first failure.

        Only cavities with a reference phase different from ``"phi_0_abs"`` are
        altered.

        .. todo::
           Could probably be simpler.

        """
        if self._reference_phase_policy == "phi_0_abs":
            return
        cavities = self.fix_acc.l_cav
        first_failed_index = cavities.index(self[0].failed_elements[0])
        cavities_after_first_failure = cavities[first_failed_index:]
        cavities_to_rephase = [
            c
            for c in cavities_after_first_failure
            if c.cavity_settings.reference != "phi_0_abs"
        ]
        logging.info(
            f"Marking {len(cavities_to_rephase)} cavities as 'to be rephased',"
            " because they are after a failed cavity and their reference phase "
            "is phi_s or phi_0_rel."
        )
        for cav in cavities_to_rephase:
            cav.update_status("rephased (in progress)")

    # =========================================================================
    # Reference phase related
    # =========================================================================
    def _transfer_phi0_from_ref_to_broken(self) -> None:
        """Transfer the reference phases from reference linac to broken.

        If the absolute initial phases are not kept between reference and
        broken linac, it comes down to rephasing the linac. This is what we
        want to avoid when :attr:`.BeamCalculator.reference_phase_policy` is
        set to ``"phi_0_abs"``.

        """
        ref_cavs = (x for x in self.ref_acc.l_cav)
        fix_settings = (x.cavity_settings for x in self.fix_acc.l_cav)

        for ref_cav, fix_set in zip(ref_cavs, fix_settings):
            reference_phase = self._resolve_reference_phase(ref_cav)
            fix_set.set_reference(
                reference=reference_phase,
                phi_ref=getattr(ref_cav.cavity_settings, reference_phase),
                ensure_can_be_calculated=False,
            )

    @property
    def _reference_phase_policy(self) -> REFERENCE_PHASE_POLICY_T:
        """Give reference phase policy of :class:`.BeamCalculator`."""
        return self.beam_calculator.reference_phase_policy

    def _resolve_reference_phase(
        self, reference_cavity: FieldMap
    ) -> REFERENCE_PHASES_T:
        """Get the reference phase matching the reference phase policy.

        According to the value of
        :attr:`.BeamCalculator.reference_phase_policy`:

        - ``"phi_0_abs"``, ``"phi_0_rel"``, ``"phi_s"``: take this reference.
        - ```"as_in_original_dat"``: take reference from ``reference_cavity``.

        """
        if self._reference_phase_policy in REFERENCE_PHASES:
            return self._reference_phase_policy
        return reference_cavity.cavity_settings.reference


def fault_scenario_factory(
    accelerators: list[Accelerator],
    beam_calc: BeamCalculator,
    wtf: dict[str, Any],
    design_space: dict[str, Any],
    objective_factory_class: type[ObjectiveFactory] | None = None,
    **kwargs,
) -> list[FaultScenario]:
    """Create the :class:`FaultScenario` objects (factory template).

    Parameters
    ----------
    accelerators :
        Holds all the linacs. The first one must be the reference linac,
        while all the others will be to be fixed.
    beam_calc :
        The solver that will be called during the optimisation process.
    wtf :
        The WhatToFit table of the TOML configuration file.
    design_space_kw :
        The design space table from the TOML configuration file.
    objective_factory_class :
        If provided, will override the ``objective_preset``. Used to let user
        define it's own :class:`.ObjectiveFactory` without altering the source
        code.

    Returns
    -------
        Holds all the initialized :class:`FaultScenario` objects, holding their
        already initialied :class:`.Fault` objects.

    """
    # TODO may be better to move this to beam_calculator.init_solver_parameters
    need_to_force_element_to_index_creation = (TraceWin,)
    if isinstance(beam_calc, *need_to_force_element_to_index_creation):
        _force_element_to_index_method_creation(accelerators[1], beam_calc)
    scenarios_fault_idx = wtf.pop("failed")

    scenarios_comp_idx = [None for _ in accelerators[1:]]
    if "compensating_manual" in wtf:
        scenarios_comp_idx = wtf.pop("compensating_manual")

    _ = [
        beam_calc.init_solver_parameters(accelerator)
        for accelerator in accelerators
    ]

    design_space_factory: DesignSpaceFactory
    design_space_factory = get_design_space_factory(**design_space)

    fault_scenarios = [
        FaultScenario(
            ref_acc=accelerators[0],
            fix_acc=accelerator,
            beam_calculator=beam_calc,
            wtf=wtf,
            design_space_factory=design_space_factory,
            fault_idx=fault_idx,
            comp_idx=comp_idx,
            objective_factory_class=objective_factory_class,
        )
        for accelerator, fault_idx, comp_idx in zip(
            accelerators[1:], scenarios_fault_idx, scenarios_comp_idx
        )
    ]

    return fault_scenarios


def _force_element_to_index_method_creation(
    accelerator: Accelerator,
    beam_calculator: BeamCalculator,
) -> None:
    """Run a first simulation to link :class:`.Element` with their index.

    .. note::
        To initalize a :class:`.Fault`, you need a sub:class:`.ListOfElements`.
        To create the latter, you need a ``_element_to_index`` method. It can
        only be created if you know the number of steps in every
        :class:`.Element`. So, for :class:`.TraceWin`, we run a first
        simulation.

    """
    beam_calculator.compute(accelerator)
