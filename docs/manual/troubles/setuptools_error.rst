.. _setuptools_scm:

setuptools-scm was unable to detect version
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Downloading LightWin using `Download ZIP` is not recommended.
If you do so, you will encounter this error when trying to `pip install -e .[test]`:

.. code-block:: console
 
   LookupError: setuptools-scm was unable to detect version for /path/to/lightwin/.
   Make sure you're either building from a fully intact git repository or PyPI tarballs. Most other sources (such as GitHub's tarballs, a git checkout without the .git folder) don't contain the necessary metadata and will not work.
   For example, if you're using pip, instead of https://github.com/user/proj/archive/master.zip use git+https://github.com/user/proj.git#egg=proj
   Alternatively, set the version with the environment variable SETUPTOOLS_SCM_PRETEND_VERSION_FOR_${NORMALIZED_DIST_NAME} as described in https://setuptools-scm.readthedocs.io/en/latest/config.


- For users, the best solution is to take the package from PyPI instead: `pip install lightwin`
- For developers, a workaround is to manually set the environment variable `SETUPTOOLS_SCM_PRETEND_VERSION` to the current version number before running `pip`:

.. code-block:: console

   alias SETUPTOOLS_SCM_PRETEND_VERSION="0.10.5"
   pip install -e .[test]

