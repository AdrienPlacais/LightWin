"""Define utility functions to perform a "pass beauty".

After a LightWin optimisation, perform a second optimisation with TraceWin. As
for now, two different beauty passes:

1. Slightly retune cavities:

 - The phase of compensating cavities can be retuned at +/- ``tol_phi_deg``
   around their compensated value.
 - The amplitude of compensating cavities can be retuned at +/- ``tol_k_e``
   around their compensated value.
 - We try to keep the phase dispersion between start of compensation zone, and
   ``number_of_dsize`` lattices after.

2. Retune quadrupoles to match transverse envelopes.

.. warning::
    Performing a pass beauty will break the colors of the cavities in the
    output plots. They will all appear in green, as if they were nominal.

.. todo::
    fix colors in plots after pass beauty

"""

import logging
import math
from collections.abc import Collection, Mapping
from pprint import pformat

from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.beam_calculation.tracewin.tracewin import TraceWin
from lightwin.core.commands.adjust import (
    Adjust,
    AdjustSteerer,
    AdjustSteererBx,
    AdjustSteererBy,
)
from lightwin.core.commands.steerer import Steerer
from lightwin.core.elements.diagnostic import (
    DiagDSize2,
    DiagDSize3,
    DiagPosition,
)
from lightwin.core.elements.element import Element
from lightwin.core.elements.field_maps.cavity_settings import CavitySettings
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.elements.quad import Quad
from lightwin.core.instruction import Instruction
from lightwin.core.list_of_elements.helper import filter_elts
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.failures.fault_scenario import FaultScenario
from lightwin.failures.helper import nested_containing_desired
from lightwin.util.helper import flatten
from lightwin.util.typing import REFERENCE_PHASES_T


