"""Test that the lines of the ``.dat`` are properly understood."""

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
