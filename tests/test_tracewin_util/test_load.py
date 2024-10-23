"""Test that the lines of the ``.dat`` are properly understood."""

import hashlib
from pathlib import Path
from pprint import pformat

import pytest

from lightwin.constants import example_dat
from lightwin.core.commands.adjust import Adjust
from lightwin.tracewin_utils.dat_files import dat_filecontent_from_file
from lightwin.tracewin_utils.line import DatLine


def are_equal(
    expected: dict[str, str | float | list[str]], returned: DatLine
) -> None:
    """Test that all arguments are the same."""
    for key, val in expected.items():
        assert val == (
            got := getattr(returned, key)
        ), f"{key} error: expected {val} but {got = }"


def check(line: str, expected: dict[str, str | float | list[str]]) -> None:
    """Instantiate and check."""
    dat_line = DatLine(line, idx=-1)
    return are_equal(expected, dat_line)


@pytest.mark.smoke
class TestDatLine:
    """Test functions to convert a ``.dat`` line to list of arguments."""

    def test_basic_line(self) -> None:
        """Test that a basic line is properly sliced."""
        line = "DRIFT 76"
        expected = {
            "personalized_name": None,
            "weight": None,
            "splitted": line.split(),
        }
        return check(line, expected)

    def test_line_with_more_arguments(self) -> None:
        line = "FIELD_MAP 100 5 0.9 0.7 54e4 3 65.6e10"
        expected = {
            "personalized_name": None,
            "weight": None,
            "splitted": line.split(),
        }
        return check(line, expected)

    def test_basic_comment(self) -> None:
        """Test that a basic comment is properly sliced."""
        line = ";DRIFT 76"
        expected = {
            "personalized_name": None,
            "weight": None,
            "splitted": [";", "DRIFT 76"],
        }
        return check(line, expected)

    def test_basic_comment_with_space(self) -> None:
        """Test that a basic comment is properly sliced."""
        line = "; DRIFT 76"
        expected = {
            "personalized_name": None,
            "weight": None,
            "splitted": [";", "DRIFT 76"],
        }
        return check(line, expected)

    def test_element_with_a_name(self) -> None:
        """Test that a named element is properly sliced."""
        line = "Louise: DRIFT 76"
        expected = {
            "personalized_name": "Louise",
            "weight": None,
            "splitted": ["DRIFT", "76"],
        }
        return check(line, expected)

    def test_element_with_a_name_additional_space(self) -> None:
        """Test that a named element is properly sliced."""
        line = "Michel : DRIFT 76"
        expected = {
            "personalized_name": "Michel",
            "weight": None,
            "splitted": ["DRIFT", "76"],
        }
        return check(line, expected)

    def test_element_with_an_underscored_name(self) -> None:
        """Test that a named element is properly sliced."""
        line = "Louise_Michel: DRIFT 76"
        expected = {
            "personalized_name": "Louise_Michel",
            "weight": None,
            "splitted": ["DRIFT", "76"],
        }
        return check(line, expected)

    def test_element_with_an_hyphenated_name(self) -> None:
        """Test that a named element is properly sliced."""
        line = "Louise-Michel: DRIFT 76"
        expected = {
            "personalized_name": "Louise-Michel",
            "weight": None,
            "splitted": ["DRIFT", "76"],
        }
        return check(line, expected)

    def test_diagnostic_with_a_weight(self) -> None:
        """Test that a weighted element is properly sliced."""
        line = "DIAG_BONJOURE(1e3) 777 0 1 2"
        expected = {
            "personalized_name": None,
            "weight": 1e3,
            "splitted": ["DIAG_BONJOURE", "777", "0", "1", "2"],
        }
        return check(line, expected)

    def test_diagnostic_with_a_weight_additional_space(self) -> None:
        """Test that a weighted element is properly sliced."""
        line = "DIAG_BONJOURE (1e3) 777 0 1 2"
        expected = {
            "personalized_name": None,
            "weight": 1e3,
            "splitted": ["DIAG_BONJOURE", "777", "0", "1", "2"],
        }
        return check(line, expected)

    def test_diagnostic_with_a_weight_different_fmt(self) -> None:
        """Test that a weighted element is properly sliced."""
        line = "DIAG_BONJOURE (4.5) 777 0 1 2"
        expected = {
            "personalized_name": None,
            "weight": 4.5,
            "splitted": ["DIAG_BONJOURE", "777", "0", "1", "2"],
        }
        return check(line, expected)

    def test_named_diagnostic_with_a_weight(self) -> None:
        """Test that a weighted element is properly sliced."""
        line = "Pichel: DIAG_BONJOURE(1e3) 777 0 1 2"
        expected = {
            "personalized_name": "Pichel",
            "weight": 1e3,
            "splitted": ["DIAG_BONJOURE", "777", "0", "1", "2"],
        }
        return check(line, expected)

    def test_named_diagnostic_with_a_weight_additional_space(self) -> None:
        """Test that a weighted element is properly sliced."""
        line = "Louise: DIAG_BONJOURE (1e3) 777 0 1 2"
        expected = {
            "personalized_name": "Louise",
            "weight": 1e3,
            "splitted": ["DIAG_BONJOURE", "777", "0", "1", "2"],
        }
        return check(line, expected)

    def test_multiple_semicommas(self) -> None:
        """Check that when we have several ;, only the first is kept."""
        line = ";;;;;;;; Section1: ;;;;;;;"
        expected = {
            "personalized_name": None,
            "weight": None,
            "splitted": [line[0], line[1:]],
        }
        return check(line, expected)

    def test_comment_at_end_of_line_is_removed(self) -> None:
        """Test that EOL comments are removed to avoid any clash."""
        line = "DRIFT 76 ; this drift is where we put the coffee machine"
        expected = {
            "personalized_name": None,
            "weight": None,
            "splitted": ["DRIFT", "76"],
        }
        return check(line, expected)

    def test_line_with_nothing_but_spaces(self) -> None:
        """Test that empty line is correctly understood."""
        line = "    "
        expected = {"personalized_name": None, "weight": None, "splitted": []}
        return check(line, expected)

    def test_windows_like_path(self) -> None:
        """Test that the : does not mess with the code."""
        line = "field_map_path C:\\path\\to\\field_maps\\"
        expected = {
            "personalized_name": None,
            "weight": None,
            "splitted": line.split(),
        }
        return check(line, expected)

    def test_end(self) -> None:
        """Test that the end is ok."""
        line = "END"
        expected = {
            "personalized_name": None,
            "weight": None,
            "splitted": [line],
        }
        return check(line, expected)


def md5(fname: Path | str) -> str:
    """Give checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


@pytest.mark.smoke
class TestLoadDatFile:
    """Ensure that the ``.dat`` file will be correctly loaded."""

    expected_checksum = "06d55c23082cedd0cc8f065dc04e608d"
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

    def test_file_was_not_changed(self) -> None:
        """Compare checksums to verify file is still the same.

        Otherwise, I may mess up with those tests.

        """
        actual_checksum = md5(example_dat)
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