# =============================================================================
# Front end
# =============================================================================
def insert_field_map_pass_beauty_instructions(
    fault_scenario: FaultScenario | Collection[FaultScenario],
    beam_calculator: BeamCalculator,
    number_of_dsize: int = 10,
    number: int = 666333,
    link_k_g: bool = True,
) -> None:
    """Overwrite |LOE| to include pass beauty instructions.

    This pass beauty inserts ``DIAG_DSIZE3`` to uniformize envelopes over
    ``number_of_dsize`` periods.

    The ``fault_scenario.fix_acc.elts`` (a |LOE|) will be overwritten.


    Parameters
    ----------
    fault_scenario :
        One or several failure scenarios, each with only one |F|.
    beam_calculator :
        A solver accepting beauty pass. Typically, :class:`.TraceWin`.
    number_of_dsize :
        Number of :class:`.DiagDSize3` diagnostics.
    number :
        The ID of diags/adjusts.
    link_k_g :
        If ``k_g`` should also be fitted.

    """
    if not isinstance(fault_scenarios := fault_scenario, FaultScenario):
        for fault_scenario in fault_scenarios:
            insert_field_map_pass_beauty_instructions(
                fault_scenario,
                beam_calculator,
                number_of_dsize=number_of_dsize,
                number=number,
                link_k_g=link_k_g,
            )
        return

    assert _is_adapted_to_pass_beauty(beam_calculator)
    assert isinstance(fault_scenario, FaultScenario)
    instructions = _field_map_pass_beauty_instructions(
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


def insert_transverse_matching_instructions(
    fault_scenario: FaultScenario | Collection[FaultScenario],
    beam_calculator: BeamCalculator,
    retune_steerers: bool = True,
    retune_quadrupoles: bool = True,
    number: int = 666000,
) -> None:
    """Overwrite |LOE| to include pass beauty instructions.

    This pass beauty inserts ``DIAG_DSIZE2`` to retune quadrupoles, which
    LightWin cannot perform.

    The ``fault_scenario.fix_acc.elts`` (a |LOE|) will be overwritten.


    Parameters
    ----------
    fault_scenario :
        One or several failure scenarios, each with only one |F|.
    beam_calculator :
        A solver accepting beauty pass. Typically, :class:`.TraceWin`.
    retune_steerers :
        If steerers should be re-adjusted.
    retune_quadrupoles :
        If quadrupoles should be retuned to keep a clean envelope.
    number :
        The ID of diags/adjusts.

    """
    if not isinstance(fault_scenarios := fault_scenario, FaultScenario):
        for fault_scenario in fault_scenarios:
            insert_transverse_matching_instructions(
                fault_scenario,
                beam_calculator,
                number=number,
                retune_steerers=retune_steerers,
                retune_quadrupoles=retune_quadrupoles,
            )
        return

    if len(fault_scenario) > 1:
        raise NotImplementedError(
            "Not sure how multiple faults would interact."
        )
    assert _is_adapted_to_pass_beauty(beam_calculator)
    assert isinstance(fault_scenario, FaultScenario)

    instructions = _spiral2_transverse_matching_instructions(
        fault_scenario,
        number=number,
        retune_steerers=retune_steerers,
        retune_quadrupoles=retune_quadrupoles,
    )

    accelerator = fault_scenario.fix_acc
    elts = beam_calculator.list_of_elements_factory.from_existing_list(
        accelerator.elts,
        instructions_to_insert=instructions,
        append_stem="qp_retuning",
    )
    logging.info("Overwriting a ListOfElements by its beauty counterpart.")
    logging.warning(
        "Expected bug: all cavities will be shown as green in plots."
    )
    accelerator.elts = elts
    return


# =============================================================================
# Field map retuning
# =============================================================================
def _cavity_settings_to_adjust(
    cavity_settings: CavitySettings,
    dat_idx: int,
    number: int,
    tol_phi_deg: float = 5,
    tol_k_e: float = 0.05,
    link_index: int = 0,
    phase_nature: REFERENCE_PHASES_T | None = None,
) -> tuple[Adjust, Adjust] | tuple[Adjust, Adjust, Adjust]:
    """Create ``ADJUST`` commands with small bounds around current values.

    Adjust phase, ``k_e``, and ``k_g``1 if ``link_index`` is different from 0.

    Parameters
    ----------
    cavity_settings :
        Settings to re-adjust.
    dat_idx :
        Index in the ``DAT`` file.
    number :
        Number of the diagnostics this commands should be associated to.
    tol_phi_deg :
        Tolerance over original phase in degrees.
    tol_k_e :
        Tolerance over field amplitude.
    link_index :
        Link the ``k_e`` ``ADJUST`` with a ``k_g`` ``ADJUST``, if different
        from 0.
    phase_nature :
        Reference phase. Note that ``"phi_s"`` will raise an error, TraceWin
        does not allow optimisation with synchronous phase as variable.

    """
    if not phase_nature:
        phase_nature = cavity_settings.reference
    assert (
        phase_nature != "phi_s"
    ), "Adjusting synchronous phase won't do with TraceWin."

    phase = getattr(cavity_settings, phase_nature)
    assert isinstance(phase, float)
    phase = math.degrees(phase)
    adjust_phi = Adjust.from_args(
        dat_idx,
        number,
        vth_variable=3,
        n_link=0,
        mini=phase - tol_phi_deg,
        maxi=phase + tol_phi_deg,
    )

    k_e = cavity_settings.k_e
    adjust_k_e = Adjust.from_args(
        dat_idx=dat_idx,
        number=number,
        vth_variable=5,
        n_link=link_index,
        mini=k_e - tol_k_e,
        maxi=k_e + tol_k_e,
    )

    if not link_index:
        return adjust_phi, adjust_k_e
    adjust_k_g = Adjust.from_args(
        dat_idx, number, vth_variable=6, n_link=link_index
    )
    return adjust_phi, adjust_k_e, adjust_k_g


def _set_of_cavity_settings_to_adjust(
    compensation_settings: Mapping[FieldMap, CavitySettings],
    number: int,
    tol_phi_deg: float = 5,
    link_k_g: bool = False,
    tol_k_e: float = 0.05,
    phase_nature: REFERENCE_PHASES_T = "phi_0_rel",
) -> list[Adjust]:
    """Create adjust commands for every compensating cavity.

    Parameters
    ----------
    compensation_settings :
        Maps cavities to their compensated settings.
    number :
        ID number of the diagnostics that should be associated with the
        ``ADJUST``s.
    tol_phi_deg :
        Tolerance over original phase in degrees.
    link_k_g :
        If ``k_g`` values should follow ``k_e``.
    tol_k_e :
        Tolerance over field amplitude.
    phase_nature :
        Reference phase. Note that ``"phi_s"`` will raise an error, TraceWin
        does not allow optimisation with synchronous phase as variable.

    """
    nested_commands = [
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
            compensation_settings.items(), start=1
        )
    ]
    flattened: list[Adjust]
    flattened = [x for x in flatten(nested_commands)]
    return flattened


def _dsize3_diagnostics(
    fix_elts: ListOfElements,
    compensating: Collection[Element],
    number: int,
    number_of_dsize: int,
) -> list[DiagDSize3]:
    """Create the DSize3 commands that will be needed.

    Create on diagnostic per lattice, over ``number_of_dsize`` lattices. The
    first one will be at the first compensating lattice.

    Parameters
    ----------
    fix_elts :
        Contains elements fixed with LightWin, to be retuned by TraceWin.
    compensating :
        Compensating elements that TraceWin should retune.
    number :
        ID number of the diagnostics to create.
    number_of_dsize :
        Number of diagnostics to create.

    Returns
    -------
        One :class:`.DiagDSize3` per lattice.

    """
    lattices = fix_elts.by_lattice
    compensating_lattices = nested_containing_desired(lattices, compensating)

    first_compensating, last_compensating = (
        compensating_lattices[0],
        compensating_lattices[-1],
    )
    assert isinstance(last_compensating, list)
    post_compensating = lattices[lattices.index(last_compensating) + 1 :]

    dsize_elements = (
        first_compensating[0],
        *[lattice[0] for lattice in post_compensating[:number_of_dsize]],
    )
    dsizes = [
        DiagDSize3.from_args(elt.idx["dat_idx"], number=number)
        for elt in dsize_elements
    ]
    return dsizes


