.. _wtf-manual:

.. toctree::
   :maxdepth: 3

Manual association of failed / compensating cavities
----------------------------------------------------

If you want to manually associate each failed cavity with its compensating cavities:

.. csv-table::
   :file: entries/wtf_manual.csv
   :header-rows: 1

In order to tell LightWin which cavities should compensate which failures, both `failed` and `compensating_manual` must be 3D lists.
The dimensions represent:

   - first dimension: :class:`.FaultScenario`\s
   - second dimension: groups of cavities that fail (or compensate) together
   - third dimension: cavity identifiers in each group.

The length of the outermost lists must match and defines the number of :class:`.FaultScenario` instances.
For each scenario, the second-level list in `compensating_manual` must have the same length as the second-level list in `failed`.

.. admonition:: Example

   .. code-block:: toml

      strategy = "manual"
      failed = [
         [
            ["FM50"],
         ],
         [
            ["FM60", "FM61"],
         ],
         [
            ["FM50"],
            ["FM60", "FM61"],
         ],
      ]
      compensating_manual = [
         [
            ["FM49", "FM51"],
         ],
         [
            ["FM58", "FM59", "FM62", "FM63"],
         ],
         [
            ["FM49", "FM51"],
            ["FM58", "FM59", "FM62", "FM63"],
         ],
      ]
      id_nature = "name"

   The above example defines three :class:`.FaultScenario`.

      #. The cavity named FM50 is broken, and compensated with the two neighboring cavities.
      #. The cavities FM60 and FM61 are broken, and compensated with the four neighboring cavities.
      #. The cavities FM50, FM60 and FM61 are broken.
         - First, FM50 is compensated with its neighboring cavities.
         - Then the beam is propagated to the next failing group, and FM60 and FM61 are compensated together using their four neighboring cavities.

Within each scenario, compensation steps are applied in the order they appear in the list.
