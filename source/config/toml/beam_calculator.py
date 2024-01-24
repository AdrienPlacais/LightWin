#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Define the functions to test the :class:`.BeamCalculator` arguments."""
import logging
from pathlib import Path

from config.toml.helper import check_type


IMPLEMENTED_BEAM_CALCULATORS = ('Envelope1D', 'TraceWin', 'Envelope3D')  #:
IMPLEMENTED_ENVELOPE1D_METHODS = ('leapfrog', 'RK')  #:
IMPLEMENTED_ENVELOPE3D_METHODS = ('RK', )  #:

TRACEWIN_EXECUTABLES = {  # Should match with your installation
    "X11 full": Path("/", "usr", "local", "bin", "TraceWin", "./TraceWin"),
    "noX11 full": Path("/", "usr", "local", "bin", "TraceWin",
                       "./TraceWin_noX11"),
    "noX11 minimal": Path("/", "home", "placais", "TraceWin", "exe",
                          "./tracelx64"),
    "no run": None
}
simulation_types = tuple(TRACEWIN_EXECUTABLES.keys())  #:


def test(tool: str,
         **beam_calculator_kw: bool | str | int) -> None:
    """
    Ensure that selected :class:`.BeamCalculator` will be properly initialized.
    """
    assert tool in IMPLEMENTED_BEAM_CALCULATORS
    specific_tester = {'Envelope1D': _test_envelope1d,
                       'TraceWin': _test_tracewin,
                       'Envelope3D': _test_envelope3d,
                       }
    specific_tester[tool](**beam_calculator_kw)


def edit_configuration_dict_in_place(beam_calculator_kw: dict) -> None:
    """Precompute some useful values, transform some ``str`` into ``Path``."""
    tool = beam_calculator_kw['tool']
    specific_editer_configuration_dict_in_place = {
        'Envelope1D': _edit_configuration_dict_in_place_envelope1d,
        'TraceWin': _edit_configuration_dict_in_place_tracewin,
        'Envelope3D': _edit_configuration_dict_in_place_envelope3d,
    }
    specific_editer_configuration_dict_in_place[tool](beam_calculator_kw)


# Comment with recommended values: leapfrog 40 and RK 20
def _test_envelope1d(method: str,
                     flag_cython: bool,
                     flag_phi_abs: bool,
                     n_steps_per_cell: int,
                     **beam_calculator_kw: bool | str | int) -> None:
    """Test the consistency for the basic :class:`.Envelope1D` beam calculator.
    """
    assert method in IMPLEMENTED_ENVELOPE1D_METHODS
    check_type(bool, "beam_calculator", flag_cython, flag_phi_abs)
    check_type(int, "beam_calculator", n_steps_per_cell)


def _edit_configuration_dict_in_place_envelope1d(beam_calculator_kw: dict
                                                 ) -> None:
    """Modify the kw dict inplace."""
    pass


def _test_tracewin(simulation_type: str,
                   ini_path: str,
                   cal_file: str | None = None,
                   synoptic_file: str | None = None,
                   partran: int | None = None,
                   toutatis: int | None = None,
                   **beam_calculator_kw) -> None:
    """Test consistency for :class:`.TraceWin` beam calculator."""
    check_type(str, "beam_calculator", simulation_type, ini_path)
    assert Path(ini_path).is_file()
    assert simulation_type in TRACEWIN_EXECUTABLES

    if cal_file is not None:
        assert Path(cal_file).is_file()

    if synoptic_file is not None:
        logging.error("Synoptic file not implemented as I am not sure how this"
                      "should work.")
    for val in (partran, toutatis):
        if val is not None:
            assert val in (0, 1)

    for key in beam_calculator_kw.keys():
        if "Ele" in key:
            logging.error("Are you trying to use the Ele[n][v] key? Please "
                          "directly modify your `.dat` to avoid clash with "
                          "LightWin.")


def _edit_configuration_dict_in_place_tracewin(beam_calculator_kw: dict
                                               ) -> None:
    """Transform some values."""
    beam_calculator_kw['tw_exe'] = TRACEWIN_EXECUTABLES[
        beam_calculator_kw['simulation_type']]

    paths = ('executable', 'ini_path', 'cal_file', 'tab_file',
             'dst_file1', 'dst_file2')
    for path in paths:
        if path not in beam_calculator_kw:
            continue
        beam_calculator_kw[path] = Path(beam_calculator_kw[path])


def _test_envelope3d(method: str,
                     flag_phi_abs: bool,
                     n_steps_per_cell: int,
                     flag_cython: bool | None = None,
                     **beam_calculator_kw: bool | str | int) -> None:
    """Check validity of arguments for :class:`.Envelope3D`."""
    assert method in IMPLEMENTED_ENVELOPE3D_METHODS
    check_type(bool, "beam_calculator", flag_phi_abs)
    check_type(int, "beam_calculator", n_steps_per_cell)

    if flag_cython is not None:
        logging.warning("Cython not implemented yet for Envelope3D.")


def _edit_configuration_dict_in_place_envelope3d(beam_calculator_kw: dict
                                                 ) -> None:
    """Modify the kw dict inplace."""
    pass
