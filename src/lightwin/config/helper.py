"""Define utility functions to test out the ``.toml`` config file."""

import functools
import logging
from pathlib import Path
from typing import Any, Literal


def check_type(
    instance: type | tuple[type],
    name: str,
    *args: Any,
) -> None:
    """Raise a warning if ``args`` are not all of type ``instance``.

    Not matching the provided type does not stop the program from running.

    """
    for arg in args:
        if not isinstance(arg, instance):
            logging.warning(f"{name} testing: {arg} should be a {instance}")


def dict_for_pretty_output(some_kw: dict) -> str:
    """Transform a dict in strings for nice output."""
    nice = [f"{key:>52s} = {value}" for key, value in some_kw.items()]
    return "\n".join(nice)


def _find_according_to_nature(
    path: Path, nature: Literal["file", "folder"] | None
) -> bool:
    """Helper function to check if the path matches the desired nature."""
    match nature:
        case "file":
            return path.is_file()
        case "folder":
            return path.is_dir()
        case None:
            return path.exists()
        case _:
            logging.error(
                "f{nature = } not recognized. Considering it's None..."
            )
            return _find_according_to_nature(path, nature=None)


def find_path(
    toml_folder: Path | None,
    path: str | Path,
    nature: Literal["file", "folder"] | None = None,
) -> Path:
    """Look for the given path in all possible places, make it absolute.

    We sequentially check and return the first valid path:
    1. If ``path`` is a ``Path`` object, resolve and check its existence.
    2. If ``path`` exists relative to ``toml_folder``.
    3. If ``path`` is absolute.

    Parameters
    ----------
    toml_folder : pathlib.Path | None
        Folder where the ``.toml`` configuration file is.
    path : str | pathlib.Path
        Path to look for.
    nature : Literal["file", "folder"] | None,  optional
        The type of path to check: "file" or "folder", or None to simply check
        existence.

    Returns
    -------
    path : pathlib.Path
        Absolute path, whose existence has been checked.

    Raises
    ------
    FileNotFoundError :
        Raised if the required path does not exists.

    """

    def path_exists(p: Path) -> bool:
        return _find_according_to_nature(p, nature)

    if isinstance(path, Path):
        updated_path = path.resolve().absolute()
        if path_exists(updated_path):
            return updated_path

    if toml_folder is None:
        msg = (
            "You must provide the location of the toml file to allow for a "
            "more complete path search."
        )
        logging.critical(msg)
        raise FileNotFoundError(msg)

    updated_path = (toml_folder / path).resolve().absolute()
    if path_exists(updated_path):
        return updated_path

    updated_path = Path(path).resolve().absolute()
    if path_exists(updated_path):
        return updated_path

    msg = (
        f"{path = } was not found. It can be defined relative to the .toml "
        "(recommended), absolute, or relative to the execution dir of the "
        f"script (not recommended). Provided {toml_folder = }"
    )
    logging.critical(msg)
    raise FileNotFoundError(msg)


# Define partial functions for finding files and folders
find_file = functools.partial(find_path, nature="file")
find_folder = functools.partial(find_path, nature="folder")
