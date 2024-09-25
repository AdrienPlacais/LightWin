TraceWin (facultative)
----------------------

**Pre-requisite**: TraceWin must be installed on your computer or server, and you must have a valid license.

Configuring the `machine_configuration.toml` file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To specify the location of the TraceWin installation, you need to create `machine_configuration.toml` file.
This file should include entries like the following:

.. code-block:: toml

   [lpsc5057x]
   noX11_full = "/usr/local/bin/TraceWin/./TraceWin_noX11"
   noX11_minimal = "/home/placais/TraceWin/exe/./tracelx64"
   no_run = ""
   X11_full = "/usr/bin/local/bin/TraceWin/./TraceWin"

   [LPSC5011W]
   X11_full = "D:/tw/TraceWin.exe"
   noX11_full = "D:/tw/TraceWin.exe"

   [a_name_to_override_default_machine_name]
   X11_full = "D:/tw/TraceWin_old.exe"
   noX11_full = "D:/tw/TraceWin_old.exe"

Replace the bracketed names with your machine's name.
If you're unsure of your machine's name, use the following Python code to find it:

.. code-block:: python

   import socket
   machine_name = socket.gethostname()
   print(f"Entry in the machine_configuration.toml file should be:\n[{machine_name}]")

Linking with the `lightwin.toml` main configuration file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After setting up `machine_configuration.toml`, you need to link it with the `lightwin.toml` file.
Include the following configuration:

.. code-block:: toml

   [my_tracewin_configuration]
   # Can be relative to `lightwin.toml`, or absolute:
   machine_config_file = "/path/to/machine_configuration.toml"
   # The corresponding path must be defined in `machine_configuration.toml`
   simulation_type = "X11_full"
   # Optional: override the actual machine name if provided:
   machine_name = "a_name_to_override_default_machine_name"
   # Note that additional entries will be required

For the full configuration of `lightwin.toml`, look at the :ref:`dedicated documentation<BeamCalculator-configuration-help-page>`
