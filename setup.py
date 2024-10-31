#!/usr/bin/env python3
"""Define function to build the Cython module(s).

Should be automatically handled by the ``pyproject.toml`` when running
``pip install -e .``.

If necessary, you can recompile the Cython module(s):
    1. Navigate to this file directory.
    2. Run ``python setup.py build_ext --inplace``

"""
import numpy as np
from Cython.Build import cythonize
from Cython.Compiler import Options
from setuptools import Extension, setup

Options.docstrings = True
Options.annotate = False

# Define the modules to be compiled
extensions = [
    Extension(
        "lightwin.beam_calculation.cy_envelope_1d.transfer_matrices",
        ["src/lightwin/beam_calculation/cy_envelope_1d/transfer_matrices.pyx"],
        include_dirs=[np.get_include()],
    )
]

# Function that will be executed at installation
setup(name="lightwin", ext_modules=cythonize(extensions))
