.. _troubleshooting:

Troubleshooting
---------------

.. note::
   Do not hesitate to reach me by filling an `issue`_ on GitHub.
   I will do my best to help you.
   Please give me as much detail as possible, so I can reproduce the problem: OS, development environment, Python version...

.. _issue: https://github.com/AdrienPlacais/LightWin/issues

(Windows) `Microsoft Visual C++ 14.0 or greater is required` error
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Usually happens when compiling the Cython modules.

  #. Go to `visual studio website`_ and download Build Tools.
  #. Download and execute `vs_BuildTools.exe`.
  #. Check "C++ Development Desktop" checkbox.
  #. Install.

.. _visual studio website: https://visualstudio.microsoft.com/visual-cpp-build-tools/

.. todo::
   Allow for an easy way to skip Cython compilation.


`Module not found`
^^^^^^^^^^^^^^^^^^

   #. Ensure that the Python environment where LightWin was installed is activated.
         * In a Python interpreter, the `import lightwin` command should not raise error.
   #. If you installed LightWin using `conda`, check that the `src/lighwin/` folder is in your `PYTHONPATH` environment variable.

