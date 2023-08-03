#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 21 11:54:19 2021.

@author: placais

This module holds `Accelerator`, the highest-level class of LightWin. It holds,
well... an accelerator. This accelerator has a `ListOfElements`. For each
`BeamCalculator` defined, it has a `SimulationOutput`. Additionaly, it has a
`ParticleInitialState`, which describes energy, phase, etc of the beam at the
entry of its `ListOfElements`.

TODO : Check if _check_consistency_phases message still relatable
TODO : compute_transfer_matrices: simplify, add a calculation of missing phi_0
at the end

"""
import os.path
import logging
from typing import Any

import numpy as np
import pandas as pd

import config_manager as con

import tracewin_utils.interface
import tracewin_utils.load

from beam_calculation.output import SimulationOutput

from core.particle import ParticleInitialState
from core.beam_parameters import BeamParameters
from core.elements import _Element, FieldMapPath
from core.list_of_elements import (ListOfElements,
                                   elt_at_this_s_idx,
                                   equiv_elt)
from core.list_of_elements_factory import new_list_of_elements

from util.helper import recursive_items, recursive_getter


# TODO dedicated methods to init self.synch (self.input_particle is better)
# TODO maybe keep the self.input_beam. And create a dedicated init
class Accelerator():
    """Class holding the list of the accelerator's elements."""

    def __init__(self, name: str, dat_file: str, project_folder: str,
                 accelerator_path: str, out_folders: tuple[str]) -> None:
        """
        Create Accelerator object.

        The different elements constituting the accelerator will be stored
        in the list self.
        The data such as the synch phase or the beam energy will be stored in
        the self.synch Particle object.

        """
        self.name = name
        self.simulation_outputs: dict[str, SimulationOutput] = {}
        self.data_in_tw_fashion: pd.DataFrame

        # Prepare files and folders
        self.files = {
            'dat_filepath': dat_file,
            'original_dat_folder': os.path.dirname(dat_file),  # used only once
            'project_folder': project_folder,
            'accelerator_path': accelerator_path,
            'dat_filecontent': None,
            'field_map_folder': None,
        }

        # Load dat file, clean it up (remove comments, etc), load elements
        dat_filecontent = tracewin_utils.load.dat_file(dat_file)
        elts = tracewin_utils.interface.create_structure(dat_filecontent)
        elts = self._set_field_map_files_paths(elts)

        self.synch = ParticleInitialState(w_kin=con.E_MEV,
                                          phi_abs=0.,
                                          synchronous=True)
        input_particle = self.synch

        # TODO separate this from Accelerator.__init__
        input_beam = BeamParameters()
        input_beam.create_phase_spaces('zdelta')
        input_beam.zdelta.tm_cumul = np.eye(2)
        input_beam.zdelta.sigma_in = con.SIGMA_ZDELTA

        # self.elts = ListOfElements(elts, w_kin=con.E_MEV, phi_abs=0.,
        #                            first_init=True)
        self.elts: ListOfElements = new_list_of_elements(elts,
                                                         input_particle,
                                                         input_beam)

        tracewin_utils.interface.set_all_electric_field_maps(
            self.files, self.elts.by_section_and_lattice)

        self.files['dat_filecontent'] = dat_filecontent

        self._special_getters = self._create_special_getters()
        self._check_consistency_phases()

        self._l_cav = self.elts.l_cav

    @property
    def l_cav(self):
        """Shortcut to easily get list of cavities."""
        return self.elts.l_cav

    def has(self, key: str) -> bool:
        """Tell if the required attribute is in this class."""
        return key in recursive_items(vars(self))

    def get(self, *keys: str, to_numpy: bool = True, none_to_nan: bool = False,
            elt: str | _Element | None = None, **kwargs: bool | str) -> Any:
        """
        Shorthand to get attributes from this class or its attributes.

        Parameters
        ----------
        *keys : str
            Name of the desired attributes.
        to_numpy : bool, optional
            If you want the list output to be converted to a np.ndarray. The
            default is True.
        none_to_nan : bool, optional
            To convert None to np.NaN. The default is False.
        elt : str | _Element | None, optional
            If provided, and if the desired keys are in SimulationOutput, the
            attributes will be given over the _Element only. You can provide an
            _Element name, such as `QP1`. If the given _Element is not in the
            Accelerator.ListOfElements, the _Element with the same name that is
            present in this list will be used.
        **kwargs : bool | str
            Other arguments passed to recursive getter.

        Returns
        -------
        out : Any
            Attribute(s) value(s).

        """
        val = {key: [] for key in keys}

        for key in keys:
            if key in self._special_getters:
                val[key] = self._special_getters[key](self)
                if elt is not None:
                    # TODO
                    logging.error("Get attribute by elt not implemented with "
                                  "special getters.")
                continue

            if not self.has(key):
                val[key] = None
                continue

            if elt is not None and (isinstance(elt, str)
                                    or elt not in self.elts):
                elt = self.equiv_elt(elt)

            val[key] = recursive_getter(key, vars(self), to_numpy=False,
                                        none_to_nan=False,
                                        elt=elt, **kwargs)

        out = [val[key] for key in keys]
        if to_numpy:
            out = [np.array(val) if isinstance(val, list) else val
                   for val in out]
            if none_to_nan:
                out = [val.astype(float) for val in out]

        if len(keys) == 1:
            return out[0]
        return tuple(out)

    def _set_field_map_files_paths(self, elts: list[_Element]
                                   ) -> list[_Element]:
        """Load FIELD_MAP_PATH, remove it from the list of elements."""
        field_map_paths = list(filter(
            lambda elt: isinstance(elt, FieldMapPath), elts))

        # FIELD_MAP_PATH are not physical elements, so we remove them
        for field_map_path in field_map_paths:
            elts.remove(field_map_path)

        if len(field_map_paths) == 0:
            field_map_paths = list(
                FieldMapPath(['FIELD_MAP_PATH',
                              self.files['original_dat_folder']])
            )

        if len(field_map_paths) != 1:
            logging.error("Change of field maps base folder not supported.")
            field_map_paths = [field_map_paths[0]]

        field_map_paths = [os.path.abspath(field_map_path.path)
                           for field_map_path in field_map_paths]
        self.files['field_map_folder'] = field_map_paths[0]
        return elts

    def _create_special_getters(self) -> dict:
        """Create a dict of aliases that can be accessed w/ the get method."""
        # FIXME this won't work with new simulation output
        # TODO also remove the M_ij?
        _special_getters = {
            'M_11': lambda self: self.simulation_output.tm_cumul[:, 0, 0],
            'M_12': lambda self: self.simulation_output.tm_cumul[:, 0, 1],
            'M_21': lambda self: self.simulation_output.tm_cumul[:, 1, 0],
            'M_22': lambda self: self.simulation_output.tm_cumul[:, 1, 1],
            'element number': lambda self: self.get('elt_idx') + 1,
        }
        return _special_getters

    def _check_consistency_phases(self) -> None:
        """Check that both TW and LW use absolute or relative phases."""
        flags_absolute = []
        for cav in self.l_cav:
            flags_absolute.append(cav.get('abs_phase_flag'))

        if con.FLAG_PHI_ABS and False in flags_absolute:
            logging.warning(
                "You asked LW a simulation in absolute phase, while there "
                + "is at least one cavity in relative phase in the .dat file "
                + "used by TW. Results won't match if there are faulty "
                + "cavities.")
        elif not con.FLAG_PHI_ABS and True in flags_absolute:
            logging.warning(
                "You asked LW a simulation in relative phase, while there "
                + "is at least one cavity in absolute phase in the .dat file "
                + "used by TW. Results won't match if there are faulty "
                + "cavities.")

    def keep_settings(self, simulation_output: SimulationOutput) -> None:
        """Save cavity parameters in _Elements and new .dat file."""
        for i, (elt, rf_field) in enumerate(zip(self.elts,
                                                simulation_output.rf_fields)):
            v_cav_mv = simulation_output.cav_params['v_cav_mv'][i]
            phi_s = simulation_output.cav_params['phi_s'][i]
            elt.keep_rf_field(rf_field, v_cav_mv, phi_s)

        dat_filepath = os.path.join(
            self.files['accelerator_path'],
            simulation_output.out_folder,
            os.path.basename(self.files['dat_filepath']))
        self._store_settings_in_dat(dat_filepath, save=True)

    def keep_simulation_output(self, simulation_output: SimulationOutput,
                               beam_calculator_id: str) -> None:
        """
        Save `SimulationOutput`. Store info on current `Accelerator` in it.

        In particular, we want to save a results path in the `SimulationOutput`
        so we can study it and save Figures/study results in the proper folder.

        """
        simulation_output.out_path = os.path.join(self.get('accelerator_path'),
                                                  simulation_output.out_folder)
        self.simulation_outputs[beam_calculator_id] = simulation_output

    def elt_at_this_s_idx(self, s_idx: int, show_info: bool = False
                          ) -> _Element | None:
        """Give the element where the given index is."""
        return elt_at_this_s_idx(self.elts, s_idx, show_info)

    def equiv_elt(self, elt: _Element | str, to_index: bool = False
                  ) -> _Element | int | None:
        """Return an element from self.elts with the same name."""
        return equiv_elt(self.elts, elt, to_index)

    def _store_settings_in_dat(self, dat_filepath: str, save: bool = True
                               ) -> None:
        """Update the dat file, save it if asked."""
        tracewin_utils.interface.update_dat_with_fixed_cavities(
            self.get('dat_filecontent', to_numpy=False),
            self.elts,
            self.get('field_map_folder')
        )

        if save:
            self.files['dat_filepath'] = dat_filepath
            with open(self.get('dat_filepath'), 'w') as file:
                for line in self.files['dat_filecontent']:
                    file.write(' '.join(line) + '\n')
            logging.info(f"New dat saved in {self.get('dat_filepath')}")


