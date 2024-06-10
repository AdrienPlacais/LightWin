"""Define functions used by the field maps."""

from pathlib import Path


def set_full_field_map_path(
    field_map_folder: Path,
    field_map_filename: str,
    extensions: dict[str, list[str]],
) -> list[Path]:
    """Set all the full field map file names with extension."""
    field_map_file_names = [
        Path(field_map_folder, field_map_filename).with_suffix("." + ext)
        for extension in extensions.values()
        for ext in extension
    ]
    return field_map_file_names
