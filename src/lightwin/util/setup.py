#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Define function to build the Cython module(s).

To compile, go to ``LightWin/source/`` and enter:
``python lightwin/util/setup.py build_ext --inplace``.

.. todo::
    Auto move the ``.so``.

"""
import os
import os.path

import numpy as np
from Cython.Build import cythonize
from setuptools import setup

source_path = os.getcwd()
pyx_path = os.path.join(
    source_path,
    "lightwin/beam_calculation/envelope_1d/transfer_matrices_c.pyx",
)

setup(
    ext_modules=cythonize(
        pyx_path,
        # compiler_directives={'boundscheck': False,
        #                      'nonecheck': False,
        #                      'wraparound': False}
    ),
    include_dirs=[np.get_include()],
)
