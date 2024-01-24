#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The functions to test the ``wtf`` (what to fit) key of the config file."""
import configparser
import logging

from config.ini.failures.failed_cavities import test_failed_cavities
from config.ini.failures.strategy import test_strategy
from config.ini.optimisation.algorithm import test_optimisation_algorithm
from config.ini.optimisation.objective import test_objective_preset


# =============================================================================
# Front end
# =============================================================================
def test(c_wtf: configparser.SectionProxy) -> None:
    """Test the 'what_to_fit' dictionaries."""
    tests = {'failed_cavities': test_failed_cavities,
             'strategy': test_strategy,
             'objective_preset': test_objective_preset,
             'optimisation_algorithm': test_optimisation_algorithm,
             'misc': _test_misc,
             }
    for key, test in tests.items():
        if not test(c_wtf):
            raise IOError(f"What to fit {c_wtf.name}: error in entry {key}.")
    logging.info(f"what to fit {c_wtf.name} tested with success.")


def config_to_dict(c_wtf: configparser.SectionProxy) -> dict:
    """Convert wtf configparser into a dict."""
    wtf = {}
    # Special getters
    getter = {
        'objective_preset': c_wtf.get,
        'failed': c_wtf.getfaults,
        'manual list': c_wtf.getgroupedfaults,
        'k': c_wtf.getint,
        'l': c_wtf.getint,
        'phi_s fit': c_wtf.getboolean,
    }
    if c_wtf.get('strategy') == 'manual':
        getter['failed'] = c_wtf.getgroupedfaults

    for key in c_wtf.keys():
        if key in getter:
            wtf[key] = getter[key](key)
            continue

        wtf[key] = c_wtf.get(key)

    return wtf


def _test_misc(c_wtf: configparser.SectionProxy) -> bool:
    """Perform some other tests."""
    if 'phi_s fit' not in c_wtf.keys():
        logging.error("Please explicitly precise if you want to fit synch "
                      "phases (recommended for least squares, which do not "
                      "handle constraints) or not (for algorithms that can "
                      "handle it).")
        return False

    try:
        c_wtf.getboolean("phi_s fit")
    except ValueError:
        logging.error("Not a boolean.")
        return False
    return True