Testing
-------

Pytest
^^^^^^

To test your installation, navigate to the base directory (where the `pyproject.toml` file is located) and run the following command:

.. code-block:: bash

   pytest

If TraceWin is not installed, you can skip tests requiring it by running:

.. code-block:: bash

   pytest -m not tracewin

If Cython is not installed or Cython modules not compiled, you can skip corresponding tests with:

.. code-block:: bash

   pytest -m not cython

You can also combine test markers as defined in `pyproject.toml`. For example, to run only fast smoke tests, use:

.. code-block:: bash

   pytest -m "(smoke and not slow)"

Frequent errors
^^^^^^^^^^^^^^^

* `E   ModuleNotFoundError: No module named 'beam_calculation'`.

   * Your `PYTHONPATH` is not properly set. Ensure that the directory containing the LightWin source code is included in your `PYTHONPATH`.

* `xfailed` errors.

   * `xfailed` stands for "expected to fail" and these errors are usually intended for developers to track issues. They are not necessarily problematic for users.

