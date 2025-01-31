Testing (for developers)
------------------------

Read this section if you built LightWin from source and expect to modify the code.

Pytest
^^^^^^

To test your installation, navigate to the base directory (where the `pyproject.toml` file is located) and run the following command:

.. code-block:: bash

   pytest -m "not implementation"

If TraceWin is not installed, you can skip tests requiring it by running:

.. code-block:: bash

   pytest -m "not tracewin and not implementation"

If Cython is not installed or Cython modules not compiled, you can skip corresponding tests with:

.. code-block:: bash

   pytest -m "not cython and not implementation"

You can also combine test markers as defined in `pyproject.toml`. For example, to run only fast smoke tests, use:

.. code-block:: bash

   pytest -m "(smoke and not slow)"

.. note::
   `xfailed` errors: `xfailed` stands for "expected to fail" and these errors are usually intended for developers to track issues. They are not necessarily problematic for users.

.. note::
   Test with the `implementation` mark are for features under not yet implemented.
   Do not expect them to work!
