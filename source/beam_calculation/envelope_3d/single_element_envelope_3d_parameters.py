#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Define a class to hold solver parameters for :class:`.Envelope3D`.

This module holds :class:`SingleElementEnvelope3DParameters`, that inherits
from the Abstract Base Class :class:`.SingleElementCalculatorParameters`.
It holds the transfer matrix function that is used, as well as the meshing in
accelerating elements.

In a first time, only Runge-Kutta (no leapfrog) and only Python (no Cython).

The list of implemented transfer matrices is
:data:`implemented_transfer_matrices`.

"""
from typing import Callable
from types import ModuleType

import numpy as np

import util.converters as convert
from core.electric_field import compute_param_cav
from beam_calculation.single_element_beam_calculator_parameters import (
    SingleElementCalculatorParameters)

from core.elements.element import Element
from core.elements.drift import Drift
from core.elements.quad import Quad
from core.elements.field_map import FieldMap


implemented_transfer_matrices = (Drift, Quad, FieldMap)  #:


class SingleElementEnvelope3DParameters(SingleElementCalculatorParameters):
    """
    Holds the parameters to compute beam propagation in an Element.

    has and get method inherited from SingleElementCalculatorParameters parent
    class.

    """

    def __init__(self,
                 elt: Element,
                 # length_m: float,
                 # is_accelerating: bool,
                 # n_cells: int | None,
                 n_steps_per_cell: int,
                 transf_mat_module: ModuleType) -> None:
        """Set the actually useful parameters."""
        length_m = elt.get('length_m', to_numpy=False)
        n_cells = elt.get('n_cell', to_numpy=False)
        element_type = type(elt)
        self.n_steps = 1

        self.n_cells = n_cells
        self.back_up_function = transf_mat_module.drift
        self.transf_mat_function = self._proper_transfer_matrix_function(
            n_cells,
            n_steps_per_cell,
            element_type,
            transf_mat_module)

        self.d_z = length_m / self.n_steps
        self.rel_mesh = np.linspace(0., length_m, self.n_steps + 1)

        self.s_in: int
        self.s_out: int
        self.abs_mesh: np.ndarray

    def _proper_transfer_matrix_function(self,
                                         n_cells: int | None,
                                         n_steps_per_cell: int,
                                         element_type: type,
                                         transf_mat_module) -> Callable:
        """Select the transfer matrix function that is adapted."""
        transfer_matrice_selector = {
            Drift: transf_mat_module.drift,
            Quad: transf_mat_module.quad,
            FieldMap: transf_mat_module.field_map_rk4,
            }
        if element_type is FieldMap:
            assert n_cells is not None
            self.n_steps = n_cells * n_steps_per_cell
        return transfer_matrice_selector[element_type]

    def set_absolute_meshes(self,
                            pos_in: float,
                            s_in: int
                            ) -> tuple[float, int]:
        """Set the absolute indexes and arrays, depending on previous elem."""
        self.abs_mesh = self.rel_mesh + pos_in

        self.s_in = s_in
        self.s_out = self.s_in + self.n_steps

        return self.abs_mesh[-1], self.s_out

    def re_set_for_broken_cavity(self):
        """Change solver parameters for efficiency purposes."""
        self.transf_mat_function = self.back_up_function

    # FIXME should not have dependencies is_accelerating, status
    def transf_mat_function_wrapper(self,
                                    w_kin_in: float,
                                    is_accelerating: bool,
                                    elt_status: str,
                                    **rf_field_kwargs) -> dict:
        """
        Calculate beam propagation in the Element.

        This wrapping is not very Pythonic, should be removed in the future.

        """
        gamma = convert.energy(w_kin_in, "kin to gamma")

        args = (self.d_z, gamma, self.n_steps)

        transfer_matrix, gamma_phi, itg_field = self.transf_mat_function(
            *args, **rf_field_kwargs)

        cav_params = None
        if is_accelerating:
            gamma_phi[:, 1] /= self.n_cells
            cav_params = compute_param_cav(itg_field, elt_status)

        w_kin = convert.energy(gamma_phi[:, 0], "gamma to kin")
        results = {'transfer_matrix': transfer_matrix,
                   'r_zz': transfer_matrix[:, 4:, 4:],
                   'cav_params': cav_params,
                   'w_kin': w_kin,
                   'phi_rel': gamma_phi[:, 1]}

        return results
