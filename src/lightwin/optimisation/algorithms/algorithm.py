"""Define the Abstract Base Class of optimisation algorithms.

Abstract methods are mandatory and a ``TypeError`` will be raised if you try to
create your own algorithm and omit them.

When you add you own optimisation algorithm, do not forget to add it to the
list of implemented algorithms in the :mod:`.algorithm` module.

.. todo::
    Check if it is necessary to pass out the whole ``elts`` to
    :class:`.OptimisationAlgorithm`?

.. todo::
    Methods and flags to keep the optimisation history or not, and also to save
    it or not. See :class:`.Explorator`.

.. todo::
    Better handling of the attribute ``folder``. In particular, a correct value
    should be set at the ``OptimisationAlgorithm`` instanciation.

"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Collection, Mapping
from pathlib import Path
from typing import Any, Callable, NotRequired, TypedDict, final

import numpy as np
from numpy.typing import NDArray

from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.elements.field_maps.cavity_settings import CavitySettings
from lightwin.core.elements.field_maps.cavity_settings_factory import (
    CavitySettingsFactory,
)
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.optimisation.design_space.design_space import DesignSpace
from lightwin.optimisation.objective.factory import ObjectiveFactory
from lightwin.optimisation.objective.objective import str_objectives
from lightwin.util.typing import REFERENCE_PHASES, REFERENCE_PHASES_T


class OptiSol(TypedDict):
    """Hold information on the solution."""

    #: Value of variables
    var: NDArray[np.float64] | list[float]
    #: Value of var, but more logical
    cavity_settings: dict[FieldMap, CavitySettings]
    #: Value of objectives
    fun: NDArray[np.float64] | list[float]
    #: Maps name of objectives with their value.
    objectives: dict[str, float]
    #: Value of constraint violation
    cv: NotRequired[float]
    #: Maps name of constaint with cv value.
    constraints: NotRequired[dict[str, float]]
    #: If optimization was successful
    success: bool
    #: Complementary information
    info: list[str]


ComputeBeamPropagationT = Callable[
    [Mapping[FieldMap, CavitySettings]], SimulationOutput
]
ComputeResidualsT = Callable[[SimulationOutput], Any]
ComputeConstraintsT = Callable[[SimulationOutput], NDArray[np.float64]]


class OptimisationAlgorithm(ABC):
    """Holds the optimization parameters, the methods to optimize."""

    supports_constraints: bool

    def __init__(
        self,
        *,
        compensating_elements: Collection[FieldMap],
        objective_factory: ObjectiveFactory,
        design_space: DesignSpace,
        compute_beam_propagation: ComputeBeamPropagationT,
        cavity_settings_factory: CavitySettingsFactory,
        reference_simulation_output: SimulationOutput,
        optimisation_algorithm_kwargs: dict[str, Any] | None = None,
        history_kwargs: dict[str, Any] | None = None,
        **kwargs,
    ) -> None:
        """Instantiate the object.

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
        optimisation_algorithm_kwargs :
            Additional kwargs for algorithm, set by user in the configuration
            ``TOML``.
        history_kwargs :
            If given, records in a file the different evaluations of residuals
            during optimization.

        """
        self.compensating_elements = tuple(compensating_elements)

        self._objective_factory = objective_factory
        self.objectives = self._objective_factory.objectives
        self._compute_residuals = self._objective_factory.compute_residuals

        self._design_space: DesignSpace = design_space
        if self.supports_constraints:
            assert self._design_space.compute_constraints is not None
        self._variables = self._design_space.variables

        _reference_phase = tuple(
            {x.name for x in self._variables if "phi" in x.name}
        )
        assert (
            len(_reference_phase) == 1
        ), "Only one phase variable should be set"
        assert (
            _reference_phase[0] in REFERENCE_PHASES
        ), f"{_reference_phase} is an invalid phase variable"
        self._reference_phase: REFERENCE_PHASES_T = _reference_phase[0]

        self._constraints = self._design_space.constraints

        self.compute_beam_propagation = compute_beam_propagation

        self.cavity_settings_factory = cavity_settings_factory

        self.opti_sol: OptiSol
        self.supports_constraints: bool

        self.optimisation_algorithm_kwargs = self._default_kwargs | (
            optimisation_algorithm_kwargs or {}
        )

        self.history = OptimizationHistory(
            reference_simulation_output,
            [obj.position_nature().strip() for obj in self.objectives],
            **(history_kwargs or {}),
        )

    def __str__(self) -> str:
        """Concatenate ``_str__`` of variables, constraints, objectives."""
        return "\n\n".join(
            (
                str(self._design_space),
                str_objectives(list(self.objectives)),
            )
        )

    @property
    def variable_names(self) -> list[str]:
        """Give name of all variables."""
        return [variable.name for variable in self._variables]

    @property
    def n_var(self) -> int:
        """Give number of variables."""
        return len(self._variables)

    @property
    def n_obj(self) -> int:
        """Give number of objectives."""
        return len(self.objectives)

    @property
    def n_constr(self) -> int:
        """Return number of (inequality) constraints."""
        if self._constraints is None:
            return 0
        return sum(
            [constraint.n_constraints for constraint in self._constraints]
        )

    @property
    def _default_kwargs(self) -> dict[str, Any]:
        """Give the default optimisation algorithm kwargs."""
        return {}

    @abstractmethod
    def optimize(self) -> OptiSol:
        """Set up optimization parameters and solve the problem.

        Returns
        -------
            Gives list of solutions, corresponding objective, convergence
            violation if applicable, etc.

        """

    @abstractmethod
    def _generate_opti_sol(self, *args, **kwargs) -> OptiSol:
        """Takes the results of the optimization in any form, returns dict."""
        pass

    def _format_variables(self) -> Any:
        """Adapt all :class:`.Variable` to this optimisation algorithm."""

    def _format_objectives(self) -> Any:
        """Adapt all :class:`.Objective` to this optimisation algorithm."""

    def _format_constraints(self) -> Any:
        """Adapt all :class:`.Constraint` to this optimisation algorithm."""

    def _wrapper_residuals(
        self, var: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        """Compute residuals from an array of variable values."""
        objectives, _ = self._evaluate_solution(var)
        return np.array(list(objectives.values()))

    def _norm_wrapper_residuals(self, var: NDArray[np.float64]) -> float:
        """Compute norm of residuals vector from array of variable values."""
        res = float(np.linalg.norm(self._wrapper_residuals(var)))
        return res

    @final
    def _finalize(self, opti_sol: OptiSol) -> None:
        """End the optimization process.

        In particular:
           - Save the optimization history if applicable.
           - Store final residual values in the appropriate :class:`.Objective`
             instances.
           - Record final constraint values in history if applicable.

        """
        for objective, residual in zip(
            self.objectives, opti_sol["objectives"].values(), strict=True
        ):
            objective.residual = residual

        fresh_objectives, constraints = self._evaluate_solution(
            opti_sol["var"]
        )

        if constraints is not None:
            opti_sol["constraints"] = constraints
            opti_sol["cv"] = float(
                np.sum(np.maximum(list(constraints.values()), 0.0))
            )

        self._check_consistency(opti_sol, fresh_objectives)
        self.history.save()

    def _to_cavity_settings(
        self, var: NDArray[np.float64]
    ) -> dict[FieldMap, CavitySettings]:
        """Transform ``var`` into :class:`.CavitySettings`.

        Parameters
        ----------
        var :
            A ``(2n,)`` array holding the settings to try, where first half
            holds the amplitudes and second the phases.

        Returns
        -------
            Maps compensating elements with their :class:`.CavitySettings`.

        """
        amplitudes = list(var[var.shape[0] // 2 :])
        phases = list(var[: var.shape[0] // 2])

        original_settings = [
            cavity.cavity_settings for cavity in self.compensating_elements
        ]

        cavity_settings_to_try = (
            self.cavity_settings_factory.for_optimisation_algorithm(
                base_settings=original_settings,
                amplitudes=amplitudes,
                phases=phases,
                reference=self._reference_phase,
            )
        )
        return {
            cav: settings
            for cav, settings in zip(
                self.compensating_elements, cavity_settings_to_try, strict=True
            )
        }

    @final
    def _evaluate_solution(
        self, var: NDArray[np.float64]
    ) -> tuple[dict[str, float], dict[str, float] | None]:
        """Evaluate objectives and constraints for a single solution.

        Runs the simulation once and returns both, avoiding redundant beam
        propagation calls when both are needed (e.g. in :meth:`._finalize`).

        Parameters
        ----------
        var :
            Array of variable values.

        Returns
        -------
        objectives :
            Maps objective names to their values.
        constraints :
            Constraint violation array, or ``None`` if no constraints defined.

        """
        cav_settings = self._to_cavity_settings(var)
        simulation_output = self.compute_beam_propagation(cav_settings)

        residuals = self._compute_residuals(simulation_output)
        objectives = {
            str(objective): value
            for objective, value in zip(
                self.objectives, residuals, strict=True
            )
        }

        cv = None
        constraints = None
        if self.n_constr > 0:
            cv = self._design_space.compute_constraints(simulation_output)
            constraints = {str(c): c for c in cv}

        self.history.add_settings(var)
        self.history.add_objective_values(list(residuals), simulation_output)
        if cv is not None:
            self.history.add_constraint_values(cv)
        self.history.checkpoint()

        return objectives, constraints

    @final
    def _check_consistency(
        self, opti_sol: OptiSol, fresh_objectives: dict[str, float]
    ) -> None:
        """Compare stored objectives with a fresh evaluation."""
        stored = np.array(list(opti_sol["objectives"].values()))
        fresh = np.array(list(fresh_objectives.values()))

        if np.allclose(stored, fresh, rtol=1e-3):
            logging.debug("Consistency check passed.")
            return

        rel_diff = np.abs(fresh - stored) / (np.abs(stored) + 1e-12)
        logging.warning(
            f"Consistency check FAILED for {self.__class__.__name__}:\n"
            + "\n".join(
                f"  {name}: stored={s:.6g}, fresh={f:.6g}, rel_diff={d:.2e}"
                for name, s, f, d in zip(
                    opti_sol["objectives"].keys(),
                    stored,
                    fresh,
                    rel_diff,
                    strict=True,
                )
            )
        )


class OptimizationHistory:
    """Keep all the settings that were tried."""

    _settings_filename = "settings.csv"
    _objectives_filename = "objectives.csv"
    _constraints_filename = "constraints.csv"

    def __init__(
        self,
        reference_simulation_output: SimulationOutput,
        objectives_names: Collection[str],
        get_args: tuple[str, ...] = (),
        get_kwargs: dict[str, Any] | None = None,
        folder: Path | str | None = None,
        save_interval: int = 100,
        **kwargs,
    ) -> None:
        """Instantiate the object.

        Parameters
        ----------
        get_args, get_kwargs :
            args and kwargs passed to the ``SimulationOutput.get`` method. Used
            to add some values to the output files.
        get_kwargs :
            Keyword arguments for the SimulationOutput.get method.
        folder :
            Where the histories will be saved. If not provided or None is
            given, this class will not have any effect and every public method
            wil be overriden with dummy methods.
        save_interval :
            Files will be saved every ``save_interval`` iteration.

        """
        if folder is None:
            self._make_public_methods_useless()
            return
        if isinstance(folder, str):
            folder = Path(folder)
        self._folder = folder

        self._get_args = get_args
        if get_kwargs is None:
            get_kwargs = {}
        self._get_kwargs = get_kwargs

        self._rename_previous_files()

        self._settings: list[NDArray[np.float64]] = []
        self._objectives: list[list[float | None] | list[str]] = list(
            self._init_objective_hist(
                objectives_names, reference_simulation_output
            )
        )
        self._constraints: list[list[float] | NDArray[np.float64] | None] = []

        self._start_idx = 0
        self._iteration_count: int = 0
        self._save_interval = save_interval

    def _make_public_methods_useless(self) -> None:
        """Override some methods so that they do not do anything."""
        self.add_settings = lambda var: None
        self.add_objective_values = lambda objectives, simulation_output: None
        self.add_constraint_values = lambda constraints: None
        self.save = lambda: None
        self.checkpoint = lambda: None

    def add_settings(self, var: NDArray[np.float64]) -> None:
        """Add a new set of cavity settings."""
        self._settings.append(var)

    def _init_objective_hist(
        self,
        objectives_names: Collection[str],
        reference_simulation_output: SimulationOutput,
    ) -> tuple[list[str], list[None | float]]:
        """Create the objective history, with header and reference values."""
        header_objective, header_outputs = self._objective_headers(
            objectives_names
        )

        reference_objective = [None for _ in header_objective]
        reference_outputs = self._simulation_output_to_objectives(
            reference_simulation_output
        )

        objectives = (
            header_objective + header_outputs,
            reference_objective + reference_outputs,
        )
        return objectives

    def _simulation_output_to_objectives(
        self, simulation_output: SimulationOutput
    ) -> list[float]:
        """Extract and format desired values from ``simulation_output``."""
        values = list(
            simulation_output.get(
                *self._get_args, to_numpy=False, **self._get_kwargs
            )
        )
        return values

    def _objective_headers(
        self, objectives_names: Collection[str]
    ) -> tuple[list[str], list[str]]:
        """Get the objective headers."""
        header_objective = list(objectives_names)
        header_outputs = [
            f"{qty} @ {elt}"
            for elt in self._get_kwargs.get("elt", ())
            for qty in self._get_args
        ]
        return header_objective, header_outputs

    def add_objective_values(
        self, objectives: list, simulation_output: SimulationOutput
    ) -> None:
        """Add some objective values."""
        sim_output_vals = self._simulation_output_to_objectives(
            simulation_output
        )
        self._objectives.append(objectives + sim_output_vals)

    def add_constraint_values(
        self, constraints: list | NDArray[np.float64] | None
    ) -> None:
        """Add some constraint values."""
        self._constraints.append(constraints)

    def save(self) -> None:
        """Save the three histories in their respective files.

        All files will be in ``self.history_folder``.

        """
        for property in ("_settings", "_objectives", "_constraints"):
            filename = getattr(self, property + "_filename")
            filepath = self._folder / filename
            values = getattr(self, property)
            _save_values(filepath, values)

        delta_i = len(self._settings)
        self._start_idx += delta_i
        self._empty_histories()
        logging.debug(
            f"Saved optimization hist at iteration {self._start_idx}."
        )

    def _rename_previous_files(self) -> None:
        """Rename the previous history files."""
        for filename in (
            self._settings_filename,
            self._objectives_filename,
            self._constraints_filename,
        ):
            filepath = self._folder / filename
            if filepath.is_file():
                filepath.rename(filepath.with_suffix(".csv.old"))

    def _empty_histories(self) -> None:
        """Empty the histories."""
        self._settings = []
        self._objectives = []
        self._constraints = []

    def checkpoint(self) -> None:
        """Save periodically based on the defined interval."""
        self._iteration_count += 1
        if self._iteration_count % self._save_interval == 0:
            self.save()


def _save_values(
    filepath: Path, values: list[list[float] | NDArray[np.float64] | None]
) -> None:
    """Save the ``values`` to ``filepath`` (can be objectives or constraints).

    Parameters
    ----------
    filepath :
       Where to save the values.
    values :
        The list of values to save (objectives or constraints), starting in
        the third column. If a value is None, it is represented as 'None' in
        the file.

    """
    with filepath.open("a", encoding="utf-8") as file:
        for value_set in values:
            if value_set is None:
                value_str = "None"
            else:
                value_str = ",".join(map(str, value_set))
            row = f"{value_str}\n"
            file.write(row)
