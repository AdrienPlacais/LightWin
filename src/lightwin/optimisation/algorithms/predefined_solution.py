"""Define a pass-through 'algorithm' that accepts a pre-built solution."""

from collections.abc import Collection
from typing import Any

import numpy as np

from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.elements.field_maps.cavity_settings_factory import (
    CavitySettingsFactory,
)
from lightwin.failures.set_of_cavity_settings import (
    FieldMap,
    SetOfCavitySettings,
)
from lightwin.optimisation.algorithms.algorithm import (
    ComputeBeamPropagationT,
    OptimisationAlgorithm,
    OptiSol,
)
from lightwin.optimisation.design_space.design_space import DesignSpace
from lightwin.optimisation.objective.factory import ObjectiveFactory


class PredefinedSolution(OptimisationAlgorithm):
    """Bypass optimization and use a pre-built cavity settings solution.

    Useful for testing, replaying a known solution, or warm-starting a
    downstream workflow without running a solver.

    """

    supports_constraints = False

    def __init__(
        self,
        *,
        compensating_elements: Collection[FieldMap],
        objective_factory: ObjectiveFactory,
        design_space: DesignSpace,
        compute_beam_propagation: ComputeBeamPropagationT,
        cavity_settings_factory: CavitySettingsFactory,
        reference_simulation_output: SimulationOutput,
        predefined_cavity_settings: SetOfCavitySettings,
        optimisation_algorithm_kwargs: dict[str, Any] | None = None,
        history_kwargs: dict[str, Any] | None = None,
        predefined_simulation_output: SimulationOutput | None = None,
        **kwargs,
    ) -> None:
        """Instantiate a fake algorithm bypassing optimization.

        Parameters
        ----------
        compensating_elements :
            Tunable elements performing compensation.
        objective_factory :
            Objects holding :class:`.Objective` creation logic.
        design_space :
            Holds :class:`.Variable`, :class:`.Constraint`.
        compute_beam_propagation :
            Takes in a :class:`.SetOfCavitySettings`, propages the beam in a
            version of ``elts`` that uses them, and produce a |SO|.
        cavity_settings_factory :
            An object that can create :class:`.SetOfCavitySettings` easily.
        reference_simulation_output :
            The reference simulation output on the reference accelerator.
        predefined_cavity_settings :
            The solution to use directly.
        optimisation_algorithm_kwargs :
            Additional kwargs for algorithm, set by user in the configuration
            ``TOML``.
        history_kwargs :
            If given, records in a file the different evaluations of residuals
            during optimization.
        predefined_simulation_output :
            If provided, residuals are computed from this output rather than
            re-running beam propagation. Useful when you already have the
            associated simulation results.

        """
        super().__init__(
            compensating_elements=compensating_elements,
            objective_factory=objective_factory,
            design_space=design_space,
            compute_beam_propagation=compute_beam_propagation,
            cavity_settings_factory=cavity_settings_factory,
            reference_simulation_output=reference_simulation_output,
            optimisation_algorithm_kwargs=optimisation_algorithm_kwargs,
            history_kwargs=history_kwargs,
            **kwargs,
        )
        self._preset_cavity_settings = predefined_cavity_settings
        self._preset_simulation_output = predefined_simulation_output

    def optimize(self) -> OptiSol:
        """Skip optimization and return the pre-built solution directly."""
        self.opti_sol = self._generate_opti_sol()
        self._finalize(self.opti_sol)
        return self.opti_sol

    def _generate_opti_sol(self) -> OptiSol:
        """Build sol from predefined settings, computing beam only if
        needed."""
        simulation_output = (
            self._preset_simulation_output
            or self.compute_beam_propagation(self._preset_cavity_settings)
        )
        residuals = self._compute_residuals(simulation_output)
        objectives = {
            str(objective): float(value)
            for objective, value in zip(
                self.objectives, residuals, strict=True
            )
        }

        var = np.full(self.n_var, np.nan)

        opti_sol: OptiSol = {
            "var": var,
            "cavity_settings": self._preset_cavity_settings,
            "fun": residuals,
            "objectives": objectives,
            "success": True,
            "info": [
                self.__class__.__name__,
                "Predefined solution, no optimization performed.",
            ],
        }
        return opti_sol
