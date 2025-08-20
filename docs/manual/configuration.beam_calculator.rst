.. _BeamCalculator-configuration-help-page:

``beam_calculator`` section (mandatory)
***************************************
.. toctree::
   :maxdepth: 5

If the desired :class:`.BeamCalculator` is :class:`.Envelope1D`:

.. csv-table::
   :file: configuration_entries/beam_calculator_envelope_1d.csv
   :header-rows: 1

If the desired :class:`.BeamCalculator` is :class:`.Envelope3D`:

.. csv-table::
   :file: configuration_entries/beam_calculator_envelope_3d.csv
   :header-rows: 1

If the desired :class:`.BeamCalculator` is :class:`.TraceWin`:

.. csv-table::
   :file: configuration_entries/beam_calculator_tracewin.csv
   :header-rows: 1

Check TraceWin's documentation for the list of command line arguments.
Note that you also need to create a configuration file that will define the path to the ``TraceWin`` executables.
See `data/examples/machine_config_file.toml` for an example.

The ``[beam_calculator_post]`` follows the same format.
It is used to store a second :class:`.BeamCalculator`.
This is mainly useful for defining a more precise -- but more time-consuming -- beam dynamics tool, for example to check your compensation settings.
