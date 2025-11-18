"""Wrap-up creation and execution of :class:`.ISimulationOutputEvaluator`.

.. todo::
    Maybe should inherit from a more generic factory.

"""

import logging
from collections.abc import Collection, Sequence
from pathlib import Path
from typing import Any

import pandas as pd

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
from lightwin.experimental.plotter.pd_plotter import PandasPlotter
from lightwin.util import pandas_helper
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
        self._plotter = plotter if plotter else PandasPlotter()
        self._constructors_n_kwargs = _constructors_n_kwargs(
            evaluator_kwargs, user_evaluators
        )

    def run(
        self, accelerators: Sequence[Accelerator], beam_solver_id: str
    ) -> list[ISimulationOutputEvaluator]:
        """Instantiate all the evaluators."""
        reference = accelerators[0].simulation_outputs[beam_solver_id]
        evaluators = self._instantiate_evaluators(reference)
        return evaluators

    def _instantiate_evaluators(
        self, reference: SimulationOutput
    ) -> list[ISimulationOutputEvaluator]:
        """Create all the evaluators.

        Parameters
        ----------
        reference :
            The reference simulation output.

        Returns
        -------
            All the created evaluators.

        """
        evaluators = [
            constructor(
                reference=reference,
                fignum=100 + i,
                plotter=self._plotter,
                **kwargs,
            )
            for i, (constructor, kwargs) in enumerate(
                self._constructors_n_kwargs.items()
            )
        ]
        return evaluators

    def batch_evaluate(
        self,
        evaluators: Collection[ISimulationOutputEvaluator],
        accelerators: Sequence[Accelerator],
        beam_solver_id: str,
        csv_kwargs: dict[str, Any] | None = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Evaluate several evaluators."""
        simulation_outputs = [
            x.simulation_outputs[beam_solver_id] for x in accelerators
        ]
        elts = [x.elts for x in accelerators]
        folders = _out_folders(simulation_outputs)

        tests = {}
        data_used_for_tests = {}
        for evaluator in evaluators:
            test, data = evaluator.evaluate(*simulation_outputs, **kwargs)
            evaluator.plot(data, elts=elts, **kwargs)

            tests[str(evaluator)] = test
            data_used_for_tests[str(evaluator)] = data

        index = [folder.parent.stem for folder in folders]

        tests_as_pd = pd.DataFrame(tests, index=index)
        # data_as_pd = pd.DataFrame(data_used_for_tests, index=index)
        #
        # pandas_helper.to_csv(
        #     tests_as_pd,
        #     path=folders[0].parents[1] / "tests.csv",
        #     **(csv_kwargs or {}),
        # )
        # pandas_helper.to_csv(
        #     data_as_pd,
        #     path=folders[0].parents[1] / "data_used_for_tests.csv",
        #     **(csv_kwargs or {}),
        # )

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
