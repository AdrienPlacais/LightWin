"""Wrap-up creation and execution of :class:`.ISimulationOutputEvaluator`.

.. todo::
    Maybe should inherit from a more generic factory.

"""

import logging
from collections.abc import Collection, Sequence
from pathlib import Path
from typing import Any

import pandas as pd

import lightwin.util.pandas_helper as pandas_helper
from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.experimental.new_evaluator.simulation_output.i_simulation_output_evaluator import (
    ISimulationOutputEvaluator,
)
from lightwin.experimental.new_evaluator.simulation_output.presets import (
    SIMULATION_OUTPUT_EVALUATORS,
)
from lightwin.experimental.plotter.i_plotter import IPlotter
from lightwin.experimental.plotter.matplotlib_plotter import MatplotlibPlotter
from lightwin.util.helper import get_constructors


class SimulationOutputEvaluatorsFactory:
    """Define a class to create and execute multiple evaluators."""

    def __init__(
        self,
        evaluator_kwargs: Collection[dict[str, str | float | bool]],
        user_evaluators: dict[str, type] | None = None,
        plotter: IPlotter | None = None,
    ) -> None:
        """Instantiate object with basic attributes.

        Parameters
        ----------
        evaluator_kwargs :
            Dictionaries holding necessary information to instantiate the
            evaluators. The only mandatory key-value pair is ``"name"`` of type
            ``str``.
        user_evaluators :
            Additional user-defined evaluators; keys should be in PascalCase,
            values :class:`.ISimulationOutputEvaluator` constructors.
        plotter :
            An object used to produce plots.

        """
        self._plotter = plotter if plotter else MatplotlibPlotter()
        self._constructors_n_kwargs = _constructors_n_kwargs(
            evaluator_kwargs, user_evaluators
        )

    def run(
        self,
        accelerators: Sequence[Accelerator],
        solvers_ids: str | Sequence[str],
    ) -> list[ISimulationOutputEvaluator]:
        """Instantiate all the evaluators.

        Parameters
        ----------
        accelerators :
            Objects holding all the different :class:`.SimulationOutput`.
        solver_ids :
            Name of the reference solver(s). If several are provided, we use
            the first one by default; we use the following if necessary data
            was not available.

        """
        if isinstance(solvers_ids, str):
            solvers_ids = (solvers_ids,)

        evaluators: list[ISimulationOutputEvaluator] = []

        for i, (constructor, kwargs) in enumerate(
            self._constructors_n_kwargs.items()
        ):
            for id in solvers_ids:
                evaluator = constructor(
                    reference=accelerators[0].simulation_outputs[id],
                    fignum=100 + i,
                    plotter=self._plotter,
                    **kwargs,
                )
                if evaluator.data_is_gettable():
                    evaluators.append(evaluator)
                    break
            else:
                logging.warning(
                    f"None of the provided beam calculators ({solvers_ids}) "
                    f"calculates the data necesary for {constructor.__name__},"
                    " so it was skipped."
                )
        return evaluators

    def batch_evaluate(
        self,
        evaluators: Collection[ISimulationOutputEvaluator],
        accelerators: Sequence[Accelerator],
        csv_kwargs: dict[str, Any] | None = None,
        get_overrides: dict[str, Any] | None = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Evaluate several evaluators.

        Parameters
        ----------
        evaluators :
            Evaluations to realize.
        accelerators :
            Objects holding all the :class:`.SimulationOutput` to be evaluated.
        beam_solver_ids :
            Name of the solvers that created the :class:`.SimulationOutput`.
            They must be keys of the :attr:`.Accelerator.simulation_outputs`
            dictionary.
        csv_kwargs :
            Keyword arguments passed to :func:`.pandas_helper.to_csv`.
        get_overrides :
            Keyword arguments passed to :meth:`.SimulationOutput.get`,
            overriding defaults. For example, if you want your evaluators to
            run on a smaller portion of the linac.

        """
        simulation_outputs = [
            simulation
            for acc in accelerators
            for simulation in acc.simulation_outputs.values()
        ]
        elts = [x.elts for x in accelerators]
        folder = _out_folders(simulation_outputs)[-1]

        tests = {}
        data_used_for_tests = {}
        for evaluator in evaluators:
            test, data = evaluator.evaluate(
                *simulation_outputs, **(get_overrides or {})
            )
            evaluator.plot(data, elts=elts, png_folder=folder, **kwargs)

            tests[repr(evaluator)] = test
            data_used_for_tests[str(evaluator)] = data

        tests_as_pd = pd.DataFrame(tests)
        pandas_helper.to_csv(
            tests_as_pd,
            path=folder.parents[1] / "tests.csv",
            **(csv_kwargs or {}),
        )
        for key, val in data_used_for_tests.items():
            pandas_helper.to_csv(
                val,
                folder.parent / f"{key}.csv",
                **(csv_kwargs or {}),
            )

        return tests_as_pd


def _constructors_n_kwargs(
    evaluator_kwargs: Collection[dict[str, str | float | bool]],
    user_evaluators: dict[str, type] | None = None,
) -> dict[type, dict[str, bool | float | str]]:
    """Take and associate every evaluator class with its kwargs.

    We also remove the ``"name"`` key from the kwargs.

    Parameters
    ----------
    evaluator_kwargs :
        Dictionaries holding necessary information to instantiate the
        evaluators. The only mandatory key-value pair is ``"name"`` of type
        ``str``.
    user_evaluators :
        Additional user-defined evaluators; keys should be in PascalCase,
        values :class:`.ISimulationOutputEvaluator` constructors.

    Returns
    -------
        Keys are class constructor, values associated keyword arguments.

    """
    evaluator_ids = []
    for kwargs in evaluator_kwargs:
        assert "name" in kwargs
        name = kwargs.pop("name")
        assert isinstance(name, str)
        evaluator_ids.append(name)

    evaluator_constructors = SIMULATION_OUTPUT_EVALUATORS
    evaluator_constructors.update(user_evaluators or {})

    constructors = get_constructors(evaluator_ids, evaluator_constructors)

    constructors_n_kwargs = {
        constructor: kwargs
        for constructor, kwargs in zip(
            constructors, evaluator_kwargs, strict=True
        )
    }
    return constructors_n_kwargs


def _out_folders(
    simulation_outputs: Collection[SimulationOutput],
) -> list[Path]:
    """Get the output folders."""
    paths = []
    for x in simulation_outputs:
        if not hasattr(x, "out_path"):
            logging.error(
                "You must set the out_path attribute of SimulationOutput "
                "object. Look at Accelerator.keep_simulation_output."
            )
            paths.append(x.out_folder)
            continue
        paths.append(x.out_path)
    return paths
