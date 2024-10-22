#!/usr/bin/env python3
import csv
from collections.abc import Sequence
from pathlib import Path

from lightwin.beam_calculation.envelope_1d.specs import ENVELOPE1D_CONFIG
from lightwin.beam_calculation.envelope_3d.specs import ENVELOPE3D_CONFIG
from lightwin.beam_calculation.tracewin.specs import TRACEWIN_CONFIG
from lightwin.config.key_val_conf_spec import KeyValConfSpec
from lightwin.constants import doc_folder
from lightwin.core.beam_specs import BEAM_CONFIG
from lightwin.core.files_specs import FILES_CONFIG
from lightwin.evaluator.specs import EVALUATORS_CONFIG
from lightwin.optimisation.design_space_specs import (
    DESIGN_SPACE_CALCULATED,
    DESIGN_SPACE_FROM_FILE,
)
from lightwin.optimisation.wtf_specs import (
    WTF_CONFIGS,
    WTF_K_OUT_OF_N,
    WTF_L_NEIGHBORING_LATTICES,
    WTF_MANUAL,
)
from lightwin.visualization.specs import PLOTS_CONFIG


def write_specs_to_csv(
    specs_list: Sequence[KeyValConfSpec], output_file: Path
) -> None:
    """Write a list of :class:`.KeyValConfSpec` objects to a CSV file.

    Parameters
    ----------
    specs_list : Sequence[KeyValConfSpec]
        List of :class:`.KeyValConfSpec` objects.
    output_file : Path
        Path to the output CSV file.

    """
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            ["Entry", "Type", "Description", "Allowed values", "Mandatory?"]
        )

        for spec in specs_list:
            line = spec.to_csv_line()
            if line is None:
                continue
            writer.writerow(line)


def main() -> None:
    """Generate all the necessary CSV files."""
    output_dir = doc_folder / "configuration_entries"

    files: dict[str, Sequence[KeyValConfSpec]]
    files = {
        # "beam": BEAM_CONFIG,
        # "beam_calculator_envelope_1d": ENVELOPE1D_CONFIG,
        # "beam_calculator_envelope_3d": ENVELOPE3D_CONFIG,
        # "beam_calculator_tracewin": TRACEWIN_CONFIG,
        # "design_space_calculated": DESIGN_SPACE_CALCULATED,
        # "design_space_from_file": DESIGN_SPACE_FROM_FILE,
        # "evaluator": EVALUATORS_CONFIG,
        # "files": FILES_CONFIG,
        # "plots": PLOTS_CONFIG,
        "wtf_k_out_of_n": WTF_K_OUT_OF_N,
        # "wtf_manual": WTF_MANUAL,
        # "wtf_l_neigboring_lattices": WTF_L_NEIGHBORING_LATTICES,
    }

    for specs_list, config in files.items():
        write_specs_to_csv(
            specs_list=config,
            output_file=(output_dir / specs_list).with_suffix(".csv"),
        )


if __name__ == "__main__":
    main()
