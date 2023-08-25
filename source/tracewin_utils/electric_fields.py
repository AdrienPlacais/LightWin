#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 17 15:52:37 2022.

@author: placais

This module holds all the functions to handle TraceWin electric field files.

"""
import logging
import os.path
from typing import Callable
import pandas as pd
import numpy as np

import config_manager as con
from core.elements.element import Element
from core.elements.field_map import FieldMap
import tracewin_utils.load


try:
    import beam_calculation.envelope_1d.transfer_matrices_c as tm_c
except ModuleNotFoundError:
    MESSAGE = 'Cython module not compilated. Check elements.py and setup.py'\
        + ' for more information.'
    if con.FLAG_CYTHON:
        raise ModuleNotFoundError(MESSAGE)
    logging.warning(MESSAGE)
    # Load Python version as Cython to allow the execution of the code.
    import beam_calculation.envelope_1d.transfer_matrices_p as tm_c


# TODO is it necessary to load all the electric fields when _p?
def set_all_electric_field_maps(field_map_folder: str,
                                sections: list[list[Element]]) -> None:
    """
    Load all the filemaps.

    Parameters
    ----------
    field_map_folder : str
        Path to the folder where the electric field files are stored.
    sections : list[list[Element]]
        List of sections containing lattices containing `Element` objects.

    """
    filepaths = []
    for i, section in enumerate(sections):
        for lattice in section:
            for elt in lattice:
                if elt.get('nature') == 'FIELD_MAP':
                    elt.field_map_file_name = os.path.join(
                        field_map_folder,
                        elt.field_map_file_name
                    )
                    a_f = elt.acc_field
                    a_f.e_spat, a_f.n_z = _get_single_electric_field_map(elt)

                    # For Cython, we need one filepath per section
                    if con.FLAG_CYTHON and len(filepaths) == i:
                        filepaths.append(elt.field_map_file_name)

    if con.FLAG_CYTHON:
        tm_c.init_arrays(filepaths)


def _get_single_electric_field_map(
    cav: FieldMap) -> tuple[Callable[[float | np.ndarray], float | np.ndarray],
                            int]:
    """
    Select the field map file and call the proper loading function.

    Warning, `filename` is directly extracted from the `.dat` file used by
    TraceWin. Thus, the relative filepath may be misunderstood by this script.

    Also check that the extension of the file is `.edz`, or manually change
    this function.

    Only 1D electric field map are implemented.

    """
    # FIXME
    cav.field_map_file_name += ".edz"
    assert tracewin_utils.load.is_loadable(
        cav.field_map_file_name, cav.geometry, cav.aperture_flag), \
        f"Error preparing {cav}'s field map."

    _, extension = os.path.splitext(cav.field_map_file_name)
    import_function = tracewin_utils.load.FIELD_MAP_LOADERS[extension]

    n_z, zmax, norm, f_z = import_function(cav.field_map_file_name)
    assert _is_a_valid_electric_field(n_z, zmax, norm, f_z, cav.length_m), \
        f"Error loading {cav}'s field map."

    z_cavity_array = np.linspace(0., zmax, n_z + 1) / norm

    def e_spat(pos: float | np.ndarray) -> float | np.ndarray:
        return np.interp(x=pos, xp=z_cavity_array, fp=f_z, left=0., right=0.)

    return e_spat, n_z


def _is_a_valid_electric_field(n_z: int, zmax: float, norm: float,
                              f_z: np.ndarray, cavity_length: float) -> bool:
    """Assert that the electric field that we loaded is valid."""
    if f_z.shape[0] != n_z + 1:
        logging.error(f"The electric field file should have {n_z + 1} "
                      + f"lines, but it is {f_z.shape[0]} lines long. ")
        return False

    tolerance = 1e-6
    if abs(zmax - cavity_length) > tolerance:
        logging.error(f"Mismatch between the length of the field map {zmax = }"
                      + f" and {cavity_length = }.")
        return False

    if abs(norm - 1.) > tolerance:
        logging.warning("Field map scaling factor (second line of the file) "
                        " is different from unity. It may enter in conflict "
                        + "with k_e (6th argument of FIELD_MAP in the .dat).")
    return True


def geom_to_field_map_type(geom: int,
                           remove_no_field: bool = True
                           ) -> dict[str, str]:
    """
    Determine the field map type from TW ``geom`` parameter.

    Notes
    -----
    Last compatibility check: TraceWin v2.22.1.0

    """
    figures = [int(i) for i in str(abs(geom))]
    field_types = ('static electric field',
                   'static magnetic field',
                   'RF electric field',
                   'RF magnetic field',
                   '3D aperture map')
    field_geometries = {
        0: 'no field',
        1: '1D: F(z)',
        2: 'not available',
        3: 'not available',
        4: '2D cylindrical static or RF electric field',
        5: '2D cylindrical static or RF magnetic field',
        6: '2D cartesian field',
        7: '3D cartesian field',
        8: '3D cylindrical field',
        9: '1D: G(z)',
    }
    out = {field_type: field_geometries[figure]
           for figure, field_type in zip(figures, field_types)}
    if 'not available' in out.values():
        logging.warning("At least one invalid field geometry was given in the "
                        ".dat.")
    if not remove_no_field:
        return out

    for key in out:
        if key == 0:
            del out[key]
    return out


def file_map_extensions(field_map_type: dict[str, str]
                        ) -> dict[str, list[str]]:
    """
    Get the proper field map extensions.

    Parameters
    ----------
    field_map_type : dict[str, str]
        Dictionary which keys are the type of electromagnetic field, and values
        are the geometry.

    Returns
    -------
    extensions : dict[str, list[str]]
        Dictionary with the same keys as input. The values are lists containing
        all the extensions of the files to load (no "." in front of extension).

    Notes
    -----
    Last compatibility check: TraceWin v2.22.1.0

    """
    extensions = {field_type: None
                  for field_type in field_map_type}

    char_1 = {'electric': 'e', 'magnetic': 'b'}
    char_2 = {'static': 's', 'RF': 'd'}
    char_3 = {'1D:': ['z'],
              '2D cylindrical': ['r', 'z', 'q'],
              '2D cartesian': ['x', 'y'],
              '3D cartesian': ['x', 'y', 'z'],
              '3D cylindrical': ['r', 'q', 'z']
              }

    for field_type, geometry in field_map_type.items():
        if geometry == 'not available':
            continue

        if field_type == '3D aperture map':
            extensions[field_type] = ['ouv']
            continue

        splitted = field_type.split(' ')
        base_extension = [char_1.get(splitted[1], None),
                          char_2.get(splitted[0], None)]

        geometry_as_a_key = geometry.split(' ')
        if geometry_as_a_key[0] == '1D:':
            geometry_as_a_key = geometry_as_a_key[0]
        else:
            geometry_as_a_key = geometry_as_a_key[:2].join(' ')

        extension = [base_extension + [last_char]
                     for last_char in char_3[geometry_as_a_key]]
        extensions[field_type] = extension
    return extensions


# FIXME Cannot import Accelerator type (circular import)
# Maybe this routine would be better in Accelerator?
# |-> more SimulationOutput
def output_data_in_tw_fashion(linac) -> pd.DataFrame:
    """Mimick TW's Data tab."""
    larousse = {
        '#': lambda lin, elt: elt.get('elt_idx', to_numpy=False),
        'Name': lambda lin, elt: elt.get('elt_name', to_numpy=False),
        'Type': lambda lin, elt: elt.get('nature', to_numpy=False),
        'Length (mm)': lambda lin, elt: elt.length_m * 1e3,
        'Grad/Field/Amp': lambda lin, elt:
            elt.grad if (elt.get('nature', to_numpy=False) == 'QUAD')
            else np.NaN,
        'EoT (MV/m)': lambda lin, elt: None,
        'EoTLc (MV)': lambda lin, elt: elt.get('v_cav_mv'),
        'Input_Phase (deg)': lambda lin, elt: elt.get('phi_0_rel',
                                                      to_deg=True),
        'Sync_Phase (deg)': lambda lin, elt: elt.get('phi_s', to_deg=True),
        'Energy (MeV)': lambda lin, elt: lin.get('w_kin', elt=elt, pos='out'),
        'Beta Synch.': lambda lin, elt: lin.get('beta', elt=elt, pos='out'),
        'Full length (mm)': lambda lin, elt: lin.get('z_abs', elt=elt,
                                                     pos='out') * 1e3,
        'Abs. phase (deg)': lambda lin, elt: lin.get('phi_abs', to_deg=True,
                                                     elt=elt, pos='out'),
    }

    data = []
    n_latt = 1
    i = 0
    for lattice in linac.elts.by_lattice:
        lattice_n = '--------M' + str(n_latt)
        data.append([np.NaN, lattice_n, '', np.NaN, np.NaN, np.NaN, np.NaN,
                     np.NaN, np.NaN, np.NaN, np.NaN, np.NaN, np.NaN])
        n_latt += 1
        for elt in lattice:
            row = []
            for value in larousse.values():
                row.append(value(linac, elt))
                data.append(row)
                i += 1

    data = pd.DataFrame(data, columns=larousse.keys())
    return data
