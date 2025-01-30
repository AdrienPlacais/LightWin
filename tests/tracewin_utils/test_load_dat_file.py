"""Test that complete ``DAT`` files are properly understood."""

import hashlib
from importlib import resources
from pathlib import Path
from pprint import pformat

import pytest

from lightwin.constants import example_dat
from lightwin.core.commands.adjust import Adjust
from lightwin.tracewin_utils.dat_files import dat_filecontent_from_file
from lightwin.tracewin_utils.line import DatLine


def sha256(fname: Path) -> str:
    """Give SHA-256 checksum of a file."""
    hash_sha256 = hashlib.sha256()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


@pytest.mark.smoke
class TestLoadDatFile:
    """Ensure that the ``.dat`` file will be correctly loaded."""

    expected_checksum = (
        "e6053120d80b36a9f1d2c1f5f238bf313deefb87e5815516c2563f83a80ccbfa"
    )
    lines = [
        "FIELD_MAP_PATH field_maps_1D",
        "LATTICE 10 0",
        "FREQ 352.2",
        "QUAD 200 5.66763 100 0 0 0 0 0 0",
        "DRIFT 150 100 0 0 0",
        "QUAD 200 -5.67474 100 0 0 0 0 0 0",
        "DRIFT 150 100 0 0 0",
        "DRIFT 589.42 30 0 0 0",
        "FIELD_MAP 100 415.16 153.171 30 0 1.55425 0 0 Simple_Spoke_1D 0",
        "DRIFT 264.84 30 0 0 0",
        "FIELD_MAP 100 415.16 156.892 30 0 1.55425 0 0 Simple_Spoke_1D 0",
        "DRIFT 505.42 30 0 0 0",
        "DRIFT 150 100 0 0 0",
        "QUAD 200 5.77341 100 0 0 0 0 0 0",
        "DRIFT 150 100 0 0 0",
    ]
    idx_fm1 = 8
    idx_fm2 = 10
    line_adj_phase = "ADJUST 42 3 1 -180 180"
    line_adj_ampl = "ADJUST 42 6 1 0 1.60"

    @property
    def expected_dat_filecontent(self) -> list[DatLine]:
        expected_dat_filecontent = [
            DatLine(line, i) for i, line in enumerate(self.lines)
        ]
        return expected_dat_filecontent

    @pytest.mark.tmp
    def test_file_was_not_changed(self) -> None:
        """Compare checksums to verify file is still the same.

        Otherwise, I may mess up with those tests.

        """
        with resources.as_file(example_dat) as path:
            actual_checksum = sha256(path)
        assert actual_checksum == self.expected_checksum, (
            f"The checksum of {example_dat} does not match the expected one."
            " Maybe the file was edited?"
        )

    def test_some_lines_of_the_dat(self) -> None:
        """Check one some lines that the loading is correct."""
        actual_dat_filecontent = dat_filecontent_from_file(
            # "splitted": ["DRIFT", "76"]}
            example_dat,
            keep="none",
        )
        expected_dat_filecontent = self.expected_dat_filecontent
        assert expected_dat_filecontent == actual_dat_filecontent[:15], (
            f"Expected:\n{pformat(expected_dat_filecontent, width=120)}\nbut "
            f"returned:\n{pformat(actual_dat_filecontent[:15], width=120)}"
        )

    def test_insert_instruction(self) -> None:
        """Check that an instruction will be inserted at the proper place."""
        line_1 = DatLine(self.line_adj_phase, self.idx_fm1)
        instruction_1 = Adjust(line_1)

        expected_dat_filecontent = self.expected_dat_filecontent[:-1]
        expected_dat_filecontent.insert(self.idx_fm1, line_1)

        actual_dat_filecontent = dat_filecontent_from_file(
            example_dat, instructions_to_insert=(instruction_1,), keep="none"
        )
        assert expected_dat_filecontent == actual_dat_filecontent[:15], (
            f"Expected:\n{pformat(expected_dat_filecontent, width=120)}\nbut "
            f"returned:\n{pformat(actual_dat_filecontent[:15], width=120)}"
        )

    def test_insert_instructions(self) -> None:
        """Check that several instructions will work together."""
        line_1 = DatLine(self.line_adj_phase, self.idx_fm1)
        line_2 = DatLine(self.line_adj_ampl, self.idx_fm1)
        line_3 = DatLine(self.line_adj_phase, self.idx_fm2)
        line_4 = DatLine(self.line_adj_ampl, self.idx_fm2)

        instructions = (line_1, line_2, line_3, line_4)
        expected_dat_filecontent = self.expected_dat_filecontent[:-4]
        expected_dat_filecontent.insert(self.idx_fm1, line_1)
        expected_dat_filecontent.insert(self.idx_fm1 + 1, line_2)
        expected_dat_filecontent.insert(self.idx_fm2 + 2, line_3)
        expected_dat_filecontent.insert(self.idx_fm2 + 3, line_4)

        actual_dat_filecontent = dat_filecontent_from_file(
            example_dat, instructions_to_insert=instructions, keep="none"
        )
        assert expected_dat_filecontent == actual_dat_filecontent[:15], (
            f"Expected:\n{pformat(expected_dat_filecontent, width=120)}\nbut "
            f"returned:\n{pformat(actual_dat_filecontent[:15], width=120)}"
        )
