#!/usr/bin/env python3
"""
Convert lost power of one or several ``patran1.out`` into lost power per meter.

.. todo::
    Sometimes the lost power in first row is 1e-10 or something? Check this out
    when I see it appear again.

.. todo::
    May be included to post-processing from within LightWin directly

"""
import argparse
import re
from pathlib import Path
from typing import Any, Literal, overload

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

COL_Z = "z(m)"
COL_P = "Powlost"
COL_LIN = "Powlost(W/m)"
COL_OUT_P = "Total lost power [W]"
COL_OUT_PLIN = "Maximum linear lost power [W/m]"

definitions_t = Literal["naive", "running_mean", "meter_per_meter"]
DEFINITIONS = {
    "naive": "The lost power per meter is calculated by dividing the power"
    + " column by corresponding delta_z. Usually leads to almost infinite "
    + "lost powers per meter.",
    "running_mean": "The power at z is averaged over z-0.5m and z+0.5m. A "
    + "gaussian weighting function is used so that z has more weight than "
    + "z +/- 0.5 m.",
    "meter_per_meter": "We sum the lost power between 0 and 1m, then 1 and"
    " 2m, etc.",
}


def compute(
    folderpath: Path | str,
    full_project: bool = False,
    z_min: float | None = None,
    z_max: float | None = None,
    definition: definitions_t = "running_mean",
    **kwargs,
) -> None:
    """Compute the lost power per meter for all given file(s).

    Parameters
    ----------
    path : Path | str
        Path to a single ``partran1.out`` file, or to a full LightWin project.
    full_project : bool, optional
        Indicate if the given path is a full project. If True, we take all the
        LightWin out folders in ``path`` with a name like ``000000_ref`` or
        ``000032`` (we look for folders with 6 digits in it). In each one, we
        treat ``1_TraceWin/partran1.out`` file. If False, we try to find
        ``patran1.out`` in ``path/``, ``path/1_TraceWin`` (if ``path`` is not
        already a file). The default is False.
    z_min, z_max : float | None, optional
        If provided, points outside of this range will be filtered out. The
        default is None, in which case all points are kept.
    definitions : definitions_t
        How the lost power should be calculated.

    """
    if not isinstance(folderpath, Path):
        folderpath = Path(folderpath)
    folderpath = folderpath.resolve()

    partran_path = get_partran1_paths(folderpath, full_project, **kwargs)  # type: ignore

    if not full_project:
        _ = _treat_single(
            partran_path,
            z_min=z_min,
            z_max=z_max,
            definition=definition,
            **kwargs,
        )
        return

    _ = _treat_full_project(
        partran_path,
        save_folder=folderpath,
        z_min=z_min,
        z_max=z_max,
        definition=definition,
        **kwargs,
    )


def _treat_single(
    path: Path, z_min: float | None, z_max: float | None, **kwargs: Any
) -> pd.Series:
    """Load the given filepath and compute lost power in W/m."""
    df = pd.read_csv(path, sep=r"\s+", usecols=(COL_Z, COL_P), skiprows=9)  # type: ignore
    _filter_in_range_only(df, z_min, z_max)
    _remove_doublons(df, file=path)
    _add_linear_losses(df, **kwargs)

    ser_info = _check_validity(df)
    _ = _plot_single(df, info=ser_info.to_string(), path=path)
    return ser_info


def _add_linear_losses(
    df: pd.DataFrame,
    definition: definitions_t,
    **kwargs: Any,
) -> None:
    """Add a column holding linear losses in W/m."""
    match definition:
        case "naive":
            df[COL_LIN] = df[COL_P] / df.diff(axis=0)[COL_Z]

        case "running_mean":
            mean_losses = _running_mean(df[COL_Z], df[COL_P])  # type: ignore
            df["running_mean"] = mean_losses
            df[COL_LIN] = mean_losses / df.diff(axis=0)[COL_Z]

        case "meter_per_meter":
            df[COL_LIN] = _meter_per_meter(df[COL_Z], df[COL_P])  # type: ignore

        case _:
            raise ValueError(f"{definition = } not in {DEFINITIONS.keys()}.")


