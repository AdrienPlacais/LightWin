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
from collections.abc import Collection
from pathlib import Path
from typing import Any, Callable, Literal, TypedDict

import numpy as np

from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.elements.element import Element
from lightwin.core.elements.field_maps.cavity_settings_factory import (
    CavitySettingsFactory,
)
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.failures.set_of_cavity_settings import SetOfCavitySettings
from lightwin.optimisation.design_space.constraint import Constraint
from lightwin.optimisation.design_space.variable import Variable
from lightwin.optimisation.objective.objective import Objective


class OptiInfo(TypedDict):
    """Hold information on how optimisation went."""

    hist_X: np.ndarray
    hist_F: np.ndarray
    hist_G: np.ndarray


class OptiSol(TypedDict):
    """Hold information on the solution."""

    x: np.ndarray


ComputeBeamPropagationT = Callable[[SetOfCavitySettings], SimulationOutput]
ComputeResidualsT = Callable[[SimulationOutput], Any]
ComputeConstraintsT = Callable[[SimulationOutput], np.ndarray]


class OptimisationAlgorithm(ABC):
    """Holds the optimisation parameters, the methods to optimize.

    Parameters
    ----------
    compensating_elements : list[Element]
        Cavity objects used to compensate for the faults.
    elts : ListOfElements
        Holds the whole compensation zone under study.
    objectives : list[Objective]
        Holds objectives, initial values, bounds.
    variables : list[Variable]
        Holds variables, their initial values, their limits.
    constraints : list[Constraint] | None, optional
        Holds constraints and their limits. The default is None.
    solution : dict
        Holds information on the solution that was found.
    supports_constraints : bool
        If the method handles constraints or not.
    compute_beam_propagation: ComputeBeamPropagationT
        Method to compute propagation of the beam with the given settings.
        Defined by a :meth:`.BeamCalculator.run_with_this` method, the
        positional argument ``elts`` being set by a ``functools.partial``.
    compute_residuals : ComputeResidualsT
        Method to compute residuals from a :class:`.SimulationOutput`.
    compute_constraints : ComputeConstraintsT | None, optional
        Method to compute constraint violation. The default is None.
    folder : str | None, optional
        Where history, phase space and other optimisation information will be
        saved if necessary. The default is None.
    cavity_settings_factory : CavitySettingsFactory
        A factory to easily create the cavity settings to try at each iteration
        of the optimisation algorithm.

    """

    supports_constraints: bool

    def __init__(
        self,
        compensating_elements: Collection[Element],
        elts: ListOfElements,
        objectives: Collection[Objective],
        variables: Collection[Variable],
        compute_beam_propagation: ComputeBeamPropagationT,
        compute_residuals: ComputeResidualsT,
        cavity_settings_factory: CavitySettingsFactory,
        constraints: Collection[Constraint] | None = None,
        compute_constraints: ComputeConstraintsT | None = None,
        folder: Path | None = None,
        optimisation_algorithm_kwargs: dict[str, Any] | None = None,
        **kwargs,
    ) -> None:
        """Instantiate the object."""
        assert all([elt.can_be_retuned for elt in compensating_elements])
        self.compensating_elements = compensating_elements
        self.elts = elts

        self.objectives = objectives
        self.variables = variables
        self.compute_beam_propagation = compute_beam_propagation
        self.compute_residuals = compute_residuals
        self.constraints = constraints

        if self.supports_constraints:
            assert compute_constraints is not None
        self.compute_constraints = compute_constraints
        self.folder = folder
        self.cavity_settings_factory = cavity_settings_factory

        self.solution: OptiSol
        self.supports_constraints: bool

        if optimisation_algorithm_kwargs is None:
            optimisation_algorithm_kwargs = {}
        self.optimisation_algorithm_kwargs = (
            self._default_kwargs | optimisation_algorithm_kwargs
        )

    @property
    def variable_names(self) -> list[str]:
        """Give name of all variables."""
        return [variable.name for variable in self.variables]

    @property
    def n_var(self) -> int:
        """Give number of variables."""
        return len(self.variables)

    @property
    def n_obj(self) -> int:
        """Give number of objectives."""
        return len(self.objectives)

    @property
    def n_constr(self) -> int:
        """Return number of (inequality) constraints."""
        if self.constraints is None:
            return 0
        return sum(
            [constraint.n_constraints for constraint in self.constraints]
        )

    @property
    def _default_kwargs(self) -> dict[str, Any]:
        """Give the default optimisation algorithm kwargs."""
        return {}

    @abstractmethod
    def optimise(
        self,
        keep_history: bool = False,
        save_history: bool = False,
    ) -> tuple[bool, SetOfCavitySettings | None, OptiInfo]:
        """Set up optimisation parameters and solve the problem.

        Parameters
        ----------
        keep_history : bool, optional
            To keep all the variables that were tried as well as the associated
            objective and constraint violation values.
        save_history : bool, optional
            To save the history.

        Returns
        -------
        success : bool
            Tells if the optimisation algorithm managed to converge.
        optimized_cavity_settings : SetOfCavitySettings
            Best solution found by the optimization algorithm. None if no
            satisfactory solution was found.
        info : OptiInfo
            Gives list of solutions, corresponding objective, convergence
            violation if applicable, etc.

        """

    def _format_variables(self) -> Any:
        """Adapt all :class:`.Variable` to this optimisation algorithm."""

    def _format_objectives(self) -> Any:
        """Adapt all :class:`.Objective` to this optimisation algorithm."""

    def _format_constraints(self) -> Any:
        """Adapt all :class:`.Constraint` to this optimisation algorithm."""

    def _wrapper_residuals(self, var: np.ndarray) -> np.ndarray:
        """Compute residuals from an array of variable values."""
        cav_settings = self._create_set_of_cavity_settings(var)
        simulation_output = self.compute_beam_propagation(cav_settings)
        residuals = self.compute_residuals(simulation_output)
        return residuals

    def _norm_wrapper_residuals(self, var: np.ndarray) -> float:
        """Compute norm of residues vector from an array of variable values."""
        return float(np.linalg.norm(self._wrapper_residuals(var)))

    def _create_set_of_cavity_settings(
        self,
        var: np.ndarray,
        status: str = "compensate (in progress)",
    ) -> SetOfCavitySettings:
        """Transform ``var`` into generic :class:`.SetOfCavitySettings`.

        Parameters
        ----------
        var
            An array holding the variables to try.
        status : str, optional
            mmmh

        Returns
        -------
        SetOfCavitySettings
            Object holding the settings of all the cavities.

        """
        reference = [x for x in self.variable_names if "phi" in x][0]
        original_settings = [
            cavity.cavity_settings for cavity in self.compensating_elements
        ]

        several_cavity_settings = (
            self.cavity_settings_factory.from_optimisation_algorithm(
                base_settings=original_settings,
                var=var,
                reference=reference,
                status=status,
            )
        )
        return SetOfCavitySettings.from_cavity_settings(
            several_cavity_settings, self.compensating_elements
        )

    def _get_objective_values(self) -> dict[str, float]:
        """Save the full array of objective values."""
        sol = self.solution
        objectives_values = self._wrapper_residuals(sol.x)
        objectives_values = {
            objective.name: objective_value
            for objective, objective_value in zip(
                self.objectives, objectives_values
            )
        }
        return objectives_values

    def _generate_optimisation_history(
        self,
        variables_values: np.ndarray,
        objectives_values: np.ndarray,
        constraints_values: np.ndarray,
    ) -> OptiInfo:
        """Create optimisation history."""
        opti_info = OptiInfo(
            hist_X=variables_values,
            hist_F=objectives_values,
            hist_G=constraints_values,
        )
        return opti_info


