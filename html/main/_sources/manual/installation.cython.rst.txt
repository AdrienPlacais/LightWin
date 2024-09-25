Cython setup (should be automatic)
----------------------------------

.. note::
   If you installed LightWin with `pip install -e .` and there was no error, you do not need to read this section.
   You can check that everything works as expected by running `pytest -m cython`.

Cython is an optional but highly recommended tool to speed up beam dynamics calculations.
Here's how to properly install and use Cython with the project:

1. Installing Cython
^^^^^^^^^^^^^^^^^^^^
Ensure Cython is installed before installing other packages like `pymoo` to take full advantage of its capabilities:

 * Using `pip`:
 
    .. code-block:: bash
       
       pip install cython
 
 * Using `conda`:
 
    .. code-block:: bash
       
       conda install cython -c conda-forge
     

2. Compiling Cython modules
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Some parts of LightWin, in particular the :class:`.Envelope1D` beam calculator, have Cython-optimized code that need to be optimized.
Follow this steps to compile the modules:

 1. Navigate to the `LightWin` base directory:
 
 .. code-block:: bash
 
    cd /path/to/LightWin/
 
 2. Run the `setup` script:
 
 .. code-block:: bash
 
    python setup.py build_ext --inplace
   
This command compiles the Cython files and places the compiled modules (`.pyd` or `.so` extensions) in the appropriate directories.


3. Handling compiled files
^^^^^^^^^^^^^^^^^^^^^^^^^^
After compilation, the compiled files should be automatically places in the correct locations.
If not, manually move the created files:

   * Unix (Linux/macOS): `build/lib.linux-XXX-cpython=3XX/beam_calculation/envelope_1d/transfer_matrices_c.cpython-3XX-XXXX-linux-gnu.so`
   * Windows: `build/lib.win-XXXX-cpython-3XX/beam_calculation/envelope_1d/transfer_matrices_c.cp3XX-win_XXXX.pyd`

To:

   * `/path/to/LightWin/src/lightwin/beam_calculation/envelope_1d/`.

`Microsoft Visual C++ 14.0 or greater is required` error is covered in the :ref:`troubleshooting section<troubleshooting>`.


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

.. todo::
   * Revise integration so that a missing Cython does not lead to import errors.
   * Specific Cython tests
