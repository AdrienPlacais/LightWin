#!/usr/bin/env python3
"""Define function to build the Cython module(s).

Should be automatically handled by the ``pyproject.toml`` when running
``pip install -e .``.

If necessary, you can recompile the Cython module(s):
    1. Navigate to this file directory.
    2. Run ``python setup.py build_ext --inplace``

"""
import importlib
from pathlib import Path
from typing import Literal

from setuptools import Extension, setup

CY_MODULES = ("lightwin.beam_calculation.cy_envelope_1d.transfer_matrices",)


def _cython_is_installed() -> bool:
    """Determine if Cython is installed."""
    try:
        importlib.import_module("Cython")
    except ImportError:
        print("Cython is not installed. Building from C files.")
        return False
    return True


def _numpy_is_installed() -> bool:
    """Determine if numpy is installed."""
    try:
        importlib.import_module("numpy")
    except ImportError:
        print("Numpy is not installed. Not building cython modules.\n")
        return False
    return True


def _filetypes(use_cython: bool) -> Literal[".pyx", ".c"]:
    """Determine the filetype of the file to compile."""
    return ".pyx" if use_cython else ".c"


def _module_files(use_cython: bool) -> tuple[list[Path], bool]:
    """Determine the files to compile."""
    filetype = _filetypes(use_cython)
    files = [
        Path("src/" + module.replace(".", "/") + filetype)
        for module in CY_MODULES
    ]
    all_exist = True
    for file in files:
        if file.is_file():
            continue
        print(f"{file = } should exist but was not found.")
        all_exist = False
    return files, all_exist


def _ext_modules(use_cython: bool) -> list[Extension]:
    """Instantiate the ``Extension`` objects.

    Handle cases where there are missing source files or missing modules.

    """
    files, all_exist = _module_files(use_cython)

    if not all_exist:
        if not use_cython:
            print("At least one file missing. Not building Cython modules.\n")
            return []
        print(
            "At least one PYX file missing. Checking if equivalent C files "
            "provided..."
        )
        return _ext_modules(not use_cython)

    import numpy as np

    extensions = [
        Extension(module, [file], include_dirs=[np.get_include()])
        for module, file in zip(CY_MODULES, files, strict=True)
    ]

    if not use_cython:
        print("Building C files.\n")
        return extensions
    print("Building PYX files.\n")
    return _cythonize(extensions)


def _cythonize(extensions: list[Extension]) -> list[Extension]:
    """Cythonize the provided PYX extensions."""
    from Cython.Build import cythonize
    from Cython.Compiler import Options

    Options.docstrings = True
    Options.annotate = False
    return cythonize(extensions)


def setup_wrapper() -> None:
    """Check existence of modules, files, and compile Cython if possible."""
    if not _numpy_is_installed():
        return

    ext_modules = _ext_modules(_cython_is_installed())
    setup(name="lightwin", ext_modules=ext_modules)


setup_wrapper()
