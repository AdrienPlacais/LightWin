#!/usr/bin/env python3
"""Generate the files used by LightWin to generate the design space.

.. todo::
    maybe show what the file should look like?

"""
import os.path
from pathlib import Path

from lightwin.beam_calculation.factory import BeamCalculatorsFactory
from lightwin.config_manager import process_config
from lightwin.core.accelerator.factory import (
    StudyWithoutFaultsAcceleratorFactory,
)
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.optimisation.design_space.design_space import DesignSpace
from lightwin.optimisation.design_space.factory import get_design_space_factory


def main() -> None:
    # =========================================================================
    # Set up the accelerator
    # =========================================================================
    toml_filepath = Path("lightwin.toml")
    toml_keys = {
        "files": "files",
        "beam": "beam",
        "beam_calculator": "generic_envelope1d",
        "design_space": "design_space_to_generate_files",
    }
    configuration = process_config(toml_filepath, toml_keys)

    # =========================================================================
    # Beam calculators
    # =========================================================================
    beam_calculator_factory = BeamCalculatorsFactory(**configuration)
    beam_calculator = beam_calculator_factory.run_all()[0]

    # =========================================================================
    # Accelerators
    # =========================================================================
    accelerator_factory = StudyWithoutFaultsAcceleratorFactory(
        beam_calculator=beam_calculator,
        **configuration["files"],
    )
    accelerator = accelerator_factory.run()

    # =========================================================================
    # Compute propagation of the beam
    # =========================================================================
    beam_calculator.compute(accelerator)

    # Take only the FieldMap objects
    cavities: list[FieldMap] = accelerator.elts.l_cav
    elements_to_put_in_file = cavities

    # =========================================================================
    # Set up generic Variable, Constraint objects
    # =========================================================================
    if configuration["design_space"]["design_space_preset"] != "everything":
        print(
            "Warning! Modifying the design_space_preset entry to have all "
            "the possible variables and constraints in the output file."
        )
        configuration["design_space"]["design_space_preset"] = "everything"

    design_space_factory = get_design_space_factory(
        **configuration["design_space"]
    )
    design_space = design_space_factory.run(
        elements_to_put_in_file, elements_to_put_in_file
    )

    design_space.to_files(
        basepath=Path("./"),
        variables_filename="variables",
        constraints_filename="constraints",
        overwrite=True,
    )
    variables_filepath = Path("variables.csv")
    constraints_filepath = Path("constraints.csv")

    # Now try to create a DesignSpace from the files
    design_space = DesignSpace.from_files(
        ("FM4", "FM5"), variables_filepath, ("k_e", "phi_0_abs"), None, None
    )


if __name__ == "__main__":
    main()
