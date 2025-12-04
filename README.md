[![Py versions](https://img.shields.io/badge/python-3.12-blue)](https://img.shields.io/badge/python-3.12-blue)
[![PyPi](https://img.shields.io/pypi/v/lightwin)](https://pypi.org/project/LightWin/)
[![Pytest](https://img.shields.io/badge/py-test-blue?logo=pytest)](https://github.com/AdrienPlacais/LightWin/actions/workflows/test.yml)
[![Documentation status](https://readthedocs.org/projects/lightwin/badge/?version=latest)](https://lightwin.readthedocs.io/en/latest/?badge=latest)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/AdrienPlacais/LightWin/main.svg)](https://results.pre-commit.ci/latest/github/AdrienPlacais/LightWin/main)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

# LightWin

LightWin is a tool to automatically find compensation settings for cavity
failures in linacs.

## Installation

The full installation instructions are detailed [in the documentation](https://lightwin.readthedocs.io/en/latest/manual/installation.html).

The steps are straightforward and can be summarized as follows:

### Users

1. Create a dedicated Python environment.
2. Run `pip install lightwin`

### Developers

1. Clone the repository: `git clone git@github.com:AdrienPlacais/LightWin.git`

> [!WARNING]
> If you `Download ZIP` this repository (which can happen if you don't have
> access to `git`), installation will fail at step #3.
> [A workaround](https://lightwin.readthedocs.io/en/latest/manual/troubles/setuptools_error.html) is proposed in the documentation.

2. Create a dedicated Python environment.
3. From LightWin folder: `pip install -e .[test]`
4. Test that everything is working with `pytest -m "not tracewin and not implementation"`.

> [!NOTE]
> If you are completely new to Python and these instructions are unclear, check [this tutorial](https://python-guide.readthedocs.io/en/latest/).
> In particular, you will want to:
>
> 1. [Install Python](https://python-guide.readthedocs.io/en/latest/starting/installation/) 3.12 or higher.
> 2. [Learn to use Python environments](https://python-guide.readthedocs.io/en/latest/dev/virtualenvs/), `pipenv` or `virtualenv`.
> 3. [Install a Python IDE](https://python-guide.readthedocs.io/en/latest/dev/env/#ides) such as Spyder or VSCode.

> [!NOTE]
> Note that the TraceWin module will not work out of the box.
> You will need to tell LightWin were to find your TraceWin executables.
> See [dedicated instructions](https://lightwin.readthedocs.io/en/latest/manual/installation.tracewin.html).

## Documentation

Documentation is now automatically built and hosted on [Read the docs](https://lightwin.readthedocs.io/en/latest/).

## How to run

See [documentation](https://lightwin.readthedocs.io/en/latest/manual/usage.html).

## Example

See the `data/example` folder.
