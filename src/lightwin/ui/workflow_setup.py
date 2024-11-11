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
from lightwin.core.accelerator.factory import NoFault, WithFaults
from lightwin.failures.fault_scenario import (
    FaultScenario,
    fault_scenario_factory,
)
from lightwin.optimisation.objective.factory import ObjectiveFactory
from lightwin.visualization import plot


def set_up_solvers(
    config: dict[str, dict[str, Any]],
) -> tuple[BeamCalculator, ...]:
    """Create the beam calculators.

    Parameters
    ----------
    config : dict[str, dict[str, Any]]
        The full TOML configuration dictionary.

    Returns
    -------
    beam_calculators : tuple[BeamCalculator, ...]
        The objects that will compute the beam propagation.

    """
    factory = BeamCalculatorsFactory(**config)
    beam_calculators = factory.run_all()
    return beam_calculators


def set_up_accelerators(
    config: dict[str, dict[str, Any]],
    beam_calculators: tuple[BeamCalculator, ...],
) -> list[Accelerator]:
    """Create the accelerators.

    Parameters
    ----------
    config : dict[str, dict[str, Any]]
        The full TOML configuration dictionary.
    beam_calculators : tuple[BeamCalculator, ...]
        The objects that will compute the beam propagation.

    Returns
    -------
    list[Accelerator]
        The instantiated :class:`.Accelerator`. If there is no fault defined,
        we return a single :class:`.Accelerator`. If there is a fault, we
        return a reference :class:`.Accelerator` and a broken one.

    """
    if "wtf" not in config:
        factory = NoFault(beam_calculators=beam_calculators[0], **config)
        accelerators = factory.run()
        return [accelerators]

    factory = WithFaults(beam_calculators=beam_calculators, **config)
    accelerators = factory.run_all()
    return accelerators


def set_up_faults(
    config: dict[str, dict[str, Any]],
    beam_calculator: BeamCalculator,
    accelerators: list[Accelerator],
    objective_factory_class: type[ObjectiveFactory] | None = None,
    **kwargs,
) -> list[FaultScenario]:
    """Create all the :class:`.Fault`, gather them in :class:`.FaultScenario`.

    Parameters
    ----------
    config : dict[str, dict[str, Any]]
        The full TOML configuration dict.
    beam_calculator : BeamCalculator
        The object that will be used for the optimization. Usually, a fast
        solver such as :class:`.CyEnvelope1D`.
    accelerators : list[Accelerator]
        First object is the reference linac; second object is the one we will
        break and fix.
    objective_factory_class : type[ObjectiveFactory] | None, optional
        If provided, will override the ``objective_preset``. Used to let user
        define it's own :class:`.ObjectiveFactory` without altering the source
        code.

    Returns
    -------
    list[FaultScenario]
        The instantiated fault scenarios.

    """
    beam_calculator.compute(accelerators[0])
    fault_scenarios = fault_scenario_factory(
        accelerators,
        beam_calculator,
        objective_factory_class=objective_factory_class,
        **config,
    )
    return fault_scenarios


def set_up(
    config: dict[str, dict[str, Any]],
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
    config : dict[str, dict[str, Any]]
        The full TOML configuration dictionary.

    Returns
    -------
    beam_calculators : tuple[BeamCalculator, ...]
        The objects to compute the beam. Typically, they are two: one for the
        optimization, and a second slower one to run a more precise simulation.
    accelerators : list[Accelerator]
        The objects that will store a linac design. Typically, they are two:
        one for the reference linac, and one for the broken/fixed linac.
     fault_scenarios : list[FaultScenario] | None
        The created failures. Will be None if no ``"wtf"`` entry was given in
        ``config``.
     ref_simulations_outputs : list[SimulationOutput]
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
     fault_scenarios : list[FaultScenario] | None
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
    beam_calculators : Collection[BeamCalculator]
        One or several beam calculators.
    references : Collection[SimulationOutput]
        A reference :class:`.SimulationOutput` per :class:`.BeamCalculator`,
        ideally generated by the same :class:`.BeamCalculator`.
    accelerators : Accelerator
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
    config : dict[str, Any]
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
