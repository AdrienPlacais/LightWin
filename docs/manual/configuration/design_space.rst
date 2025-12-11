``design_space`` section
*************************************
.. toctree::
   :maxdepth: 5

This section parametrizes how the design space will be defined:

- which variables are included,
- their limits and initial values,
- which constraints apply,
- and the limits of those constraints.

All these settings are passed down to :meth:`.DesignSpaceFactory.__init__` as `design_space_kw`.

There are two ways to specify the design space limits and initial values.
The first is to let LightWin calculate them from the nominal linac settings.
This approach is easier to use for initial runs.


.. csv-table::
   :file: entries/design_space_calculated.csv
   :header-rows: 1

.. important::
   The design space defines which variables the optimizer explores.
   If your `design_space_preset` key is set to, for example, `"abs_phase_amplitude"`, the optimization variables are the amplitude :math:`k_e` and the absolute phase :math:`\phi_{0,\,\mathrm{abs}}` of each compensating cavity.
   Consequently, the synchronous phase is not part of the variable set, and the following parameters will have no effect:

   - `max_absolute_sync_phase_in_deg`
   - `min_absolute_sync_phase_in_deg`
   - `max_increase_sync_phase_in_percent`

   To take these parameters into account, you should use the preset `"sync_phase_amplitude"`.
   Please note that this option increases computation time, since LightWin must determine the *physical* phase :math:`\phi_0` corresponding to the target synchronous phase :math:`\phi_s`.
   This value changes whenever the field amplitude or the beam energy at the cavity entrance changes.

When `from_file` is `True`, you must provide a path to a `CSV` file containing, for every element:

- the variables name as header,
- its initial value,
- and its limits.

If the problem is constrained, you must also provide a `CSV` file with, for every element, the limits of each constraint.
This approach is useful when you want to fine-tune the optimisation, as you can manually edit the `CSV` -- for example, to account for multipacting barriers in a problematic cavity.

To generate `CSV` files with the proper format, see `examples/generate_design_space_files.py`.
You can also re-use following files in `data/example`:

- `variables.csv`
- `variables_centered_around_solution.csv`
- `constraints.csv`

.. csv-table::
   :file: entries/design_space_from_file.csv
   :header-rows: 1
