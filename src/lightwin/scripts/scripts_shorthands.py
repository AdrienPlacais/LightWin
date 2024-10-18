"""Define several helper functions.

.. todo::
    Should they be in a module somewhere?

"""

from collections.abc import Collection
from typing import Any

from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.core.accelerator.factory import NoFault


def compute_beam(
    beam_calculator: BeamCalculator,
    config: dict[str, dict[str, Any]],
) -> tuple[Accelerator, SimulationOutput]:
    """Create the :class:`.Accelerator` and compute beam in it.

    Parameters
    ----------
    beam_calculator : BeamCalculator
        Solver to use.
    config : dict[str, dict[str, Any]]
        Full configuration dictionary.

    Returns
    -------
    Accelerator
        An accelerator with its :class:`.SimulationOutput`.

    """
    accelerator_factory = NoFault(beam_calculators=beam_calculator, **config)
    accelerator = accelerator_factory.run()
    simulation_output = beam_calculator.compute(accelerator)
    return accelerator, simulation_output


def compute_beams(
    beam_calculators: Collection[BeamCalculator], config_files: dict[str, Any]
) -> tuple[list[Accelerator], list[SimulationOutput]]:
    """Propagate beam with all :class:`.BeamCalculator`."""
    accelerators, simulation_outputs = zip(
        *(
            compute_beam(beam_calculator, config_files)
            for beam_calculator in beam_calculators
        )
    )
    return accelerators, simulation_outputs