def _remove_doublons(df: pd.DataFrame, file: Path | str | None = None) -> None:
    """Remove positions that are represented twice."""
    n_points = df.shape[0]
    indexes_to_delete = []
    for i in range(n_points - 1):
        if df.loc[i, COL_Z] != df.loc[i + 1, COL_Z]:
            continue

        pow_i = df.loc[i, COL_P]
        pow_j = df.loc[i + 1, COL_P]
        if pow_i != 0.0 or pow_j != 0.0:
            print(
                "warning! lost power at a position represented several times "
                f"in the partran1.out. Check index {i} in {file}."
            )
            df.loc[i + 1, COL_P] += pow_i

        indexes_to_delete.append(i)
    df.drop(index=indexes_to_delete, inplace=True)


def _filter_in_range_only(
    df: pd.DataFrame, z_min: float | None, z_max: float | None
) -> None:
    """Remove the points before ``z_min`` or after ``z_max``."""
    if z_min is not None:
        df.where(df[COL_Z] >= z_min, inplace=True)
    if z_max is not None:
        df.where(df[COL_Z] <= z_max, inplace=True)
    return


def _running_mean(
    position: pd.Series,
    quantity: pd.Series,
    window: float = 1.0,
    sigma: float = 0.5,
) -> list[float]:
    """Provide running_mean of ``quantity`` over a length of ``window``."""
    half_window = 0.5 * window
    running_mean_values = []

    def gauss_weight(distance: np.ndarray, sigma: float) -> np.ndarray:
        """Compute weighter mean over window."""
        return np.exp(-0.5 * (distance / sigma) ** 2)

    for center_pos in position:
        distances = np.abs(position - center_pos)
        weights = gauss_weight(distances, sigma)
        in_window = distances <= half_window

        if in_window.sum() > 0.0:
            weighted_mean = np.average(
                quantity[in_window], weights=weights[in_window]
            )
        else:
            weighted_mean = np.nan
        running_mean_values.append(weighted_mean)

    return running_mean_values


def _meter_per_meter(
    position: pd.Series, quantity: pd.Series, window: float = 1.0
) -> list[float]:
    """Sum lost power between 0 and 1m, between 1 and 2m, etc."""
    if window != 1.0:
        raise ValueError
    n_points = int(position.max()) + 1

    values = []
    for i in range(n_points):
        lower_bound = i * window
        upper_bound = (i + 1) * window
        in_window = (position >= lower_bound) & (position < upper_bound)
        total_in_window = float(quantity[in_window].sum())
        for _ in quantity[in_window]:
            values.append(total_in_window)

    return values


