``wtf`` section
***************
.. toctree::
   :maxdepth: 5

``wtf`` stands for *what to fit*.
This section parametrizes the failed cavities, as well as how they are fixed.

If you want to use the *k out of n* method:

.. csv-table::
   :file: configuration_entries/wtf_k_out_of_n.csv
   :header-rows: 1

If you want to use the *l neighboring lattices* method:

.. csv-table::
   :file: configuration_entries/wtf_l_neighboring_lattices.csv
   :header-rows: 1

If you want to manually associate each failed cavity with its compensating cavities:

.. csv-table::
   :file: configuration_entries/wtf_manual.csv
   :header-rows: 1

.. note::
   You can type the index of failed cavities on several lines if you want to study several fault scenarios at once.

.. rubric:: Example

.. code-block:: toml

   # Indexes are cavity indexes
   idx = "cavity"
   failed = [
      [0, 1],       # First simulation first cryomodule is down
      [0],          # Second simulation only first cavity is down
      [1, 45]       # Third simulation second and 46th cavity are down
   ]
