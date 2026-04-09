#!/usr/bin/env python3
"""Generate the files used by LightWin to generate the design space.

.. todo::
    maybe show what the file should look like?

"""

from pathlib import Path

from lightwin.config.config_manager import process_config
from lightwin.optimisation.design_space.design_space import DesignSpace
from lightwin.optimisation.design_space.factory import (
    DesignSpaceFactory,
    get_design_space_factory,
)
from lightwin.ui.workflow_setup import set_up


def main() -> None:
    # =========================================================================
    # Set up the accelerator
    # =========================================================================
    toml_filepath = Path("lightwin.toml")
    toml_keys = {
        "files": "files",
        "beam": "beam",
        "beam_calculator": "envelope1d",
        "design_space": "design_space_to_generate_files",
    }
    config = process_config(toml_filepath, toml_keys)

    _, accelerators, _, _ = set_up(config)
    field_maps = accelerators[0][0].elts.l_cav

    design_space_kw = config.get("design_space")
    if design_space_kw is None:
        raise ValueError("missing 'design_space' key")

    design_space_factory = get_design_space_factory(**design_space_kw)
    design_space = design_space_factory.create(field_maps, field_maps)
    design_space.to_files(
        basepath=Path("./"),
        variables_filename="variables",
        constraints_filename="constraints",
        overwrite=True,
    )
    # variables_filepath = Path("variables.csv")
    # constraints_filepath = Path("constraints.csv")
    #
    # # Now try to create a DesignSpace from the files
    # design_space_kw = DesignSpace.from_files(
    #     ("FM4", "FM5"), variables_filepath, ("k_e", "phi_0_abs"), None, None
    # )


if __name__ == "__main__":
    main()
