"""Define function to build the Cython module(s).

Should be automatically handled at the package installation. If not, simply
run:

.. code-block:: sh

    make compile

"""

import importlib
from pathlib import Path
from typing import Literal

from setuptools import Extension, setup

CY_MODULES = (
    "lightwin.core.em_fields.cy_field_helpers",
    "lightwin.beam_calculation.cy_envelope_1d.transfer_matrices",
    "lightwin.beam_calculation.integrators.cy_rk4",
)


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


def _ext_modules(use_cython: bool) -> list[Extension] | None:
    """Instantiate the ``Extension`` objects.

    Handle cases where there are missing source files or missing modules.

    """
    if not _numpy_is_installed():
        return None
    files, all_exist = _module_files(use_cython)

    if not all_exist:
        if not use_cython:
            print("At least one file missing. Not building Cython modules.\n")
            return []
        print(
            "At least one PYX file missing. Checking if equivalent C files "
            "provided..."
        )
        return _ext_modules(use_cython=False)

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


setup(
    name="lightwin",
    ext_modules=_ext_modules(use_cython=_cython_is_installed()),  # type: ignore
)
