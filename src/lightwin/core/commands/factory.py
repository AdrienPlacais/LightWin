"""Define a class to easily create :class:`.Command` objects.

.. todo::
    handle personalized name of commands (marker)

"""

from pathlib import Path
from typing import Any

from lightwin.core.commands.adjust import Adjust
from lightwin.core.commands.chopper import Chopper
from lightwin.core.commands.command import Command
from lightwin.core.commands.dummy_command import DummyCommand
from lightwin.core.commands.end import End
from lightwin.core.commands.error import (
    ErrorBeamDyn,
    ErrorBeamStat,
    ErrorBendCPLDyn,
    ErrorBendCPLStat,
    ErrorBendNCPLDyn,
    ErrorBendNCPLStat,
    ErrorCavCPLDyn,
    ErrorCavCPLStat,
    ErrorCavNCPLDyn,
    ErrorCavNCPLStat,
    ErrorCavNCPLStatFile,
    ErrorGaussianCutOff,
    ErrorQuadNCPLDyn,
    ErrorQuadNCPLStat,
    ErrorRFQCelNCPLDyn,
    ErrorRFQCelNCPLStat,
    ErrorSetRatio,
    ErrorStatFile,
)
from lightwin.core.commands.field_map_path import FieldMapPath
from lightwin.core.commands.freq import Freq
from lightwin.core.commands.lattice import Lattice, LatticeEnd
from lightwin.core.commands.marker import Marker
from lightwin.core.commands.repeat_ele import RepeatEle
from lightwin.core.commands.set_adv import SetAdv
from lightwin.core.commands.set_sync_phase import SetSyncPhase
from lightwin.core.commands.shift import Shift
from lightwin.core.commands.steerer import Steerer
from lightwin.core.commands.superpose_map import SuperposeMap
from lightwin.tracewin_utils.line import DatLine

IMPLEMENTED_COMMANDS = {
    "ADJUST": Adjust,
    "ADJUST_STEERER": DummyCommand,
    "DUMMY_COMMAND": DummyCommand,
    "CHOPPER": Chopper,
    "END": End,
    "ERROR_BEAM_DYN": ErrorBeamDyn,
    "ERROR_BEAM_STAT": ErrorBeamStat,
    "ERROR_BEND_CPL_DYN": ErrorBendCPLDyn,
    "ERROR_BEND_CPL_STAT": ErrorBendCPLStat,
    "ERROR_BEND_NCPL_DYN": ErrorBendNCPLDyn,
    "ERROR_BEND_NCPL_STAT": ErrorBendNCPLStat,
    "ERROR_CAV_CPL_DYN": ErrorCavCPLDyn,
    "ERROR_CAV_CPL_STAT": ErrorCavCPLStat,
    "ERROR_CAV_NCPL_DYN": ErrorCavNCPLDyn,
    "ERROR_CAV_NCPL_STAT": ErrorCavNCPLStat,
    "ERROR_CAV_NCPL_STAT_FILE": ErrorCavNCPLStatFile,
    "ERROR_GAUSSIAN_CUT_OFF": ErrorGaussianCutOff,
    "ERROR_QUAD_NCPL_DYN": ErrorQuadNCPLDyn,
    "ERROR_QUAD_NCPL_STAT": ErrorQuadNCPLStat,
    "ERROR_RFQ_CEL_NCPL_DYN": ErrorRFQCelNCPLDyn,
    "ERROR_RFQ_CEL_NCPL_STAT": ErrorRFQCelNCPLStat,
    "ERROR_STAT_FILE": ErrorStatFile,
    "ERROR_SET_RATIO": ErrorSetRatio,
    "FIELD_MAP_PATH": FieldMapPath,
    "FREQ": Freq,
    "LATTICE": Lattice,
    "LATTICE_END": LatticeEnd,
    "MARKER": Marker,
    "PLOT_DST": DummyCommand,
    "REPEAT_ELE": RepeatEle,
    "SET_ADV": SetAdv,
    "SET_SYNC_PHASE": SetSyncPhase,
    "SHIFT": Shift,
    "STEERER": Steerer,
    "SUPERPOSE_MAP": SuperposeMap,
}  #:


class CommandFactory:
    """An object to create :class:`.Command` objects."""

    def __init__(
        self, default_field_map_folder: Path, **factory_kw: Any
    ) -> None:
        """Do nothing for now.

        .. todo::
            Check if it would be relatable to hold some arguments? As for now,
            I would be better off with a run function instead of a class.

        """
        self.default_field_map_folder = default_field_map_folder
        return

    def run(
        self, line: DatLine, dat_idx: int | None = None, **command_kw
    ) -> Command:
        """Call proper constructor."""
        command_creator = IMPLEMENTED_COMMANDS[line.instruction]
        command = command_creator(
            line,
            dat_idx,
            default_field_map_folder=self.default_field_map_folder,
            name=line.personalized_name,
            **command_kw,
        )
        return command
