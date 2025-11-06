``wtf`` section
***************
.. toctree::
   :maxdepth: 5

``wtf`` stands for *what to fit*.
This section parametrizes the failed cavities, as well as how they are fixed.

Selecting compensating cavities
===============================

Compensating cavities are selected according to the `strategy` keyword; actual functions mapping failures with failed cavities are listed here:

.. configmap:: lightwin.failures.strategy.STRATEGIES_MAPPING
   :value-header: Strategy function
   :keys-header: Corresponding keyword

Every strategy requires user to set specific parameters, as listed below.

*k out of n* method
-------------------

Compensate the :math:`n` failed cavities with :math:`k\times n` closest cavities :cite:`saini_assessment_2021,Yee-Rendon2022a`.

.. csv-table::
   :file: configuration_entries/wtf_k_out_of_n.csv
   :header-rows: 1

*l neighboring lattices* method
-------------------------------

Every fault will be compensated by `l` full lattices, direct neighbors of the errors :cite:`Bouly2014,Placais2022a`.
You must provide `l`.
Non-failed cavities in the same lattice as the failure are also used.

.. csv-table::
   :file: configuration_entries/wtf_l_neighboring_lattices.csv
   :header-rows: 1

*Corrector at exit* method
--------------------------

Use ``n_compensating`` cavities around the failure to shape the beam and propagate it without losses.
Rephase downstream cavities to keep the beam as intact as possible.
Give an ultimate energy boost to the beam with the last ``n_correctors`` cavities.

This method is very similar to the one used at SNS :cite:`Shishlo2022`.
In this paper however, there are no compensating cavities around the failure.

.. important::
   This method was designed to to work with:

      1. `reference_phase_policy = "phi_s"`.
         This way, cavities downstream of a failure are rephased to preserve synchronous phase and hence acceptance.
      2. `strategy = "corrector at exit"`.
         This tells the :func:`.failed_and_compensating` called at initialization of :class:`.FaultScenario` to add ``n_correctors`` cavities at the end of the linac to retrieve energy.

   **LightWin will not verify that these keys are properly set.**

   .. todo::
      Automatically check validity of ``reference_phase_policy`` and consistency of ``strategy``/``objective_preset``.

.. warning::
   Setting `n_compensating = 0` in the `[wtf]` section of the `TOML` configuration file will raise an error, as LightWin currently does not handle optimization problem without compensating elements.

   .. todo::
      Handle optimization problems without compensating cavities.
      - Skip creation of associated :class:`.Fault`?
      - Other solution?

.. csv-table::
   :file: configuration_entries/wtf_corrector_at_exit.csv
   :header-rows: 1

Manual association of failed / compensating cavities
----------------------------------------------------

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

Global, global downstream compensation
--------------------------------------

Use either all cavities of the linac, or all cavities downstream of the failure.
These methods require a very large number of compensating cavities and therefore significant numerical resources.
As a result, they are only lightly tested.

Settings optimization problem
=============================

Optimisation objectives
-----------------------

The values for `objective_preset` are explained here:

.. configmap:: lightwin.optimisation.objective.factory.OBJECTIVE_PRESETS
   :value-header: Objectives preset
   :keys-header: Corresponding keys

If you do not retrieve the beam absolute phase at the exit of the compensation zone (*eg*, if you use :class:`.EnergyMismatch`), you should probably rephase downstream cavities to keep RF/beam synchronicity.
This is acheived by setting your `beam_calculator.reference_phase_policy` key to `"phi_0_rel"` or `"phi_0_s"`.
See also :ref:`this notebook<notebooks-cavities-reference-phase>`.

.. note::
   You can subclass :class:`.ObjectiveFactory` to your liking, and pass the created object to :func:`.run_simulation` directly.

  .. code-block:: python
    
     config = process_config(toml_filepath, toml_keys)
     fault_scenarios = run_simulation(
         config,
         objective_factory_class=MyObjectiveFactory,  # subclass of ObjectiveFactory
     )

  An example is provided in `data/example/my_own_objectives.py`.

  .. todo::
     Make it more explicit and easy to understand with a jupyter notebook.

Optimisation algorithms
-----------------------

Here are mappings of `optimisation_algorithm` key to actual :class:`.OptimisationAlgorithm`.
Check the documentation of the optimisation algorithm you want to use, in particular if you want to tune it using `optimisation_algorithm_kwargs` key.

.. configmap:: lightwin.optimisation.algorithms.factory.ALGORITHM_SELECTOR
   :value-header: Optimisation algorithm
   :keys-header: Corresponding keys
