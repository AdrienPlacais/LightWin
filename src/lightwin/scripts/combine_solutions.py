#!/usr/bin/env python3
"""Take the best compensation settings among several runs.

Basic usage:
``./combine_solutions.py -d /path/to/sim1/ /path/to/sim2/ /path/to/sim3``

This is useful when different strategies are best on different fault scenarios.

The compensation settings are sorted against a column in the
``evaluations.csv`` files.

Reminder on the directory structure and conventions:
    
simulation_1            <- project folder
    | 000000_ref        <- simulation folder (holds a fault scenario)
        | 0_Envelope1D
        | 1_TraceWin
    | 000001
        | 0_Envelope1D
        | 1_TraceWin
    | ...
    | evaluations.csv
simulation_2
    | 000000_ref
    | 000001
    | ...


"""
import argparse
import os
import shutil
from collections.abc import Collection, Sequence
from pathlib import Path

import pandas as pd


def combine_bests(
    paths: Sequence[Path | str],
    criterion_to_minimize: str = "Lost power over whole linac in W.",
    out_folder: Path | str = "",
    copy: bool = False,
) -> None:
    """Compare several solutions, and concatenate the best one.

    To determine the best solution for every fault scenario, we open each
    simulation's ``evaluations.csv``, look at the value of the column
    ``criterion_to_minimize`` and keep the simulation with the lowest.

    Parameters
    ----------
    paths : Sequence[Path]
        Project folders (where ``evaluations.csv`` and every simulation is).
    criterion_to_minimize : str, optional
        The ``evaluations.csv`` column against which simulations are compared.
        The default is ``"Lost power over whole linac in W."`` (we keep
        simulations with the lowest lost power).
    out_folder : Path | str, optional
        Where every best simulation folder will be gathered. If not provided,
        we create a ``combined/`` folder in the last common ancestor of all
        provided paths.
    copy : bool, optional
        To create hard-copies of the original simulation folders instead of
        creating a symlink. The default is False.

    """
    paths = [Path(p).resolve() if isinstance(p, str) else p for p in paths]
    best_simulation_folders, combined = _select_best_simulations(
        paths, criterion_to_minimize=criterion_to_minimize
    )

    if not out_folder:
        out_folder = _infer_an_output_folder(paths)
    if isinstance(out_folder, str):
        out_folder = Path(out_folder)
    if not out_folder.is_dir():
        os.mkdir(out_folder)

    combined.to_csv(out_folder / "evaluations.csv", sep=",")

    _gather_best_simulations_in_same_place(
        best_simulation_folders,
        out_folder,
        create_symlinks_instead_of_hard_copies=not copy,
    )


def _infer_an_output_folder(
    paths: Sequence[Path], output_folder_name: str = "combined"
) -> Path:
    """Return output folder in the last common parent of ``paths``."""
    assert len(paths) > 0
    common_parent = paths[0].parts
    for path in paths[1:]:
        common_parent = [
            part
            for part, other_part in zip(common_parent, Path(path).parts)
            if part == other_part
        ]
    output_path = Path(*common_parent) / output_folder_name
    if not output_path.exists():
        output_path.mkdir()
    return output_path


def _select_best_simulations(
    paths: Sequence[Path],
    criterion_to_minimize: str,
) -> tuple[pd.Series, pd.DataFrame]:
    """Give the name of the best solution according to ``criterion_to_minimize``

    Parameters
    ----------
    paths : Sequence[Path]
        Path to project folders to be compared.
    criterion_to_minimize : str
        The quantity that we want to minimize. It must be a column name in
        ``evaluations.csv``.

    Returns
    -------
    best_simulation_folders : pd.Series
        For each fault scenario, holds the path to the best simulation folder.
    combined : pandas.DataFrame
        A ``evaluations.csv`` where each row holds the values for the best
        simulation. You must ensure that all ``evaluations.csv`` have the same
        columns.

    """
    all_df = [
        _load_evaluation(
            simulation_folder,
            evaluation_namecol=(criterion_to_minimize,),
            new_name=(str(simulation_folder),),
        )
        for simulation_folder in paths
    ]
    criterion_values = pd.concat(all_df, axis=1)
    best_simulations = criterion_values.idxmin(axis=1)
    best_simulations.name = "best simulation project folder"

    n_simulations = len(all_df[0])
    folder_names = _reconstruct_folder_names(n_simulations)
    criterion_values = pd.concat((best_simulations, folder_names), axis=1)

    best_simulation_folders = [
        Path(best_sim) / folder_name
        for best_sim, folder_name in zip(best_simulations, folder_names)
    ]

    all_df = {
        simulation_folder: _load_evaluation(simulation_folder)
        for simulation_folder in paths
    }
    combined = _concat_evaluations_files(all_df, best_simulations)

    return best_simulation_folders, combined


def _reconstruct_folder_names(n_simulations: int) -> pd.Series:
    """Reconstruct the name of the simulation folders."""
    folders = [f"{i:06d}" for i in range(n_simulations)]
    folders[0] += "_ref"
    return pd.Series(folders, name="simulation_folder")


