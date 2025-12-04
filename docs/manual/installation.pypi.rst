.. _simple-installation:

Simple installation (recommended)
---------------------------------

You will need Python 3.12 or higher.
If you run a 32-bits Windows system, you will also need a :ref:`C compiler<windows_c_compiler>`.
Set up a virtual environment; instructions will vary according to you installation.

.. tabs::

   .. tab:: venv (Recommended)

      Python's built-in `venv` module is the recommended way to create a virtual environment.

      .. code-block:: bash

         python -m venv venv

      Activate the environment:

      - On macOS/Linux:

        .. code-block:: bash

           source venv/bin/activate

      - On Windows:

        .. code-block:: bash

           venv\Scripts\activate

   .. tab:: virtualenv

      If you prefer `virtualenv`, install it first:

      .. code-block:: bash

         pip install virtualenv
         virtualenv venv

      Activate the environment:

      - On macOS/Linux:

        .. code-block:: bash

           source venv/bin/activate

      - On Windows:

        .. code-block:: bash

           venv\Scripts\activate

   .. tab:: Conda

      If you manage environments with Conda:

      .. code-block:: bash

         conda create --name lightwin python=3.x
         conda activate lightwin

Once it is activated, run the following command:

.. code-block:: bash

   pip install lightwin[cython]

Note that Cython is not mandatory, but speeds up calculations.
If you run into a Cython related issue, you can always:

.. code-block:: bash

   pip install lightwin