class OptimizationHistory:
    """Keep all the settings that were tried."""

    settings_filename = "settings.csv"
    objectives_filename = "objectives.csv"
    constraints_filename = "constraints.csv"

    def __init__(
        self,
        history_folder: Path | None = None,
        save_interval: int = 50,
        run_id: str = "dummy",
        mode: Literal["append", "overwrite"] = "overwrite",
    ) -> None:
        """Instantiate the object.

        Parameters
        ----------
        history_folder : Path | None, optional
            Where the histories will be saved. If not provided or None is
            given, this class will not have any effect and every public method
            wil be overriden with dummy methods.
        save_interval : int, optional
            Files will be saved every ``save_interval`` iteration.
        run_id : str, optional
            An ID to keep track of the optimization parameters in the output
            files.
        mode : Literal["append", "overwrite"], optional
            If we should happen data to previous files or overwrite them.

        """
        if history_folder is None:
            self._make_public_methods_useless()
            return
        self.history_folder = history_folder
        if mode == "overwrite":
            self._remove_previous_files()

        self.settings: list[SetOfCavitySettings] = []
        self.objectives: list[list[float] | np.ndarray] = []
        self.constraints: list[list[float] | np.ndarray | None] = []

        self.start_idx = self._determine_start_idx()
        self.iteration_count: int = 0
        self.save_interval = save_interval
        self.run_id = run_id

    def _determine_start_idx(self) -> int:
        """Open ``variables.csv`` to determine at which position we should start writing.

        Used when ``mode`` is ``"append"``.

        """
        if self.mode == "overwrite":
            return 0
        raise NotImplementedError

    def _make_public_methods_useless(self) -> None:
        """Override some methods so that they do not do anything."""
        self.add_settings = lambda set_of_cavity_settings: None
        self.add_objective_values = lambda objectives: None
        self.add_constraint_values = lambda constraints: None
        self.save = lambda: None

    def add_settings(
        self, set_of_cavity_settings: SetOfCavitySettings
    ) -> None:
        """Add a new set of cavity settings, update number of iterations."""
        self.settings.append(set_of_cavity_settings)

    def add_objective_values(self, objectives: list | np.ndarray) -> None:
        """Add some objective values."""
        self.objectives.append(objectives)

    def add_constraint_values(
        self, constraints: list | np.ndarray | None
    ) -> None:
        """Add some constraint values."""
        self.constraints.append(constraints)

    def save(self) -> None:
        """Save the three histories in their respective files.

        All files will be in ``self.history_folder``.

        """
        for property, save_func in zip(
            ("settings", "objectives", "constraints"),
            (_save_settings, _save_values, _save_values),
        ):
            filename = getattr(self, property + "_filename")
            filepath = self.history_folder / filename
            values = getattr(self, property)
            save_func(filepath, self.run_id, self.start_idx, values)

        delta_i = len(self.settings)
        self.start_idx += delta_i
        self._empty_histories()

    def _remove_previous_files(self) -> None:
        """Remove the previous history files.

        This is not the default behavior, it is only called when ``self.mode``
        is ``"overwrite"``.

        """

    def _empty_histories(self) -> None:
        """Empty the histories."""
        self.settings = []
        self.objectives = []
        self.constraints = []

    def checkpoint(self) -> None:
        """Save periodically based on the defined interval."""
        self.iteration_count += 1
        if self.iteration_count % self.save_interval == 0:
            self.save()
            logging.debug(
                f"Checkpoint saved at iteration {self.iteration_count}."
            )


