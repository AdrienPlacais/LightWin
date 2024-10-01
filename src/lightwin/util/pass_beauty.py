"""Define utility functions to perform a "pass beauty".

After a LightWin optimisation, perform a second optimisation with TraceWin. As
for now, the implementation is kept very simple:

 - The phase of compensating cavities can be retuned at +/- ``tol_phi_deg``
   around their compensated value.
 - The amplitude of compensating cavities can be retuned at +/- ``tol_k_e``
   around their compensated value.
 - We try to keep the phase dispersion between start of compensation zone, and
   ``number_of_dsize`` lattices after.

.. warning::
    Performing a pass beauty will break the colors of the cavities in the
    output plots. They will all appear in green, as if they were nominal.

.. todo::
    fix colors in plots after pass beauty

"""

import logging
import math
from collections.abc import Collection

from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.beam_calculation.tracewin.tracewin import TraceWin
from lightwin.core.commands.adjust import Adjust
from lightwin.core.elements.diagnostic import DiagDSize3, Diagnostic
from lightwin.core.elements.element import Element
from lightwin.core.elements.field_maps.cavity_settings import CavitySettings
from lightwin.core.instruction import Instruction
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.failures.fault import Fault
from lightwin.failures.fault_scenario import FaultScenario
from lightwin.failures.helper import nested_containing_desired
from lightwin.failures.set_of_cavity_settings import SetOfCavitySettings
from lightwin.util.helper import flatten


def _cavity_settings_to_adjust(
    cavity_settings: CavitySettings,
    dat_idx: int,
    number: int,
    tol_phi_deg: float = 5,
    tol_k_e: float = 0.05,
    link_index: int = 0,
    phase_nature: str = "",
) -> tuple[Adjust, Adjust] | tuple[Adjust, Adjust, Adjust]:
    """Create a ADJUST command with small bounds around current value."""
    if not phase_nature:
        phase_nature = cavity_settings.reference
    assert (
        phase_nature != "phi_s"
    ), "Adjusting synchronous phase won't do with TraceWin."

    phase = getattr(cavity_settings, phase_nature)
    assert isinstance(phase, float)
    phase = math.degrees(phase)
    line_phi = (
        f"ADJUST {number} 3 0 {phase - tol_phi_deg} {phase + tol_phi_deg}"
    )

    k_e = cavity_settings.k_e
    line_k_e = (
        f"ADJUST {number} 5 {link_index} {k_e - tol_k_e} {k_e + tol_k_e}"
    )

    adjust_phi = Adjust(line_phi.split(), dat_idx)
    adjust_k_e = Adjust(line_k_e.split(), dat_idx)
    if not link_index:
        return adjust_phi, adjust_k_e
    line_k_g = f"ADJUST {number} 6 {link_index}"
    return adjust_phi, adjust_k_e, Adjust(line_k_g.split(), dat_idx)


def set_of_cavity_settings_to_adjust(
    set_of_cavity_settings: SetOfCavitySettings,
    number: int,
    tol_phi_deg: float = 5,
    link_k_g: bool = False,
    tol_k_e: float = 0.05,
    phase_nature: str = "phi_0_rel",
) -> list[Adjust]:
    """Create adjust commands for every compensating cavity."""
    commands = [
        _cavity_settings_to_adjust(
            cavity_settings,
            elt.idx["dat_idx"],
            number,
            link_index=i if link_k_g else 0,
            tol_phi_deg=tol_phi_deg,
            tol_k_e=tol_k_e,
            phase_nature=phase_nature,
        )
        for i, (elt, cavity_settings) in enumerate(
            set_of_cavity_settings.items(), start=1
        )
    ]
    return [x for x in flatten(commands)]


