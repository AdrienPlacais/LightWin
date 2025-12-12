.. toctree::
   :maxdepth: 3

*Corrector at exit* method
--------------------------

Use ``n_compensating`` cavities around the failure to shape the beam and propagate it without losses.
Rephase downstream cavities to keep the beam as intact as possible.
Give an ultimate energy boost to the beam with the last ``n_correctors`` cavities.

This method is very similar to the one used at SNS :cite:`Shishlo2022`.
In this paper however, there are no compensating cavities around the failure.

.. important::
   This method was designed to work with:

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
   :file: entries/wtf_corrector_at_exit.csv
   :header-rows: 1

