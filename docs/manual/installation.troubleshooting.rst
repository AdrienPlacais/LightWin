.. _troubleshooting:

Troubleshooting
---------------

`Module not found`
^^^^^^^^^^^^^^^^^^

   #. Ensure that the Python environment where LightWin was installed is activated.
         * In a Python interpreter, the `import lightwin` command should not raise error.
   #. If you installed LightWin using `conda`, check that the `src/lighwin/` folder is in your `PYTHONPATH` environment variable.

(Windows) `Microsoft Visual C++ 14.0 or greater is required` error
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Usually happens when compiling the Cython modules.

  #. Go to `visual studio website`_ and download Build Tools.
  #. Download and execute `vs_BuildTools.exe`.
  #. Check "C++ Development Desktop" checkbox.
  #. Install.

.. _visual studio website: https://visualstudio.microsoft.com/visual-cpp-build-tools/

.. note::
   Do not hesitate to reach me by filling an `issue`_ on GitHub. I will do my best to help you.

.. _issue: https://github.com/AdrienPlacais/LightWin/issues