def _save_settings(
    filepath: Path,
    run_id: str,
    start_idx: int,
    settings: list[SetOfCavitySettings],
) -> None:
    """Save the ``settings`` to ``filepath``.

    Parameters
    ----------
    filepath : Path
       Where to save ``filepath``.
    start_idx : int
        The position at which the first :class:`.SetOfCavitySettings` should be
        saved. Also stored in the first column.
    run_id : str
        An ID to discriminate runs; useful when several optimization are kept
        in the same file. Stored in second column.
    settings : list[SetOfCavitySettings]
        The settings that will be saved, in third column and onwards.

    """
    with filepath.open("w", encoding="utf-8") as file:
        for idx, setting in enumerate(settings, start=start_idx):
            row = f"{idx},{run_id},{setting}\n"
            file.write(row)


def _save_values(
    filepath: Path,
    run_id: str,
    start_idx: int,
    values: list[list[float] | np.ndarray | None],
) -> None:
    """Save the ``values`` to ``filepath`` (can be objectives or constraints).

    Parameters
    ----------
    filepath : Path
       Where to save the values.
    start_idx : int
        The position at which the first entry should be saved.
    run_id : str
        An ID to discriminate runs; useful when several optimizations are kept
        in the same file.
    values : list[list[float] | np.ndarray | None]
        The list of values to save (objectives or constraints), starting in
        the third column. If a value is None, it is represented as 'None' in
        the file.

    """
    with filepath.open("w") as file:
        for idx, value_set in enumerate(values, start=start_idx):
            if value_set is None:
                value_str = "None"
            else:
                value_str = ",".join(map(str, value_set))
            row = f"{idx},{run_id},{value_str}\n"
            file.write(row)