def _concat_evaluations_files(
    evaluations: dict[str, pd.DataFrame],
    best_solutions: Sequence[Path],
) -> pd.DataFrame:
    """Concatenate the evaluations, taking only the best.

    Parameters
    ----------
    evaluations : dict[str, pandas.DataFrame]
        Keys are user-defined names for every simulation. Values are
        corresponding ``evaluations.csv`` files; their columns must be the
        same. They must have the same indexes.
    best_solutions : Sequence[str]
        For every calculation, defines the ``evaluation`` we want to keep.
        The lenght must be the same as the length of every object in
        ``evaluations``. Contained strings must all be keys of ``evaluations``.

    Returns
    -------
    combined : pandas.DataFrame
        Same columns as ``evaluations``. Every row contains the
        ``evaluations.csv`` row of the best solution.

    """
    best_evaluation_dfs = []

    for i, solution in enumerate(best_solutions):
        solution = Path(solution)
        if solution not in evaluations:
            raise ValueError(
                f"The solution '{solution}' is not found in evaluations."
            )

        best_line = evaluations[solution].iloc[i]
        best_evaluation_dfs.append(best_line)

    combined = pd.concat(best_evaluation_dfs, axis=1).T
    combined["best solutions"] = best_solutions

    return combined


def _gather_best_simulations_in_same_place(
    best_simulation_folders: Collection[Path],
    out_folder: Path,
    create_symlinks_instead_of_hard_copies: bool,
    dirs_exist_ok: bool = True,
) -> None:
    """Concatenate the best simulation folders in a single place."""
    for folder in best_simulation_folders:
        dst = out_folder / folder.name
        _copy_or_create_symlink(
            folder,
            dst,
            create_symlinks_instead_of_hard_copies=create_symlinks_instead_of_hard_copies,
            dirs_exist_ok=dirs_exist_ok,
        )


def _copy_or_create_symlink(
    src: Path,
    dst: Path,
    create_symlinks_instead_of_hard_copies: bool,
    dirs_exist_ok: bool,
) -> None:
    """Copy ``src`` to ``dst`` or create symlinks."""
    if dst.exists():
        if not dirs_exist_ok:
            raise FileExistsError(f"Directory {dst} already exists.")
        if dst.is_symlink():
            os.unlink(dst)
        else:
            shutil.rmtree(dst)

    if not create_symlinks_instead_of_hard_copies:
        shutil.copytree(src, dst, dirs_exist_ok=dirs_exist_ok)
        return
    os.symlink(src, dst, target_is_directory=True)


def _load_evaluation(
    evaluation_folder: Path,
    evaluation_namecol: Sequence[str] | None = None,
    new_name: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Load the file and rename column header.

    Parameters
    ----------
    evaluation_folder : Path
        Folder where the ``evaluations.csv`` file is.
    evaluation_namecol : Sequence[str] | None, optional
        Name of the column in the ``evaluations.csv`` for the sorting; if not
        provided, we keep all the columns. The default is None.
    new_name : Sequence[str] | None, optional
        If provided, the loaded columns will be renamed with this. The length
        of ``new_name`` must match ``evaluation_namecol``.

    Returns
    -------
    pandas.DataFrame
        Holds all the values of ``evaluation_namecol`` in ``evaluation_path``.

    """
    df = pd.read_csv(
        evaluation_folder / "evaluations.csv",
        # usecols=evaluation_namecol  # type: ignore
    )
    df.columns = df.columns.str.trip()
    df = df[[evaluation_namecol]]

    if new_name is not None:
        assert evaluation_namecol is not None
        assert len(new_name) == len(evaluation_namecol)
        new_names = {
            original_col: new
            for original_col, new in zip(
                evaluation_namecol, new_name, strict=True
            )
        }
        df.rename(columns=new_names, inplace=True)
    return df


def main():
    parser = argparse.ArgumentParser("combine_solutions")

    parser.add_argument(
        "-m",
        "--minimize",
        help="Column we want to minimize in the different evaluations.csv. If "
        + " not provided, we minimize 'Lost power over whole linac in W.'.",
        type=str,
        required=False,
        default="Lost power over whole linac in W.",
    )
    parser.add_argument(
        "-o",
        "--outfolder",
        help="Where the resulting evaluations.csv and corresponding simulation"
        + " folders should be stored. If not provided, we create a 'combined' "
        + "folder in the closest ancestor of all provided simulation folders.",
        type=str,
        required=False,
        default="",
    )
    parser.add_argument(
        "-c",
        "--copy",
        help="Flag to copy the whole simulation folders instead of symlinking "
        + "them.",
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "-d",
        "--dirs",
        help="The project folders to compare. They are the folders "
        + "holding the `evaluations.csv` as well as the `000000_ref`, `000001`"
        + ", etc folders.",
        required=True,
        nargs="+",
    )

    args = parser.parse_args()
    combine_bests(
        paths=args.dirs,
        criterion_to_minimize=args.minimize,
        out_folder=args.outfolder,
        copy=args.copy,
    )


if __name__ == "__main__":
    main()
