#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Define functions to test the optimisatio problem design space config.

.. todo::
    I do not like the fact that some ``design_space_kw`` values are defined
    twice... I could move the default values to the initialisation of the
    DesignSpace object maybe. Eventually, everything from this script will be
    moved to the object instantiation anyway.

"""
import logging
from pathlib import Path
from typing import Any

from config.toml.helper import check_type


IMPLEMENTED_DESIGN_SPACE_PRESETS = ('unconstrained',
                                    'constrained_sync_phase',
                                    'sync_phase_as_variable',
                                    'FM4_MYRRHA',
                                    'experimental',
                                    'everything',
                                    )


def test(from_file: bool,
         design_space_preset: str,
         **design_space_kw: str | float | bool | int | list) -> None:
    """Ensure that optimisation algorithm will initalize properly."""
    if design_space_preset not in IMPLEMENTED_DESIGN_SPACE_PRESETS:
        logging.error(f"{design_space_preset = } is not in "
                      f"{IMPLEMENTED_DESIGN_SPACE_PRESETS = }. Program will "
                      "try and continue anyway...")
        return

    if from_file:
        return _test_from_file(**design_space_kw)
    return _test_not_from_file(**design_space_kw)


def _test_from_file(variables_filepath: str,
                    constraints_filepath: str | None,
                    **design_space_kw: str | float | bool | int | list
                    ) -> None:
    """Test the entries to initialize the design space from files."""
    assert Path(variables_filepath).is_file()
    if constraints_filepath is not None:
        assert Path(constraints_filepath).is_file()


def _test_not_from_file(
        max_increase_sync_phase_in_percent: float,
        max_decrease_k_e_in_percent: float,
        max_increase_k_e_in_percent: float,
        max_absolute_sync_phase_in_deg: float = 0.,
        min_absolute_sync_phase_in_deg: float = -90.,
        maximum_k_e_is_calculated_wrt_maximum_k_e_of_section: bool = False,
        **design_space_kw: str | float | bool | int | list) -> None:
    """Test the configuration entries when design space calculated."""
    check_type(float, 'design_space', max_increase_sync_phase_in_percent,
               max_decrease_k_e_in_percent, max_increase_k_e_in_percent,
               max_absolute_sync_phase_in_deg, min_absolute_sync_phase_in_deg)
    check_type(bool, 'design_space',
               maximum_k_e_is_calculated_wrt_maximum_k_e_of_section)


def edit_configuration_dict_in_place(design_space_kw: dict[str, Any],
                                     **kwargs) -> None:
    """Edit some keys for later."""
    if design_space_kw['from_file']:
        return _edit_configuration_dict_in_place_from_file(design_space_kw)
    return _edit_configuration_dict_in_place_not_from_file(design_space_kw)


def _edit_configuration_dict_in_place_from_file(
        design_space_kw: dict[str, Any]) -> None:
    """Edit some keys for later."""
    key_files = ('variables_filepath', 'constraints_filepath')
    for key_file in key_files:
        if key_file in design_space_kw:
            design_space_kw[key_file] = Path(
                design_space_kw[key_file]).absolute()


def _edit_configuration_dict_in_place_not_from_file(
        design_space_kw: dict[str, Any]) -> None:
    """Edit some keys for later."""
    default_values = {
        'max_absolute_sync_phase_in_deg': 0.,
        'min_absolute_sync_phase_in_deg': -90.,
        'maximum_k_e_is_calculated_wrt_maximum_k_e_of_section': False,
    }
    for key, value in default_values.items():
        if key in design_space_kw:
            continue
        design_space_kw[key] = value
