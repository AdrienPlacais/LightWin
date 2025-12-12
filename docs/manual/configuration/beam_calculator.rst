.. _BeamCalculator-configuration-help-page:

``beam_calculator`` section (mandatory)
***************************************
.. toctree::
   :maxdepth: 5


Note that the role of the `reference_phase_policy` is extremely important, as it controls how cavities are rephased after failure.
More details and an example in the :ref:`dedicated notebook<notebooks-cavities-reference-phase>`.

:class:`.Envelope1D` solver
===========================

This solver computes the propagation of the beam in the longitudinal phase space and in envelope.
Space charge effects are not considered.
It is adapted to high energy problems, such as ADS linacs.

.. csv-table::
   :file: entries/beam_calculator_envelope_1d.csv
   :header-rows: 1

The following elements are explicitly supported.
Note that, by default, an element that is implemented but not explicitly supported is replaced by a `DRIFT`.
In 1D, this is perfectly acceptable for most non-implemented elements that act on the transverse dynamics, such as `THIN_LENS`.

.. configkeys:: lightwin.beam_calculation.envelope_1d.element_envelope1d_parameters_factory.PARAMETERS_1D
   :n_cols: 3

:class:`.Envelope3D` solver
===========================

Envelope solver in 3D, without space charge.

.. csv-table::
   :file: entries/beam_calculator_envelope_3d.csv
   :header-rows: 1

.. note::

   As transverse effects are generally not predominant, I do not use this solver very often and a lot of elements are not implemented.
   The current list of explicitly supported elements is:

   .. configkeys:: lightwin.beam_calculation.envelope_3d.element_envelope3d_parameters_factory.PARAMETERS_3D
     :n_cols: 2

  The default behavior when an element in the input `DAT` file is not recognized, is to issue a warning and replace this element by a `DRIFT`.

  Do not hesitate to file an |issue|_ if you need me to implement some elements.

:class:`.TraceWin` solver
===========================

3D solver, can be used in multiparticle or envelope.
You will need a valid TraceWin license.
It can be used during the optimization process, though this approach relies on a lot of file writing/reading and is very slow.
Generally, I use it to re-compute the propagation of the beam in the linac when compensation settings were found (`beam_calculator_post`).

.. csv-table::
   :file: entries/beam_calculator_tracewin.csv
   :header-rows: 1

Check TraceWin's documentation for the list of command line arguments.
Note that you also need to create a configuration file that will define the path to the ``TraceWin`` executables.
See `data/examples/machine_config_file.toml` for an example.

The ``[beam_calculator_post]`` follows the same format.
It is used to store a second :class:`.BeamCalculator`.
This is mainly useful for defining a more precise -- but more time-consuming -- beam dynamics tool, for example to check your compensation settings.
