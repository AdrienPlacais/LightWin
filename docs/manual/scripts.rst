Utility scripts
===============

.. toctree::
   :maxdepth: 5
   :hidden:

LightWin includes several utility scripts located in the `LightWin/scripts/` folder.
They are scripts that I developed for my own usage, but did not directly belong to the LightWin library.

List of scripts
---------------
* `combine_solutions`: 
  This script merges the best compensation settings from various project folders.
  It is useful for testing different methods across multiple cavities and compiling the optimal settings in a single directory.

* `compute_lost_power_per_meter`:
  Takes one or several ``patran1.out`` produced by TraceWin and compute the lost power per meter from the lost power in W.

* `compare_beam_calculators`: 
  Compares results from two different :class:`.BeamCalculator` classes, such as :class:`.TraceWin` and :class:`.Envelope1D`, to determine if the latter is sufficiently accurate for your needs.

* `generate_design_space_files`: 
  Generates `variables.csv` and `constraints.csv` files, which specify the limits and initial values for phase, synchronous phase, and amplitude for each cavity.
  This is particularly useful for customizing the design space, *e.g.* updating the maximum amplitude in a cavity producing field emission.

* `reorder_output_figures`: 
  Gathers figures produced by LightWin from the simulation folders into a single `images` directory for easier access and review.

* `save_cavity_settings`: 
  Provides examples for saving compensation settings in a specified format, which can be helpful for standardizing outputs across different projects.

Scripts without a CLI
---------------------
Currently, the following scripts do not have a Command-Line Interface (CLI) and require manual editing before use:

* `compare_beam_calculators`
* `generate_design_space_files`
* `save_cavity_settings`

To use these scripts, edit them according to your needs (it's recommended to work on a copy to preserve the original) and run them in your Python interpreter.
Future versions aim to provide CLI functionality for all scripts.

Scripts with a CLI
------------------
The following scripts are equipped with a CLI, allowing them to be executed directly from the command line.
They can be called from everywhere in your system:

* `lw-combine-solutions`
* `lw-compute-lost-power-per-meter`
* `lw-reorder-output-figures`

1. **View available options**:
   Each script comes with its own set of options.
   To view them, use the `--help` flag:
    
   .. code-block:: bash

      ./lw-script-name --help

2. **Execute the script**:
   Run it with the desired arguments:

   .. code-block:: bash
   
      ./lw-script-name --arg1 <val1> --arg2 <val2>

.. note::
   Preliminary steps are mandatory if you installed LightWin with conda:

   1. **Set execution permissions** (if the script does not already have execution permission):

      * Unix (Linux/macOS): use the following command:

      .. code-block:: bash

         chmod +x /path/to/the/script.py

      * Windows: Set the execution rights via the "Properties" menu of the script file.

      This allows you to run the script with `./my_script.py` instead of `python my_script.py`.
         
   2. **Adding Scripts to PATH**:
   To run the scripts from any location on your system, add the `/path/to/lightwin/scripts/` directory to your system `PATH`.

