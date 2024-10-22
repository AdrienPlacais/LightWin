"""Define parameters necessary to define files.

.. note::
    We define custom :class:`.TableConfSpec` class in order to also set up the
    folder to store results and the logging tool.

"""

import datetime
import logging
from pathlib import Path
from typing import Any, Literal

from lightwin.constants import example_dat, example_folder
from lightwin.new_config.key_val_conf_spec import KeyValConfSpec
from lightwin.new_config.table_spec import TableConfSpec
from lightwin.util.log_manager import set_up_logging

FILES_CONFIG = (
    KeyValConfSpec(
        key="dat_file",
        types=(str, Path),
        description="Path to the ``.dat`` file",
        default_value=example_dat,
        is_a_path_that_must_exists=True,
    ),
    KeyValConfSpec(
        key="logfile_console_level",
        types=(str,),
        description="Level of messages written in console",
        default_value="INFO",
        is_mandatory=False,
        allowed_values=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
    ),
    KeyValConfSpec(
        key="logfile_file",
        types=(str,),
        description="Name of the file where the logging output will be written",
        default_value="lightwin.log",
        is_mandatory=False,
    ),
    KeyValConfSpec(
        key="logfile_log_level",
        types=(str,),
        description="Level of messages written in logfile",
        default_value="INFO",
        is_mandatory=False,
        allowed_values=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
    ),
    KeyValConfSpec(
        key="project_folder",
        types=(str, Path),
        description="Where output results will be stored",
        default_value=example_folder / "results/",
        is_mandatory=False,
    ),
)


class FilesTableConfSpec(TableConfSpec):
    """Override the default table to add logging and results folder set up."""

    def _pre_treat(self, toml_subdict: dict[str, Any], **kwargs) -> None:
        """Set up the logging as well as the results folder.

        .. note::
            The ``toml_folder`` required by ``_create_project_folders`` is in
            the ``kwargs``.

        """
        project_path = _create_project_folders(**kwargs, **toml_subdict)
        _set_up_logging(project_path=project_path, **toml_subdict)

    def validate(self, toml_subdict: dict[str, Any], **kwargs) -> bool:
        """Insert the pre-treat methd before validation."""
        self._pre_treat(toml_subdict=toml_subdict, **kwargs)
        return super().validate(toml_subdict, **kwargs)


def _set_up_logging(
    project_path: Path,
    log_file: str = "lightwin.log",
    logfile_log_level: Literal[
        "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    ] = "INFO",
    console_log_level: Literal[
        "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    ] = "INFO",
    **toml_subdict,
) -> None:
    """Set up the logging."""
    logfile_file = project_path / log_file
    set_up_logging(
        logfile_file=logfile_file,
        logfile_log_level=logfile_log_level,
        console_log_level=console_log_level,
    )
    logging.info(f"Setting {project_path = }\nSetting {log_file = }")


def _create_project_folders(
    toml_folder: Path,
    project_folder: str | Path = "",
    **toml_subdict,
) -> Path:
    """Create a folder to store outputs and log messages."""
    project_path, exist_ok = _set_project_path(toml_folder, project_folder)
    project_path.mkdir(exist_ok=exist_ok)
    return project_path.absolute()


def _set_project_path(
    toml_folder: Path, project_folder: str | Path = ""
) -> tuple[Path, bool]:
    """Create a default project folder name if not given."""
    if isinstance(project_folder, Path):
        project_path = project_folder.resolve().absolute()
        exist_ok = True
        return project_path, exist_ok

    if project_folder:
        project_path = (toml_folder / project_folder).resolve()
        exist_ok = True
        return project_path, exist_ok

    time = datetime.datetime.now().strftime("%Y.%m.%d_%Hh%M_%Ss_%fms")
    project_path = toml_folder / time
    exist_ok = False
    return project_path, exist_ok
