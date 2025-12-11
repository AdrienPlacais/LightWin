"""Define helper functions to set up LightWin workflow."""

import logging
from collections.abc import Collection
from typing import Any

from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.beam_calculation.factory import BeamCalculatorsFactory
from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.core.accelerator.factory import AcceleratorFactory
from lightwin.failures.fault_scenario import (
    FaultScenario,
    FaultScenarioFactory,
)
from lightwin.failures.strategy import determine_cavities
from lightwin.optimisation.objective.factory import ObjectiveFactory
from lightwin.util.typing import BeamKwargs
from lightwin.visualization import plot


def set_up_solvers(
    config: dict[str, dict[str, Any] | BeamKwargs],
) -> tuple[BeamCalculator, ...]:
    """Create the beam calculators.

    Parameters
    ----------
    config :
        The full ``TOML`` configuration dictionary.

    Returns
    -------
        The objects that will compute the beam propagation.

    """
    factory = BeamCalculatorsFactory(**config)
    beam_calculators = factory.run_all()
    return beam_calculators


def set_up_accelerators(
    config: dict[str, dict[str, Any] | BeamKwargs],
    beam_calculators: tuple[BeamCalculator, ...],
) -> list[Accelerator]:
    """Create the accelerators.

    .. note::
       If an automatic study is asked, the ``wtf`` dictionary is updated to
       explicitly mention the list of failed cavities.

    Parameters
    ----------
    config :
        The full ``TOML`` configuration dictionary.
    beam_calculators :
        The objects that will compute the beam propagation.

    Returns
    -------
        A nominal :class:`.Accelerator` without failure, and an
        :class:`.Accelerator` per fault scenario.

    """
    factory = AcceleratorFactory(beam_calculators, **config)
    reference_accelerator = factory.create_nominal()

    wtf = config.get("wtf")
    if not wtf:
        return [reference_accelerator]

    n_scenarios, updated_wtf = determine_cavities(
        reference_accelerator.elts, wtf
    )
    config["wtf"] = updated_wtf
    accelerators = factory.create_failed(n_objects=n_scenarios)
    return [reference_accelerator] + accelerators


def set_up_faults(
    config: dict[str, dict[str, Any] | BeamKwargs],
    beam_calculator: BeamCalculator,
    accelerators: list[Accelerator],
    objective_factory_class: type[ObjectiveFactory] | None = None,
    **kwargs,
) -> list[FaultScenario]:
    """Create all the :class:`.Fault`, gather them in :class:`.FaultScenario`.

    Parameters
    ----------
    config :
        The full ``TOML`` configuration dict.
    beam_calculator :
        The object that will be used for the optimization. Usually, a fast
        solver such as :class:`.CyEnvelope1D`.
    accelerators :
        First object is the reference linac; second object is the one we will
        break and fix.
    objective_factory_class :
        If provided, will override the ``objective_preset``. Used to let user
        define its own :class:`.ObjectiveFactory` without altering the source
        code.

    Returns
    -------
        The instantiated fault scenarios.

    """
    beam_calculator.compute(accelerators[0])
    factory = FaultScenarioFactory(
        accelerators,
        beam_calculator,
        config.get("design_space"),
        objective_factory_class=objective_factory_class,
    )
    return factory.create(**config.get("wtf"))


def set_up(
    config: dict[str, dict[str, Any] | BeamKwargs],
    **kwargs,
) -> tuple[
    tuple[BeamCalculator, ...],
    list[Accelerator],
    list[FaultScenario] | None,
    list[SimulationOutput],
]:
    """Create all the objects used in a typical LightWin simulation.

    Parameters
    ----------
    config :
        The full ``TOML`` configuration dictionary.

    Returns
    -------
    beam_calculators :
        The objects to compute the beam. Typically, they are two: one for the
        optimization, and a second slower one to run a more precise simulation.
    accelerators :
        The objects that will store a linac design. Typically, they are two:
        one for the reference linac, and one for the broken/fixed linac.
     fault_scenarios :
        The created failures. Will be None if no ``"wtf"`` entry was given in
        ``config``.
     ref_simulations_outputs :
        A reference :class:`.SimulationOutput` corresponding to the nominal
        linac per :class:`.BeamCalculator`.

    """
    beam_calculators = set_up_solvers(config)
    accelerators = set_up_accelerators(config, beam_calculators)

    fault_scenarios = None
    if "wtf" in config:
        fault_scenarios = set_up_faults(
            config, beam_calculators[0], accelerators, **kwargs
        )

    ref_simulations_outputs = [
        x.compute(accelerators[0]) for x in beam_calculators
    ]
    return (
        beam_calculators,
        accelerators,
        fault_scenarios,
        ref_simulations_outputs,
    )


def fix(fault_scenarios: Collection[FaultScenario] | None) -> None:
    """Fix all the generated faults.

    Parameters
    ----------
     fault_scenarios :
        The created failures. Will be None if no ``"wtf"`` entry was given in
        ``config``.

    """
    if fault_scenarios is None:
        logging.info("No fault was set!")
        return
    for fault_scenario in fault_scenarios:
        fault_scenario.fix_all()


def recompute(
    beam_calculators: Collection[BeamCalculator],
    references: Collection[SimulationOutput],
    *accelerators: Accelerator,
) -> list[list[SimulationOutput]]:
    """Recompute accelerator after a fix with more precision.

    Parameters
    ----------
    beam_calculators :
        One or several beam calculators.
    references :
        A reference :class:`.SimulationOutput` per :class:`.BeamCalculator`,
        ideally generated by the same :class:`.BeamCalculator`.
    accelerators :
        One or several fixed linacs.

    Returns
    -------
    list[list[SimulationOutput]]
        A nested list of simulation results.

    """
    simulation_outputs = [
        [
            beam_calculator.compute(
                accelerator, ref_simulation_output=reference
            )
            for accelerator in accelerators
        ]
        for beam_calculator, reference in zip(
            beam_calculators, references, strict=True
        )
    ]
    return simulation_outputs


def run_simulation(
    config: dict[str, Any],
    **kwargs,
) -> list[FaultScenario] | list[Accelerator]:
    """Compute propagation of beam; if failures are defined, fix them.

    Parameters
    ----------
    config :
        The full TOML configuration dict.

    Returns
    -------
    list[FaultScenario] | list[Accelerator]
        If no failure is defined, return the created accelerators. If failures
        were defined, return the full fault scenarios. Note that you can access
        the accelerator objects with ``FaultScenario.ref_acc`` and
        ``FaultScenario.fix_acc``.

    """
    beam_calculators, accelerators, fault_scenarios, ref_simulation_output = (
        set_up(config, **kwargs)
    )
    if fault_scenarios is None:
        plot.factory(accelerators, **config)
        return accelerators

    fix(fault_scenarios)
    recompute(
        beam_calculators[1:], ref_simulation_output[1:], *accelerators[1:]
    )
    plot.factory(accelerators, fault_scenarios=fault_scenarios, **config)

    return fault_scenarios
