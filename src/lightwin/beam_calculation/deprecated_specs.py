"""Define monkey patches for deprecated options.

They are common to all :class:`.BeamCalculator`.

"""

import logging
from typing import Any

from lightwin.config.table_spec import TableConfSpec


def apply_deprecated_flag_phi_abs(
    self: TableConfSpec, toml_table: dict[str, Any], **kwargs
) -> None:
    """Update ``reference_phase_policy`` if ``flag_phi_abs`` was given.

    This option is deprecated, but we keep it for compatibility.

    """
    flag_phi_abs = toml_table.get("flag_phi_abs", None)
    if flag_phi_abs is None:
        return

    overriden = toml_table.get("reference_phase_policy", None)
    new = "phi_0_abs" if flag_phi_abs else "phi_0_rel"

    logging.warning(
        "Overriding ``reference_phase_policy`` following (deprecated) "
        f"{flag_phi_abs = }. reference_phase_policy {overriden} -> {new}"
    )
    toml_table["reference_phase_policy"] = new
