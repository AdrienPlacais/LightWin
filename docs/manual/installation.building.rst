Building from source (for developers)
-------------------------------------

Pre-requisites:

* Python 3.12 or higher.
* A C++ compiler. On Unix systems, install `gcc`. On Windows, check :ref:`here<windows_c_compiler>`.

Cloning the repository
^^^^^^^^^^^^^^^^^^^^^^

Download the source from GitHub.

.. code-block:: bash

   git clone git@github.com:AdrienPlacais/LightWin.git

Alternatively, you can download the code as a `.zip` file from the repository's page.
However, please note that using this method requires manually downloading updates whenever changes are made to the repository.

Installation
^^^^^^^^^^^^

Navigate to the `LightWin` folder.
Create and activate a Python environment (see :ref:`instructions<simple-installation>`).
Install and test with:

.. code-block:: bash

   pip install -e .[test]
   pytest -m "not tracewin"

Setting up TraceWin requires :ref:`additional steps<installation-tracewin>`.

.. hint::
   If you encounter issues with the `[test]` extra dependency, try escaping the brackets:
   
   .. code-block:: bash
   
      pip install -e .\[test\]

If you want to install LightWin with `conda`, you will have to `manually`_ install all the dependencies listed in the `pyproject.toml` file.

.. _manually: https://github.com/conda/conda/issues/12462
