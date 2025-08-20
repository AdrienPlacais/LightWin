"""Define :class:`.KeyValConfSpec` tests."""

from lightwin.config.csv_formatter import chunk


def test_split_simple_line() -> None:
    """Test splitting with no difficulty."""
    text = "Bonjoure sa va"
    expected = ["Bonjoure", "sa va"]
    assert chunk(text, 8) == expected


def test_split_simple_line_hyphenation() -> None:
    """Test splitting with no difficulty."""
    text = "Bonjoure sa va"
    expected = ["Bon-", "jou-", "re", "sa", "va"]
    assert chunk(text, 4) == expected


def test_simple_backtick_line() -> None:
    """Test splitting a variable name."""
    text = "`key_val_conf_spec`"
    expected = ["`key_val_`", "`conf_spec`"]
    assert chunk(text, 9) == expected


def test_mixed_text_backtick() -> None:
    """Test normal text with a variable name.

    The variable name should not be splitted if it can fit on the next line.

    """
    text = "This is set by `GETTABLE_ELT`"
    expected = ["This is set", "by", "`GETTABLE_ELT`"]
    assert chunk(text, 12) == expected


def test_mixed_text_backtick_too_long() -> None:
    """Test normal text with a variable name.

    The variable name should be splitted if it cannot fit on the next line.

    """
    text = "This is set by `GETTABLE_ELT`"
    expected = ["This is", "set by", "`GETTABLE_`", "`ELT`"]
    assert chunk(text, 10) == expected


def test_rest_not_splitted() -> None:
    """Check that ReST roles are not splitted."""
    text = "Keyword arguments for the :class:`.SimulationOutputEvaluator`."
    expected = [
        "Keyword arguments for the",
        ":class:`.SimulationOutputEvaluator`.",
    ]
    assert chunk(text, 30) == expected


def test_keep_backticks_when_splitting() -> None:
    """Check that fixed width text keeps backticks when splitted."""
    text = (
        "Distance increase for downstream elements (`shift < 0`) or "
        "upstream elements (`shift > 0`). Used to have a window of "
        "compensating cavities which is not centered around the failed "
        "elements."
    )
    expected = [
        "Distance increase for",
        "downstream elements (`shift <`",
        "`0`) or upstream elements",
        "(`shift > 0`). Used to have a",
        "window of compensating",
        "cavities which is not centered",
        "around the failed elements.",
    ]
    assert chunk(text, 30) == expected
