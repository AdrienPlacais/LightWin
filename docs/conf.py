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

from pprint import pformat

from sphinx.util import inspect

import lightwin

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
    "sphinx.ext.todo",  # allow use of TODO
    # "sphinx.ext.viewcode",
    "nbsphinx",
    "sphinx_multiversion",
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
nitpicky = True
nitpick_ignore = [
    ("py:exc", "NotImplementedError"),
    ("py:exc", "TypeError"),
    ("py:class", "abc.ABCMeta"),
    ("py:class", "abc.ABC"),
    ("py:class", "cls"),
    ("py:class", "collections.abc.Callable"),
    ("py:class", "collections.abc.Collection"),
    ("py:class", "collections.abc.Container"),
    ("py:class", "collections.abc.Generator"),
    ("py:class", "collections.abc.Iterable"),
    ("py:class", "collections.abc.MutableSequence"),
    ("py:class", "collections.abc.Sequence"),
    ("py:class", "datetime.timedelta"),
    ("py:class", "logging.Formatter"),
    ("py:class", "matplotlib.axes._axes.Axes"),
    ("py:class", "matplotlib.figure.Figure"),
    ("py:class", "matplotlib.pyplot.figure"),
    ("py:class", "matplotlib.patches.Ellipse"),
    ("py:class", "matplotlib.patches.Rectangle"),
    ("py:class", "matplotlib.patches.Polygon"),
    ("py:class", "mpl_toolkits.mplot3d.axes3d.Axes3D"),
    ("py:class", "numpy.ndarray"),
    ("py:class", "np.ndarray"),
    ("py:class", "optional"),
    ("py:class", "pathlib.Path"),
    ("py:class", "Path"),
    ("py:class", "pandas.core.frame.DataFrame"),
    ("py:class", "pd.DataFrame"),
    ("py:class", "pandas.core.series.Series"),
    ("py:class", "pd.Series"),
    # pymoo fixes should be temporary
    ("py:class", "ElementwiseProblem"),
    ("py:class", "pymoo.core.algorithm.Algorithm"),
    ("py:class", "pymoo.core.result.Result"),
    ("py:class", "pymoo.core.population.Population"),
    ("py:class", "pymoo.core.problem.ElementwiseProblem"),
    ("py:class", "pymoo.core.problem.Problem"),
    ("py:class", "pymoo.termination.default.DefaultMultiObjectiveTermination"),
    # -------------------------------
    ("py:class", "scipy.optimize._constraints.Bounds"),
    ("py:class", "T"),
    ("py:class", "types.ModuleType"),
    # Due to bad design
    ("py:class", "lightwin.failures.set_of_cavity_settings.FieldMap"),
    ("py:obj", "lightwin.failures.set_of_cavity_settings.FieldMap"),
    ("py:class", "lightwin.core.list_of_elements.helper.ListOfElements"),
    # -----------------
]
# Avoid errors: `, optional` not recognized or so
# https://github.com/sphinx-doc/sphinx/issues/6861
napoleon_use_param = False

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "lightwin/modules.rst",
    "**/*.inc.rst",
]

bibtex_bibfiles = ["references.bib"]

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
    r"v0.7.0b2|latest"  # keep only major tags
)
smv_branch_whitelist = "main|doc"
smv_remote_whitelist = None
smv_released_pattern = r"v.*"
smv_latest_version = version


# -- Constants display fix ---------------------------------------------------
# https://stackoverflow.com/a/65195854
def object_description(obj: object) -> str:
    """Format the given object for a clearer printing."""
    return pformat(obj, indent=4)


inspect.object_description = object_description