def elements_to_diagnostics(
    fix_elts: ListOfElements,
    compensating: Collection[Element],
    number: int,
    number_of_dsize: int,
) -> list[Diagnostic]:
    """Create the DSize3 commands that will be needed."""
    lattices = fix_elts.by_lattice
    compensating_lattices = nested_containing_desired(lattices, compensating)

    first_compensating, last_compensating = (
        compensating_lattices[0],
        compensating_lattices[-1],
    )
    assert isinstance(last_compensating, list)
    post_compensating = lattices[lattices.index(last_compensating) + 1 :]

    dzise_elements = (
        first_compensating[0],
        *[lattice[0] for lattice in post_compensating[:number_of_dsize]],
    )
    dsize_args = (
        (f"DIAG_DSIZE3 {number} 0 0".split(), elt.idx["dat_idx"])
        for elt in dzise_elements
    )
    dsizes = [DiagDSize3(*args) for args in dsize_args]
    return dsizes


def _pass_beauty_instructions(
    fault_scenario: FaultScenario,
    number_of_dsize: int,
    number: int = 666333,
    link_k_g: bool = True,
) -> list[Instruction]:
    """Perform a beauty pass."""
    if len(fault_scenario) > 1:
        raise NotImplementedError(
            "Not sure how multiple faults would interact."
        )
    fault: Fault = fault_scenario[0]
    fix_elts = fault_scenario.fix_acc.elts
    compensating = fault.compensating_elements

    diagnostics = elements_to_diagnostics(
        fix_elts,
        compensating,
        number=number,
        number_of_dsize=number_of_dsize,
    )

    adjusts = set_of_cavity_settings_to_adjust(
        fault.optimized_cavity_settings, number=number, link_k_g=link_k_g
    )
    if len(adjusts) < 2:
        logging.error(
            f"Not enough DIAG_DSIZE3 in {compensating = } for pass beauty."
        )
        return []
    out = sorted([*diagnostics, *adjusts], key=lambda x: x.idx["dat_idx"])
    return out


def insert_pass_beauty_instructions(
    fault_scenario: FaultScenario | Collection[FaultScenario],
    beam_calculator: BeamCalculator,
    number_of_dsize: int = 10,
    number: int = 666333,
    link_k_g: bool = True,
) -> None:
    """
    Overwrite :class:`.ListOfElements` to include pass beauty instructions.

    The ``fault_scenario.fix_acc.elts`` (a :class:`.ListOfElements`) will
    be overwritten.

    """
    if not isinstance(fault_scenarios := fault_scenario, FaultScenario):
        for fault_scenario in fault_scenarios:
            insert_pass_beauty_instructions(
                fault_scenario,
                beam_calculator,
                number_of_dsize=number_of_dsize,
                number=number,
                link_k_g=link_k_g,
            )
        return

    assert _is_adapted_to_pass_beauty(beam_calculator)
    assert isinstance(fault_scenario, FaultScenario)
    instructions = _pass_beauty_instructions(
        fault_scenario,
        number_of_dsize=number_of_dsize,
        number=number,
        link_k_g=link_k_g,
    )

    accelerator = fault_scenario.fix_acc
    elts = beam_calculator.list_of_elements_factory.from_existing_list(
        accelerator.elts,
        instructions_to_insert=instructions,
        append_stem="beauty",
        which_phase="phi_0_rel",
    )
    logging.info("Overwriting a ListOfElements by its beauty counterpart.")
    logging.warning(
        "Expected bug: all cavities will be shown as green in plots."
    )
    accelerator.elts = elts
    return


def _is_adapted_to_pass_beauty(
    beam_calculator: BeamCalculator,
) -> bool:
    """Check if the provided beam calculator can perform beauty pass."""
    if not isinstance(beam_calculator, TraceWin):
        logging.error("Beauty pass will only work with TraceWin.")
        return False

    if beam_calculator.base_kwargs.get("cancel_matching", False):
        logging.error("You shall specify `cancel_matching = False` in config.")
        return False

    if not beam_calculator.base_kwargs.get("cancel_matchingP", False):
        logging.warning(
            "Doing a Partran optimisation may take a very long time. Doing it "
            "anyway."
        )
        return True
    return True
