.. _TraceWin-compatibility-note:

Compatibility with TraceWin `.dat` files
----------------------------------------

LightWin uses the same format as TraceWin for the linac structure.
As TraceWin developers implemented a significant number of elements and commands, those will be progressively implemented in LightWin too.

"Useless" commands and elements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some instructions will raise a warning, even if they will not influence the results.
As an example, if you use :class:`.Envelope1D`, transverse dynamics are not considered and the fact that transverse field maps are not implemented should not be a problem.

"Useful" commands and elements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You should clean the `.dat` to remove any command that influences the design of the linac.
In particular: `SET_ADV`, `SET_SYNC_PHASE`, `ADJUST` commands.
Warnings may not always appear, so be careful that :class:`.Envelope1D` or :class:`.Envelope3D` match with TraceWin.
If you choose :class:`.TraceWin` solver for the optimization, both LightWin and TraceWin could modify the design of the linac at the same time, so unexpected side effects may appear.

.. note::
   Since `0.6.21`, `SET_SYNC_PHASE` commands can be kept in the original `.dat`.
   The output `.dat` will contain relative or absolute phase, according to the corresponding :attr:`.BeamCalculator.reference_phase`.
   In the future, it will be possible to export `.dat` with `SET_SYNC_PHASE` for all cavities, or to keep the phase definitions of the original `.dat`.

   See also: :meth:`.ListOfElements.store_settings_in_dat` (the method which is actually called to create the `.dat`).

How to implement commands or elements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can implement the desired elements and `git push` them, file an issue on GitHub and I will try to add the desired element(s) as soon as possible.

.. note::
   Add an example.

.. warning::
   Field maps file formats must be ascii, binary files to handled yet

