"""Define helper functions to set up LightWin workflow."""

import logging
from collections.abc import Collection
from pprint import pformat
from typing import Any

from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.beam_calculation.factory import BeamCalculatorsFactory
from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.core.accelerator.factory import NoFault, WithFaults
from lightwin.core.list_of_elements.list_of_elements import (
    NESTED_ELEMENTS_ID,
    ListOfElements,
)
from lightwin.failures.fault_scenario import (
    FaultScenario,
    FaultScenarioFactory,
)
from lightwin.optimisation.objective.factory import ObjectiveFactory
from lightwin.util.helper import flatten
from lightwin.util.typing import AUTOMATIC_STUDY_T, ID_NATURE_T, BeamKwargs
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
    if "wtf" not in config:
        factory = NoFault(beam_calculators=beam_calculators[0], **config)
        accelerator = factory.run()
        return [accelerator]

    # =========================================================================
    # Dirty patch for automatic studies
    # =========================================================================
    if "automatic_study" in config["wtf"]:
        # Create a useless Accelerator just to get its ListOfElements
        factory = NoFault(beam_calculators=beam_calculators[0], **config)
        accelerator = factory.run()

        # Edit `wtf` dict with number of cavities stored in the desired
        # lattices/sections
        config["wtf"] = _edit_wtf_dict_for_automatic_studies(
            accelerator.elts, config["wtf"]
        )

    factory = WithFaults(beam_calculators=beam_calculators, **config)
    accelerators = factory.run_all()
    return accelerators


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
        The full TOML configuration dict.
    beam_calculator :
        The object that will be used for the optimization. Usually, a fast
        solver such as :class:`.CyEnvelope1D`.
    accelerators :
        First object is the reference linac; second object is the one we will
        break and fix.
    objective_factory_class :
        If provided, will override the ``objective_preset``. Used to let user
        define it's own :class:`.ObjectiveFactory` without altering the source
        code.

    Returns
    -------
        The instantiated fault scenarios.

    """
    beam_calculator.compute(accelerators[0])
    design_space = config.get("design_space")
    factory = FaultScenarioFactory(
        accelerators,
        beam_calculator,
        design_space,
        objective_factory_class=objective_factory_class,
    )
    wtf = config.get("wtf")
    return factory.create(**wtf)


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


def _edit_wtf_dict_for_automatic_studies(
    elts: ListOfElements, wtf: dict[str, Any]
) -> dict[str, Any]:
    """Fix the `wtf` dictionary when an automatic study is asked.

    This is a temporary patch; it is mandatory because of a design issue:

    - :class:`.AcceleratorFactory` needs to know the number of failures to
      create the proper number of :class:`.Accelerator`.
    - We need :class:`.Accelerator` (or, more precisely,
      :class:`.ListOfElements`) to know the number of cavities in a given
      section/lattice and thus the number of failures.

    .. note::
       ``automatic_study`` doc to put somewhere

        Automatically generate the list of failed cavities to avoid manually
        typing all the cavities identifiers in systematic studies.

        - ``"single cavity failures"``: study all single cavity failures among
        ``failed_cavities``. ``failed_cavities`` must be a list of elements.
        It is best used with something like:

        - ``failed = [1, 3, 7]``
        - ``id_nature = "lattice"``

        All the single cavity failures of lattices 1, 3 and 7 will be
        studied. Also works very well with ``id_nature = "section"``.

    """
    id_nature: ID_NATURE_T = wtf.get("id_nature")
    failed: NESTED_ELEMENTS_ID | list[NESTED_ELEMENTS_ID] = wtf.get("failed")
    automatic_study: AUTOMATIC_STUDY_T | None = wtf.get(
        "automatic_study", None
    )

    if automatic_study is None:
        return wtf

    if automatic_study != "single cavity failures":
        raise ValueError(
            f"You set {automatic_study = } but the only value that is accepted"
            " is 'single cavity failures'."
        )

    if id_nature not in ("section", "lattice"):
        logging.error(
            f"{id_nature = }, but 'lattice' or 'section' is expected "
            f"for {automatic_study = }."
        )

    lattices_or_sections = elts.take(failed, id_nature)
    failed_cavities = [
        x for x in flatten(lattices_or_sections) if x.can_be_retuned
    ]
    failed_names = [cav.name for cav in flatten(failed_cavities)]

    logging.critical(
        "Experimental feature: automatic study. Studying all single "
        f"cavity failures in {id_nature} of index(es) {failed}. "
        f"List of failed cavities: {pformat(failed_names)}"
    )
    wtf["id_nature"] = "name"
    wtf["failed"] = [[x] for x in failed_names]
    return wtf


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