def _field_map_pass_beauty_instructions(
    fault_scenario: FaultScenario,
    number_of_dsize: int,
    number: int = 666333,
    link_k_g: bool = True,
) -> list[Instruction]:
    """Create diagnostics and adjust commands.

    Parameters
    ----------
    fault_scenario :
        Scenario under study. Should contain only one failure.
    number_of_dsize :
        Number of diagnostics to use (one diagnostic per lattice will be used).
    number :
        ID number of the diagnostics and adjusts.
    link_k_g :
        If ``k_g`` values should follow ``k_e``.

    Returns
    -------
        All diagnostic and adjust commands.

    """
    if len(fault_scenario) > 1:
        raise NotImplementedError(
            "Not sure how multiple faults would interact."
        )
    fault = fault_scenario[0]
    fix_elts = fault_scenario.fix_acc.elts
    compensating = fault.compensating_elements

    diagnostics = _dsize3_diagnostics(
        fix_elts,
        compensating,
        number=number,
        number_of_dsize=number_of_dsize,
    )

    adjusts = _set_of_cavity_settings_to_adjust(
        fault.compensation_settings, number=number, link_k_g=link_k_g
    )
    if len(adjusts) < 2:
        logging.error(
            f"Not enough DIAG_DSIZE3 in {compensating = } for pass beauty."
        )
        return []
    out = sorted([*diagnostics, *adjusts], key=lambda x: x.idx["dat_idx"])
    return out


# =============================================================================
# Quadrupole retuning
# =============================================================================
def _spiral2_transverse_matching_instructions(
    fault_scenario: FaultScenario,
    number: int = 666000,
    retune_steerers: bool = True,
    retune_quadrupoles: bool = True,
) -> list[Instruction]:
    """Create commands for transverse rematching."""
    fault = fault_scenario[0]
    fix_elts = fault_scenario.fix_acc.elts
    altered = fault.compensating_elements + fault.failed_elements
    altered_lattices_idx = set(sorted([elt.idx["lattice"] for elt in altered]))
    altered_lattices = [fix_elts.by_lattice[i] for i in altered_lattices_idx]

    steerers_diags, steerers_adjusts = (), ()
    if retune_steerers:
        steerers_quadrupoles = _get_steerers_and_qps(
            fix_elts, altered_lattices_idx
        )
        steerers_adjusts = _steerer_adjust_commands(
            steerers_quadrupoles, number=number + 100
        )
        steerers_diags = _steerer_diag_commands(
            by_lattice=fix_elts.by_lattice,
            adjust_steerers=steerers_adjusts,
            number=number + 100,
        )

    qp_diagnostics, qp_adjusts = (), ()
    if retune_quadrupoles:
        compensating_quadrupoles = _spiral2_quadrupoles(altered_lattices)
        diag_quadrupoles = compensating_quadrupoles[1::3]
        qp_diagnostics = _dsize2_diagnostics(
            diag_quadrupoles=diag_quadrupoles, number=number
        )
        qp_adjusts = _quadrupole_adjust_commands(
            compensating_quadrupoles=compensating_quadrupoles, number=number
        )
        if len(qp_adjusts) < 2:
            logging.error("Not enough DIAG_DSIZE2 for pass beauty.")
            return []

    instructions = sorted(
        [*steerers_adjusts, *steerers_diags, *qp_diagnostics, *qp_adjusts],
        key=lambda x: x.idx["dat_idx"],
    )
    return instructions


def _spiral2_quadrupoles(lattices: list[list[Element]]) -> list[Quad]:
    """Get QP from SPIRAL2 linac, check structure.

    We expect, in each lattice:
    - two identical defocusing quadrupoles of length 65mm, directly after each
      other
    - one focusing quadrupole of length 130mm
    We insert the diags between the two identical defoc.

    """
    quadrupoles = [
        x for lattice in lattices for x in lattice if isinstance(x, Quad)
    ]
    assert len(quadrupoles) % 3 == 0
    qp1 = quadrupoles[::3]
    qp2 = quadrupoles[1::3]
    qp3 = quadrupoles[2::3]
    for q1, q2, q3 in zip(qp1, qp2, qp3, strict=True):
        assert q1.grad < 0.0
        assert q1.length_m == 65e-3
        assert q2.grad < 0.0
        assert q2.length_m == 65e-3
        assert q3.grad > 0.0
        assert q3.length_m == 130e-3
    return quadrupoles


