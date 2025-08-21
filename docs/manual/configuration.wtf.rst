``wtf`` section
***************
.. toctree::
   :maxdepth: 5

``wtf`` stands for *what to fit*.
This section parametrizes the failed cavities, as well as how they are fixed.

*k out of n* method
===================

.. csv-table::
   :file: configuration_entries/wtf_k_out_of_n.csv
   :header-rows: 1

*l neighboring lattices* method
===============================

.. csv-table::
   :file: configuration_entries/wtf_l_neighboring_lattices.csv
   :header-rows: 1

Manual association of failed / compensating cavities
====================================================

If you want to manually associate each failed cavity with its compensating cavities:

.. csv-table::
   :file: configuration_entries/wtf_manual.csv
   :header-rows: 1


.. rubric:: Example

.. code-block:: toml

   # Indexes are cavity indexes
   idx = "cavity"
   failed = [
      [0, 1],       # First simulation first cryomodule is down
      [0],          # Second simulation only first cavity is down
      [1, 45]       # Third simulation second and 46th cavity are down
   ]

Optimisation algorithms
=======================

Here are mappings of `optimisation_algorithm` key to actual :class:`.OptimisationAlgorithm`.
Check the documentation of the optimisation algorithm you want to use, in particular if you want to tune it using `optimisation_algorithm_kwargs` key.

.. configmap:: lightwin.optimisation.algorithms.factory.ALGORITHM_SELECTOR
   :value-header: Optimisation algorithm
   :keys-header: Corresponding keys
