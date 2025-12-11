.. toctree::
   :maxdepth: 3

Common configuration keys
=========================

Below are listed the configuration keys commonly used in the the `[wtf]` section, independently of the chosen failure-compensation strategy.

.. csv-table::
   :file: entries/wtf_common.csv
   :header-rows: 1

Choice of failed cavities
-------------------------

General case
^^^^^^^^^^^^

The failed cavities are selected using the `failed` keyword.
This is typically a 2D list identifying groups of simultaneously failed cavities.
Each inner list represents one :class:`.FaultScenario`.

.. admonition:: Example

   .. code-block:: toml

      failed = [
         ["FM50"],
         ["FM60", "FM61"],
         ["FM50", "FM60", "FM61"],
      ]
      id_nature = "name"

   The above example defines three :class:`.FaultScenario`.

      #. The cavity named FM50 is broken.
      #. The cavities FM60 and FM61 are broken.
      #. The cavities FM50, FM60 and FM61 are broken.

`id_nature` controls how cavity identifiers are interpreted (names, cavity indices, element indices...).
The above example could also be written:

.. code-block:: toml

   failed = [
      [49],
      [59, 60],
      [49, 59, 60],
   ]
   id_nature = "cavity"

.. note::
   Indexes start at `0`.
   Hence, the cavity numbered :math:`i` by the user appears with index `i - 1`.

   .. todo::
      Add configuration option to allow index start at 1, which is more natural for users.

Automatic studies
^^^^^^^^^^^^^^^^^

The `automatic_study` configuration key saves you the hassle of having to manually type all the cavity names when performing systematic studies.
Concretely, it expand `failed` into all individual :class:`.FaultScenario` used in a systematic study.
Two modes are available:

   - `"single cavity failures"`: study all single cavity failures in `failed`.
   - `"cryomodule failures"`: study all cryomodule failures.

When `automatic_study` is set, `failed` should be a 1D list.

.. admonition:: Examples

   Study all single failures of the first five lattices:

   .. code-block:: toml

      automatic_study = "single cavity failures"
      failed = [0, 1, 2, 3, 4]
      id_nature = "lattice"

   Study all cryomodule failures in the first three sections:

   .. code-block:: toml

      automatic_study = "cryomodule failures"
      failed = [0, 1, 2]
      id_nature = "section"


Manual association of failed/compensating cavities
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you want to manually associate each failed cavity to its compensating cavities, `failed` must be a 3D list:

   - first dimension: :class:`.FaultScenario`\s
   - second dimension: groups of failed cavities (:class:`.Fault`\s)
   - third dimension: cavity identifiers in each group.

.. seealso::
   The :ref:`specific documentation<wtf-manual>` for `strategy = "manual"`.

Attribution of compensating cavities to every fault
---------------------------------------------------

The association of failed cavities with their compensating cavities is done with the `strategy` key.
The functions that assign compensating cavities to each failed cavity are listed below.

.. configmap:: lightwin.failures.strategy.STRATEGIES_MAPPING
   :value-header: Strategy function
   :keys-header: Corresponding keyword

Every strategy requires user to set specific parameters, as listed below.