def _get_steerers_and_qps(
    elts: ListOfElements, altered_lattices_idx: Collection[int]
) -> dict[Steerer, Quad]:
    """Get all steerers after first alteration, as well as associated qps."""
    steerers_quadrupoles: dict[Steerer, Quad] = {}
    first_altered = min(altered_lattices_idx)
    # We remove two lattices:
    # - exit of linac
    # - last "real" lattice because the DIAG must be one lattice after
    lattices_after_first_alteration = elts.by_lattice[first_altered:-2]

    for lattice in lattices_after_first_alteration:
        quadrupoles = filter_elts(lattice, Quad)

        for qp in quadrupoles:
            steerers = filter_elts(qp.influencing_instructions, Steerer)
            for steerer in steerers:
                steerers_quadrupoles[steerer] = qp
    return steerers_quadrupoles


def _steerer_adjust_commands(
    steerers_quadrupoles: Mapping[Steerer, Quad], number: int
) -> list[AdjustSteerer]:
    """Create adjust steerer commands."""
    adjust_steerers: list[AdjustSteerer] = []

    for st, qp in steerers_quadrupoles.items():
        if qp.grad < 0.0:
            cls = AdjustSteererBx
        else:
            cls = AdjustSteererBy

        adjust = cls.from_args(
            st.idx["dat_idx"],
            number=number + qp.idx["lattice"],
            mini=0,
            maxi=0,
            first_step=0.25,
        )
        adjust_steerers.append(adjust)
    return adjust_steerers


def _steerer_diag_commands(
    by_lattice: list[list[Element]],
    adjust_steerers: list[AdjustSteerer],
    number: int,
) -> list[DiagPosition]:
    """Add a diag in the middle of first QP, in the lattice following
    steerers."""
    diagnostics: list[DiagPosition] = []

    for adjust in adjust_steerers:
        if isinstance(adjust, AdjustSteererBy):
            continue
        next_lattice_idx = adjust.number - number + 1
        if next_lattice_idx + 1 >= len(by_lattice):
            continue
        next_lattice = by_lattice[next_lattice_idx]
        qps = filter_elts(next_lattice, Quad)
        if len(qps) != 3:
            continue

        if next_lattice_idx <= 12:
            name = "LINA-BPM"
        else:
            name = "LINB-BPM"
            next_lattice_idx -= 12
        name = f"{name}{next_lattice_idx+1:02}1"
        diag = DiagPosition.from_args(
            dat_idx=qps[1].idx["dat_idx"],
            number=adjust.number,
            x_pos=0,
            y_pos=0,
            accuracy=0.25,
            personalized_name=name,
        )
        diagnostics.append(diag)
    logging.critical(pformat(diagnostics))
    return diagnostics


def _dsize2_diagnostics(
    diag_quadrupoles: list[Quad], number: int
) -> list[DiagDSize2]:
    """Create the proper diagnostics.

    Adapted to SPIRAL2.

    """
    dsizes = [
        DiagDSize2.from_args(
            qp.idx["dat_idx"],
            number=number,
            x_rms_beam_delta_size=0,
            y_rms_beam_delta_size=0,
            accuracy=0.2,
        )
        for qp in diag_quadrupoles
    ]
    return dsizes


def _quadrupole_adjust_commands(
    compensating_quadrupoles: list[Quad], number: int
) -> list[Adjust]:
    """Create adjust commands for spiral2 quadrupoles.

    We link the gradient of the quadrupoles 0 and 1, 3 and 4, 6 and 7, etc.

    """
    qp1 = compensating_quadrupoles[::3]
    qp2 = compensating_quadrupoles[1::3]
    qp3 = compensating_quadrupoles[2::3]

    adjusts = []
    for i, (q1, q2, q3) in enumerate(zip(qp1, qp2, qp3, strict=True), start=1):
        adjusts += [
            Adjust.from_args(
                dat_idx=q1.idx["dat_idx"],
                number=number,
                vth_variable=2,
                n_link=i,
            ),
            Adjust.from_args(
                dat_idx=q2.idx["dat_idx"],
                number=number,
                vth_variable=2,
                n_link=i,
            ),
            Adjust.from_args(
                dat_idx=q3.idx["dat_idx"],
                number=number,
                vth_variable=2,
                n_link=0,
            ),
        ]
    return adjusts


# =============================================================================
# Generic
# =============================================================================
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
            "Doing a Partran optimisation may take a very long time. Doing it anyway."
        )
        return True
    return True
