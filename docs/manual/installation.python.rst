Python (mandatory)
------------------
LightWin requires Python 3.12 or higher.
Ensure that you have an appropriate version of Python installed on your system.
If not, you can download the latest version from the `official Python website`_.

.. _official Python website: https://www.python.org/downloads/

Installation with pip (recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1. Navigate to the LightWin base folder (i.e., where the `pyproject.py` file is located).
2. **In a dedicated Python environment**, run the following command:

  .. code-block:: bash

     pip install -e .

The mandatory packages with their dependencies should be automatically downloaded.

.. hint::
   The `-e` flag means that the installation is editable.
   In other words, you can edit the source files and the changes will be taken into account when calling lightwin.

.. note::
   If there is a problem during the installation, file an `issue`_.
   Give me your OS, development environment, and the full log error.
   You can probably fix the issue yourself by manually installing the packages listed in `pyproject.toml`, taking a more recent version of the offending package(s).
   In any case, I'll be happy to have the information.

Installation with conda (not recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The package dependencies are listed in a single compact `pyproject.toml` file.
This is `not yet`_ supported by `conda`.
So the installation will require more work from your side.

.. _not yet: https://github.com/conda/conda/issues/12462

1. In a dedicated environment, install all the dependencies defined in the `pyproject.toml` (some can be removed, see following sections).
2. Add the `/path/to/LightWin/src` to your `PYTHONPATH` environment variable. This is the folder containing the `lightwin` folder.

.. todo::
   Consider providing more detailed instructions for setting the `PYTHONPATH`.
   For now, you can search for "PYTHONPATH" or "ModuleNotFoundError" online for additional guidance.

Following packages are optional
"""""""""""""""""""""""""""""""

* `cython` - Used to speed up calculations. Check `cython integration documentation`_.

   * Note: Installing `cython` prior to `pymoo` enable compilation of some `pymoo` functions for improved performance.

* `pytest` - To run tests and ensure everything is working as expected.
* `cloudpickle` - To pickle/unpickle some objects (see the `util.pickling` documentation).

.. _cython integration documentation: https://adrienplacais.github.io/LightWin/html/manual/installation.cython.html

For developers
""""""""""""""

To compile the documentation, the following packages are necessary:

* `sphinx_rtd_theme`
* `myst-parser`
* `nbsphinx`

The files are formatted with `black`.

Reminders
^^^^^^^^^

Installation of a package
"""""""""""""""""""""""""

To install a package, use the appropriate method based on your environment:

* If using `pip`:

  .. code-block:: bash

     pip install <package>

* If using `conda`, avoid mixing with `pip` to prevent potential conflicts. Instead, use:

  .. code-block:: bash

     conda install <package>

.. note::
   Since `pymoo` is not available on the default Anaconda channels, you should create a `conda` environment and use `conda-forge`:

   .. code-block:: bash

      conda create -n <env-name> -c conda-forge python=3.12
      conda activate <env-name>
      conda install cython matplotlib numpy palettable pandas scipy tkinter pymoo pytest -c conda-forge

   Always specify `-c conda-forge` when installing or updating packages.

   .. warning::
      `pip` and `conda` are not fully compatible.
      Avoid using them together, or create a dedicated environment to prevent conflicts.
      For more details, you may refer to this `video`_.

   .. _video: https://www.youtube.com/watch?v=Ul79ihg41Rs

