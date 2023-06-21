#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  9 11:56:20 2023.

@author: placais

A class to uniformly store the outputs from the different simulation tools:
    envelope1d
    tracewin_envelope
    tracewin_multiparticle
"""
from dataclasses import dataclass
from typing import Any
import numpy as np

from util.helper import recursive_items, recursive_getter
from core.list_of_elements import ListOfElements
import util.converters as convert
from core.emittance import beam_parameters_all


# TODO remove unnecessary
@dataclass
class SimulationOutput:
    """Stores the information that is needed for a fit."""

    w_kin: list[float] | None = None
    phi_abs_array: list[float] | None = None
    mismatch_factor: list[float | None] | None = None

    cav_params: list[dict | None] | None = None
    phi_s: list[float] | None = None
    r_zz_elt: list[np.ndarray] | None = None
    tm_cumul: np.ndarray | None = None
    rf_fields: list[dict] | None = None
    eps_zdelta: np.ndarray | None = None
    twiss_zdelta: np.ndarray | None = None
    sigma_matrix: np.ndarray | None = None

    def has(self, key: str) -> bool:
        """Tell if the required attribute is in this class."""
        return key in recursive_items(vars(self))

    def get(self, *keys: tuple[str], to_numpy: bool = True, **kwargs: dict
            ) -> Any:
        """Shorthand to get attributes."""
        val = {}
        for key in keys:
            val[key] = []

        for key in keys:
            if not self.has(key):
                val[key] = None
                continue

            val[key] = recursive_getter(key, vars(self), **kwargs)
            # Easier to concatenate lists that stack numpy arrays, so convert
            # to list
            if not to_numpy and isinstance(val[key], np.ndarray):
                val[key] = val[key].tolist()

        # Convert to list; elements of the list are numpy is required, except
        # strings that are never converted
        out = [np.array(val[key]) if to_numpy and not isinstance(val[key], str)
               else val[key]
               for key in keys]

        # Return as tuple or single value
        if len(out) == 1:
            return out[0]
        # implicit else:
        return tuple(out)

    def compute_complementary_data(self, elts: ListOfElements) -> None:
        """
        Compute some other indirect quantities.

        Parameters
        ----------
        elts: ListOfElements
            Must be a full ListOfElements, containing all the _Elements of the
            linac.
        """
        gamma = convert.energy(self.get('w_kin'), "kin to gamma")
        self.beam_param = beam_parameters_all(self.eps_zdelta,
                                              self.twiss_zdelta,
                                              gamma)

        mism = self.mismatch_factor
        if mism is not None:
            self.beam_param["mismatch_factor"] = mism
