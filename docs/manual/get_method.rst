The `get` method
================

Most objects in LightWin implement a versatile `get` method.  
This method provides a convenient way to access the data you're interested in without needing to write long or complex paths.

If your development environment is properly configured for type completion, it should automatically suggest the list of valid keys you can use with this method.

.. image:: images/get_example.png
   :width: 400
   :alt: Auto-completion example in an editor

.. tip::
   The first argument of the `get` method uses the standard Python `*args` syntax.  
   This means you can request multiple keys at once:
   
   .. code-block:: python

      energy, phase = simulation_output.get("w_kin", "phi_abs")

   which is equivalent to:

   .. code-block:: python

      energy = simulation_output.get("w_kin")
      phase = simulation_output.get("phi_abs")

You can also refer to the documentation of each specific `get` method:

* :meth:`.Accelerator.get`
* :meth:`.BeamParameters.get`
* :meth:`.CavitySettings.get`
* :meth:`.Element.get`
* :meth:`.FieldMap.get`
* :meth:`.InitialBeamParameters.get`
* :meth:`.ListOfElements.get`
* :meth:`.ParticleFullTrajectory.get`
* :meth:`.RfField.get`
* :meth:`.SimulationOutput.get`
* :meth:`.TransferMatrix.get`

Additional utility keyword arguments (`**kwargs`) are supported by some `get` methods.  
Here are a few commonly used ones:

.. list-table:: Common `**kwargs` for `get` methods
   :widths: 25 25 50
   :header-rows: 1

   * - Keyword
     - Purpose
     - Notes
   * - `elt`
     - Access data for a specific :class:`.Element`
     - See :meth:`.SimulationOutput.get`
   * - `phase_space_name`
     - Select data from a particular phase space
     - See :meth:`.BeamParameters.get`
   * - `pos`
     - Retrieve data only at element entry or exit
     - Requires `elt`; see :meth:`.SimulationOutput.get`
   * - `to_deg`
     - Convert phase values (keys containing `"phi"`) to degrees
     - Defaults to `False`
   * - `to_numpy`
     - Convert the result to a NumPy array
     - Defaults to `True`

.. warning::
   Use caution with the `to_deg` keyword.  
   It may incorrectly convert keys such as `beta_phiw`, where `phiw` refers to a phase space name, not an angular quantity.  
   To avoid this, use the `phase_space_name` keyword instead.

If the requested key is not found, the method does **not** raise an error -- it simply returns an empty array.

Some examples are provided at the end of the :ref:`example notebook<notebooks-lightwin-example>`.
