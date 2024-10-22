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

import os
import sys
from pprint import pformat

from sphinx.util import inspect

import lightwin

# Add the _ext/ folder so that Sphinx can find it
sys.path.append(os.path.abspath("./_ext"))

project = "LightWin"
copyright = (
    "2024, A. Plaçais, F. Bouly, J.-M. Lagniel, D. Uriot, B. Yee-Rendon"
)
author = "A. Plaçais, F. Bouly, J.-M. Lagniel, D. Uriot, B. Yee-Rendon"

# See https://protips.readthedocs.io/git-tag-version.html
# The full version, including alpha/beta/rc tags.
# release = re.sub("^v", "", os.popen("git describe").read().strip())
# The short X.Y version.
# version = release
version = lightwin.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinxcontrib.bibtex",  # Integrate citations
    "sphinx.ext.napoleon",  # handle numpy style
    "sphinx.ext.autodoc",
    "sphinx_rtd_theme",  # ReadTheDocs theme
    "myst_parser",
    "sphinx.ext.intersphinx",  # interlink with other docs, such as numpy
    "sphinx.ext.todo",  # allow use of TODO
    # "sphinx.ext.viewcode",
    "nbsphinx",
    "sphinx_multiversion",
    "lightwin_sphinx_extensions",
]

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",  # Keep original members order
    "private-members": True,  # Document _private members
    "special-members": "__init__, __post_init__, __str__",  # Document those special members
    "undoc-members": True,  # Document members without doc
}

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
    ("py:class", "REFERENCE_T"),
    ("py:class", "STATUS_T"),
]

# Link to other libraries
intersphinx_mapping = {
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs", None),
    "python": ("https://docs.python.org/3", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "display_version": True,
}
html_static_path = ["_static"]
html_sidebars = {
    "**": [
        "versions.html",
    ],
}

# -- Options for LaTeX output ------------------------------------------------
# https://stackoverflow.com/questions/28454217/how-to-avoid-the-too-deeply-nested-error-when-creating-pdfs-with-sphinx
latex_elements = {"preamble": r"\usepackage{enumitem}\setlistdepth{99}"}

# -- Options for multiversion in doc -----------------------------------------
smv_tag_whitelist = (
    # r"^v\d+\.\d+.*$|latest"  # would keep all the versions (unnecessary)
    r"^(v0\.7\.0|v0\.8\.0b0)$"  # keep only major tags
)
smv_branch_whitelist = "main"
smv_remote_whitelist = None
smv_released_pattern = r"v.*"
smv_latest_version = version


# -- Constants display fix ---------------------------------------------------
# https://stackoverflow.com/a/65195854
def object_description(obj: object) -> str:
    """Format the given object for a clearer printing."""
    return pformat(obj, indent=4)


inspect.object_description = object_description
