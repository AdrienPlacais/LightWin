# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Build info --------------------------------------------------------------
# From project base, generate the rst files with:
# sphinx-apidoc -o docs/lightwin -f -e -M src/ -d 5
# cd docs/lightwin
# nvim *.rst
# :bufdo %s/^\(\S*\.\)\(\S*\) \(package\|module\)/\2 \3/e | update
# cd ../..
# sphinx-multiversion docs ../LightWin-docs/html

# If you want unversioned doc:
# make html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from __future__ import annotations

import os
import sys
from pprint import pformat

import sphinx
from sphinx.util import inspect

import lightwin

# Add the _ext/ folder so that Sphinx can find it
sys.path.append(os.path.abspath("./_ext"))

project = "LightWin"
author = "A. Plaçais, F. Bouly, J.-M. Lagniel, D. Uriot, B. Yee-Rendon"
copyright = "2025, " + author

# See https://protips.readthedocs.io/git-tag-version.html
# The full version, including alpha/beta/rc tags.
# release = re.sub("^v", "", os.popen("git describe").read().strip())
# The short X.Y version.
# version = release
version = lightwin.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "lightwin_sphinx_extensions",
    "myst_parser",
    "nbsphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinx_rtd_theme",
    "sphinx_tabs.tabs",
    "sphinxcontrib.bibtex",
]

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",  # Keep original members order
    "private-members": True,  # Document _private members
    "special-members": "__init__, __post_init__, __str__",  # Document those special members
    "undoc-members": True,  # Document members without doc
}
autodoc_mock_imports = ["pso", "lightwin.optimisation.algorithms.pso"]

add_module_names = False
default_role = "literal"
todo_include_todos = True

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "lightwin/modules.rst",
    "**/*.inc.rst",
]
bibtex_bibfiles = ["references.bib"]

# -- Check that there is no broken link --------------------------------------
nitpicky = True
nitpick_ignore = [
    # Not recognized by Sphinx, don't know if this is normal
    ("py:class", "optional"),
    ("py:class", "T"),
    ("py:class", "numpy.float64"),
    ("py:class", "numpy.typing.NDArray"),
    ("py:class", "NDArray[np.float64]"),
    ("py:class", "NDArray"),
    ("py:class", "np.float64"),
    # pymoo fixes should be temporary
    ("py:class", "ElementwiseProblem"),
    ("py:class", "pymoo.core.algorithm.Algorithm"),
    ("py:class", "pymoo.core.result.Result"),
    ("py:class", "pymoo.core.population.Population"),
    ("py:class", "pymoo.core.problem.ElementwiseProblem"),
    ("py:class", "pymoo.core.problem.Problem"),
    ("py:class", "pymoo.termination.default.DefaultMultiObjectiveTermination"),
    # Due to bad design
    ("py:class", "lightwin.failures.set_of_cavity_settings.FieldMap"),
    ("py:obj", "lightwin.failures.set_of_cavity_settings.FieldMap"),
    ("py:class", "lightwin.core.list_of_elements.helper.ListOfElements"),
    # Due to Sphinx error, https://github.com/sphinx-doc/sphinx/issues/10785
    ("py:class", "definitions_t"),
    ("py:class", "ComputeBeamPropagationT"),
    ("py:class", "ComputeConstraintsT"),
    ("py:class", "ComputeResidualsT"),
    ("py:class", "post_treater_t"),
    ("py:class", "ref_value_t"),
    ("py:class", "tester_t"),
    ("py:class", "value_t"),
]

# Link to other libraries
intersphinx_mapping = {
    "bayes_opt": (
        "https://bayesian-optimization.github.io/BayesianOptimization/master/",
        None,
    ),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs", None),
    "python": ("https://docs.python.org/3", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
}

autodoc_type_aliases = {
    "np.float64": "numpy.float64",
    "NDArray": "numpy.typing.NDArray",
}
# Parameters for sphinx-autodoc-typehints
always_document_param_types = True
always_use_bars_union = True
typehints_defaults = "comma"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_sidebars = {
    "**": [
        "versions.html",
    ],
}

# -- Options for IPYNB --------------------------------------------------------
# In particular: options for automatic re-execution
# (they are auto-cleaned by pre-commit to avoid cluttering github repo)

on_rtd = os.environ.get("READTHEDOCS") == "True"

# We should rebuild if we are on ReadTheDocs
if on_rtd:
    nbsphinx_execute = "auto"
# Locally, we rebuild if we ran `make ci`, but not if we `make html`
else:
    # This `NB_EXEC` env constant is defined in the docs/Makefile
    nbsphinx_execute = os.environ.get("NB_EXEC", "auto")

# -- Options for LaTeX output ------------------------------------------------
# https://stackoverflow.com/questions/28454217/how-to-avoid-the-too-deeply-nested-error-when-creating-pdfs-with-sphinx
latex_elements = {"preamble": r"\usepackage{enumitem}\setlistdepth{99}"}


# -- Constants display fix ---------------------------------------------------
# https://stackoverflow.com/a/65195854
def object_description(obj: object) -> str:
    """Format the given object for a clearer printing."""
    return pformat(obj, indent=4)


inspect.object_description = object_description

# -- Shortcuts ---------------------------------------------------
rst_prolog = """
.. |axplot| replace:: :meth:`matplotlib.axes.Axes.plot`

.. |issue| replace:: issue
.. _issue: https://github.com/AdrienPlacais/LightWin/issues

"""

# -- Bug fixes ---------------------------------------------------------------
# Fix following warning:
# <unknown>:1: WARNING: py:class reference target not found: pathlib._local.Path [ref.class]
# Note that a patch is provided by Sphinx 8.2, but nbsphinx 0.9.7 requires
# sphinx<8.2
# Associated issue:
# https://github.com/sphinx-doc/sphinx/issues/13178
if sys.version_info[:2] >= (3, 13) and sphinx.version_info[:2] < (8, 2):  # type: ignore
    import pathlib

    from sphinx.util.typing import _INVALID_BUILTIN_CLASSES

    _INVALID_BUILTIN_CLASSES[pathlib.Path] = "pathlib.Path"  # type: ignore
    nitpick_ignore.append(("py:class", "pathlib._local.Path"))
