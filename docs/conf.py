# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Build info --------------------------------------------------------------
# From project base, generate the rst files with:
# sphinx-apidoc -o docs/lightwin -f -e -M src/
# cd docs/lightwin
# nvim *.rst
# :bufdo %s/^\(\S*\.\)\(\S*\) \(package\|module\)/\2 \3 | update
# cd ../..
# sphinx-multiversion docs ../LightWin-docs/html

# If you want unversioned doc:
# make html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import lightwin

project = "LightWin"
copyright = "2024, A. Plaçais, F. Bouly, B. Yee-Rendon"
author = "A. Plaçais, F. Bouly, B. Yee-Rendon"

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
    "special-members": "__init__, __post_init__",  # Document those special members
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
    "experimental",
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
    r"v0.7.0b1|latest"  # keep only major tags
)
smv_branch_whitelist = "main|doc"
smv_remote_whitelist = None
smv_released_pattern = r"v.*"
smv_latest_version = version
