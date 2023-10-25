#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module holds :class:`Accelerator`, the highest-level class of LightWin.

It holds, well... an accelerator. This accelerator has a
:class:`.ListOfElements`. For each :class:`.BeamCalculator` defined, it has a
:class:`.SimulationOutput`. Additionally, it has a
:class:`.ParticleInitialState`, which describes energy, phase, etc of the beam
at the entry of its :class:`.ListOfElements`.

.. todo::
    Check if _check_consistency_phases message still relatable

.. todo::
    Compute_transfer_matrices: simplify, add a calculation of missing phi_0
    at the end

"""
import os.path
import logging
from typing import Any

import numpy as np
import pandas as pd

import config_manager as con

from beam_calculation.output import SimulationOutput

from core.elements.element import Element
from core.list_of_elements.list_of_elements import ListOfElements
from core.list_of_elements.factory import new_list_of_elements
from core.list_of_elements.helper import (elt_at_this_s_idx,
                                          equivalent_elt)

from util.helper import recursive_items, recursive_getter


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

        self.files = {'project_folder': project_folder,
                      'accelerator_path': accelerator_path}

        kwargs = {'w_kin': con.E_MEV,
                  'phi_abs': 0.,
                  'z_in': 0.,
                  'sigma_in': con.SIGMA}
        self.elts: ListOfElements
        self.elts = new_list_of_elements(dat_file, accelerator_path, **kwargs)
        # self.synch: ParticleInitialState = self.elts.input_particle

        self._special_getters = self._create_special_getters()
        self._check_consistency_phases()

        self._l_cav = self.elts.l_cav
        self._tracewin_command: list[str] | None = None

    @property
    def l_cav(self):
        """Shortcut to easily get list of cavities."""
        return self.elts.l_cav

    def has(self, key: str) -> bool:
        """Tell if the required attribute is in this class."""
        return key in recursive_items(vars(self))

    def get(self,
            *keys: str,
            to_numpy: bool = True,
            none_to_nan: bool = False,
            elt: str | Element | None = None,
            **kwargs: bool | str) -> Any:
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
        elt : str | Element | None, optional
            If provided, and if the desired keys are in SimulationOutput, the
            attributes will be given over the Element only. You can provide an
            Element name, such as `QP1`. If the given Element is not in the
            Accelerator.ListOfElements, the Element with the same name that is
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
                elt = self.equivalent_elt(elt)

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
        """Save cavity parameters in Elements and new .dat file."""
        for i, (elt, rf_field) in enumerate(zip(self.elts,
                                                simulation_output.rf_fields)):
            v_cav_mv = simulation_output.cav_params['v_cav_mv'][i]
            phi_s = simulation_output.cav_params['phi_s'][i]
            elt.keep_rf_field(rf_field, v_cav_mv, phi_s)

        dat_filepath = os.path.join(
            self.files['accelerator_path'],
            simulation_output.out_folder,
            os.path.basename(self.elts.files['dat_filepath']))
        self.elts.store_settings_in_dat(dat_filepath, save=True)

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
                          ) -> Element | None:
        """Give the element where the given index is."""
        return elt_at_this_s_idx(self.elts, s_idx, show_info)

    def equivalent_elt(self, elt: Element | str) -> Element:
        """Return element from ``self.elts`` with the same name as ``elt``."""
        return equivalent_elt(self.elts, elt)


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
