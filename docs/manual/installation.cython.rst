.. _Cython-setup:


Cython setup (should be automatic)
----------------------------------

.. note::
   If you installed LightWin with `pip` and there was no error, you do not need to read this section.
   If you built the code from source, you can check that everything works as expected with `pytest -m cython`.

Cython is an optional but highly recommended tool to speed up beam dynamics calculations.
Here's how to properly install and use Cython with the project:

1. Pre-requisites
^^^^^^^^^^^^^^^^^
Ensure Cython is installed before installing other packages like `pymoo` to take full advantage of its capabilities:

 .. code-block:: bash
    
    pip install cython

You should have Python installed in your `PATH`, and a `C` compiler.
While the compiler should be available on Unix systems, you will have to install `Microsoft Build Tools for Visual Studio` (`C++ build tools` component) on Windows.
Check :ref:`this link<windows_c_compiler>` for instructions.

2. Compiling Cython modules
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Some parts of LightWin, in particular the :class:`.CyEnvelope1D` beam calculator, have Cython-optimized code that need to be compiled.
Navigate to the LightWin directory and run:

.. tabs::

   .. tab:: Unix systems

      .. code-block:: bash

         make compile

   .. tab:: Windows

      .. code-block:: bash

         python setup.py build_ext --inplace
 
This command compiles the Cython files and places the compiled modules (`.pyd` or `.so` extensions) in the appropriate directories.


3. Handling compiled files
^^^^^^^^^^^^^^^^^^^^^^^^^^
After compilation, the compiled files should be automatically placed in the correct locations.
If not, manually move the created files:

   * Unix (Linux/macOS): `build/lib.linux-XXX-cpython-3XX/beam_calculation/cy_envelope_1d/transfer_matrices.cpython-3XX-XXXX-linux-gnu.so`
   * Windows: `build/lib.win-XXXX-cpython-3XX/beam_calculation/cy_envelope_1d/transfer_matrices.cp3XX-win_XXXX.pyd`

To:

   * `/path/to/LightWin/src/lightwin/beam_calculation/cy_envelope_1d/`.

`Microsoft Visual C++ 14.0 or greater is required` error is covered :ref:`here<windows_c_compiler>`.


4. Restarting Your Interpreter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you are using an IDE like Spyder or VSCode, remember to restart the kernel after compiling the Cython modules to ensure they are correctly loaded.

5. Testing Cython Compilation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To verify that everything is set up correctly, run the test suite using `pytest`.
This will check if the Cython modules are properly integrated:

.. code-block:: bash

   pytest -m cython

.. seealso::

   `Cython documentation <https://cython.readthedocs.io/>`_.