def _treat_full_project(
    paths: dict[str, Path],
    z_min: float | None,
    z_max: float | None,
    save_folder: Path | None = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Load several files and concatenate the lost powers."""
    series = {
        name: _treat_single(path, z_min=z_min, z_max=z_max, **kwargs)
        for name, path in paths.items()
    }
    assert len(series) > 1, "There is not enough objects to concatenate."
    df_info = pd.concat(series, axis=1).T

    if save_folder is not None:
        df_info.to_csv(save_folder / "linear_lost_powers.csv")
    _plot_several(df_info, path=save_folder)

    return df_info


def _get_partran1_filepath(folderpath: Path) -> Path:
    """Look for ``partran1.out`` in ``folderpath`` and subfolders."""
    if folderpath.is_file():
        filepath = folderpath
        return filepath

    folder = folderpath.stem
    if folder == "1_TraceWin":
        filepath = folderpath / "partran1.out"
        assert filepath.is_file(), f"{filepath = } was not found."
        return filepath

    folderpath = folderpath / "1_TraceWin"
    return _get_partran1_filepath(folderpath)


@overload
def get_partran1_paths(
        folderpath: Path, full_project: Literal[True], verbose: bool=False,**kwargs: Any
) -> dict[str, Path]: ...


@overload
def get_partran1_paths(
        folderpath: Path, full_project: Literal[False],verbose:bool=False, **kwargs: Any
) -> Path: ...


def get_partran1_paths(
        folderpath: Path, full_project: bool, verbose:bool=False,**kwargs: Any
) -> Path | dict[str, Path]:
    """Gather the file(s) to treat."""
    if verbose:
        print(f"Looking for files in {folderpath}...")

    if not full_project:
        filepath = _get_partran1_filepath(folderpath)
        if verbose:
            print(f"Study only one file: {filepath}")
        return filepath

    folders: dict[str, Path] = {}
    reg_compile = re.compile(r"\d{6}")
    for folder in folderpath.iterdir():
        if verbose:
            print(f"Inspecting {folder}...")
        if folder.is_file():
            continue

        folder_name = folder.name
        if not reg_compile.match(folder_name):
            if verbose:
                print(f"\tSkipping it as it does not matches pattern.")
            continue

        if verbose:
            print(f"\tGot one matching pattern!")
        filepath =  _get_partran1_filepath(folder)
        folders[folder_name] = filepath
        if verbose:
            print(f"\tFound {filepath = }")

    return folders


def _check_validity(df: pd.DataFrame) -> pd.Series:
    """Print some info to ensure consistency."""
    total_lost = df[COL_P].sum()
    max_lost_per_meter = df[COL_LIN].max()
    data_dict = {
        COL_OUT_P: float(total_lost),
        COL_OUT_PLIN: float(max_lost_per_meter),
    }
    ser_info = pd.Series(data_dict)
    return ser_info


def _plot_single(
    df: pd.DataFrame, info: str | None, path: Path | None = None
) -> Figure:
    """Plot the data for validity checking."""
    plt.close("all")
    axes = df.plot(x=COL_Z, subplots=True, grid=True, title=info)
    fig = axes[0].get_figure()
    if path is None:
        return fig

    fig_path = path.parent / "lost_power.png"
    fig.savefig(fig_path)
    return fig


def _plot_several(df: pd.DataFrame, path: Path | None = None) -> Figure:
    """Concatenate all plots."""
    axes = df.plot(subplots=True, grid=True)
    axes[-1].axhline(y=1.0, ls="--", c="r", label="Upper limit 1W/m")
    for ax in axes:
        ax.legend()
    fig = axes[0].get_figure()
    if path is None:
        return fig

    fig_path = path / "linear_lost_powers.png"
    fig.savefig(fig_path)
    print(f"Figure saved in {fig_path}")
    return fig

def main():
    parser = argparse.ArgumentParser("compute_lost_power_per_meter", formatter_class=argparse.RawTextHelpFormatter,
                                     description="Take one or several ``patran1.out`` file(s) and convert lost power [W] to lost power per meter [W/m].")
    parser.add_argument(
        "-f",
        "--folder",
        help="Folder where to look for partran1.out. Subfolders are inspected "
        + "too.",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-s",
        "--severalfiles",
        help="To tell that several patran1.out are expected.\nIf given, the "
        + "--folder should be the simulation project holding all the "
        + "calculations\n.(This is where ``evaluations.csv``, ``000000_ref/``, "
        + "``000001/``, etc are).",
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "--zmin",
        help="Losses before zmin [m] will not be considered.\nNote for MINERVA studies: use zmin=12.440976.",
        type=float,
        required=False,
    )
    parser.add_argument(
        "--zmax",
        help="Losses after zmax [m] will not be considered.",
        type=float,
        required=False,
    )

    str_defs = "\n".join((f"\t{key}: {value}" for key, value in DEFINITIONS.items()))
    parser.add_argument(
        "-d",
        "--definition",
        help=f"How the power should be averaged.\nAllowed values are:\n{str_defs}",
        type=str,
        choices=DEFINITIONS.keys(),
        required=True,
    )
    parser.add_argument(
            "-v","--verbose",help="To print out more information.",action="store_true",required=False,
            )
    args = parser.parse_args()
    compute(
        args.folder,
        full_project=args.severalfiles,
        z_min=args.zmin,
        z_max=args.zmax,
        definition=args.definition,
        verbose=args.verbose,
    )

if __name__ == "__main__":
    main()
