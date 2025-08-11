.. _TraceWin-compatibility-note:

Compatibility with TraceWin `DAT` files
---------------------------------------

LightWin uses the same format as TraceWin for the linac structure.
As TraceWin developers implemented a significant number of elements and commands, those will be progressively implemented in LightWin too.

"Useless" commands and elements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some instructions will raise a warning, even if they will not influence the results.
As an example, if you use :class:`.Envelope1D`, transverse dynamics are not considered and the fact that transverse field maps are not implemented should not be a problem.

"Useful" commands and elements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You should clean the `DAT` to remove any command that influences the design of the linac.
In particular: `SET_ADV`, `ADJUST` commands.
Warnings may not always appear, so be careful that :class:`.Envelope1D` or :class:`.Envelope3D` results match TraceWin's.
If you choose :class:`.TraceWin` solver for the optimization, both LightWin and TraceWin could modify the design of the linac at the same time, so unexpected side effects may appear.

.. note::
   Since `0.6.21`, `SET_SYNC_PHASE` commands can be kept in the original `DAT`.
   Since `0.8.0b3`, the `SET_SYNC_PHASE` can be exported in the output `DAT` file.

   See also: :meth:`.ListOfElements.store_settings_in_dat` (the method which is actually called to create the `DAT`).

How to implement commands or elements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can implement the desired elements and `git push` them, or file an issue on GitHub and I will try to add the desired element(s) as soon as possible.

.. note::
   Add an example.

.. warning::
   Field maps file formats must be ascii, binary files to handled yet