def accelerator_factory(beam_calculators: tuple[object | None],
                        files: dict[str, str],
                        beam: dict[str, Any],
                        wtf: dict[str, Any] | None = None,
                        **kwargs
                        ) -> list[Accelerator]:
    """Create the required Accelerators as well as their output folders."""
    n_simulations = 1
    if wtf is not None:
        n_simulations = len(wtf['failed']) + 1

    out_folders = tuple([beam_calculator.out_folder
                        for beam_calculator in beam_calculators
                        if beam_calculator is not None
                         ])

    accelerator_paths = _generate_folders_tree_structure(
        project_folder=files['project_folder'],
        n_simulations=n_simulations,
        out_folders=out_folders
    )
    names = ['Broken' if i > 0 else 'Working' for i in range(n_simulations)]

    accelerators = [Accelerator(name, accelerator_path=accelerator_path,
                                out_folders=out_folders, **files)
                    for name, accelerator_path
                    in zip(names, accelerator_paths)]
    return accelerators


def _generate_folders_tree_structure(project_folder: str, n_simulations: int,
                                     out_folders: tuple[str]) -> None:
    """
    Create the proper folders for every Accelerator.

    The default structure is:

    where_original_dat_is/
        YYYY.MM.DD_HHhMM_SSs_MILLIms/              <- project_folder
            000000_ref/                            <- accelerator_path
                beam_calculation_toolname/         <- beam_calc
                (beam_calculation_post_toolname)/  <- beam_calc_post
            000001/
                beam_calculation_toolname/
                (beam_calculation_post_toolname)/
            000002/
                beam_calculation_toolname/
                (beam_calculation_post_toolname)/
            etc

    """
    accelerator_paths = [os.path.join(project_folder, f"{i:06d}")
                         for i in range(n_simulations)]
    accelerator_paths[0] += '_ref'

    _ = [os.makedirs(os.path.join(fault_scenar, out_folder))
         for fault_scenar in accelerator_paths
         for out_folder in out_folders]
    return accelerator_paths
