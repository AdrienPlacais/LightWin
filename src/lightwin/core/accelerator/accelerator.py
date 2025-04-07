"""Define :class:`Accelerator`, the highest-level class of LightWin.

It holds, well... an accelerator. This accelerator has a
:class:`.ListOfElements`. For each :class:`.BeamCalculator` defined, it has a
:class:`.SimulationOutput`. Additionally, it has a
:class:`.ParticleInitialState`, which describes energy, phase, etc of the beam
at the entry of its :class:`.ListOfElements`.

.. todo::
    Compute_transfer_matrices: simplify, add a calculation of missing phi_0
    at the end

"""

import logging
from pathlib import Path
from typing import Any, Self

import numpy as np
import pandas as pd

from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.elements.element import Element
from lightwin.core.list_of_elements.factory import ListOfElementsFactory
from lightwin.core.list_of_elements.helper import (
    elt_at_this_s_idx,
    equivalent_elt,
)
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.util.helper import recursive_getter, recursive_items
from lightwin.util.pickling import MyPickler
from lightwin.util.typing import EXPORT_PHASES_T, GETTABLE_ACCELERATOR_T


class Accelerator:
    """Class holding a :class:`.ListOfElements`."""

    def __init__(
        self,
        name: str,
        dat_file: Path,
        accelerator_path: Path,
        list_of_elements_factory: ListOfElementsFactory,
        e_mev: float,
        sigma: np.ndarray,
        **kwargs,
    ) -> None:
        r"""Create object.

        Parameters
        ----------
        name :
            Name of the accelerator, used in plots.
        dat_file :
            Absolute path to the linac ``DAT`` file.
        accelerator_path :
            Absolute path where results for each :class:`.BeamCalculator` will
            be stored.
        list_of_elements_factory :
            A factory to create the list of elements.
        e_mev :
            Initial beam energy in :unit:`MeV`.
        sigma :
            Initial beam :math:`\sigma` matrix in :unit:`m` and :unit:`rad`.

        """
        self.name = name
        self.simulation_outputs: dict[str, SimulationOutput] = {}
        self.data_in_tw_fashion: pd.DataFrame
        self.accelerator_path = accelerator_path

        kwargs = {
            "w_kin": e_mev,
            "phi_abs": 0.0,
            "z_in": 0.0,
            "sigma_in": sigma,
        }
        self.elts: ListOfElements
        self.elts = list_of_elements_factory.whole_list_run(
            dat_file, accelerator_path, **kwargs
        )

        self._special_getters = self._create_special_getters()

        self._l_cav = self.elts.l_cav
        self._tracewin_command: list[str] | None = None

    @property
    def l_cav(self):
        """Shortcut to easily get list of cavities."""
        return self.elts.l_cav

    def has(self, key: str) -> bool:
        """Tell if the required attribute is in this class."""
        return key in recursive_items(vars(self))

    def get(
        self,
        *keys: GETTABLE_ACCELERATOR_T,
        to_numpy: bool = True,
        none_to_nan: bool = False,
        elt: str | Element | None = None,
        **kwargs: bool | str,
    ) -> Any:
        """
        Shorthand to get attributes from this class or its attributes.

        Parameters
        ----------
        *keys :
            Name of the desired attributes.
        to_numpy :
            If you want the list output to be converted to a np.ndarray.
        none_to_nan :
            To convert None to np.nan.
        elt :
            If provided, and if the desired keys are in SimulationOutput, the
            attributes will be given over the Element only. You can provide an
            Element name, such as ``QP1``. If the given Element is not in the
            Accelerator.ListOfElements, the Element with the same name that is
            present in this list will be used.
        **kwargs :
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
                    logging.error(
                        "Get attribute by elt not implemented with special "
                        "getters."
                    )
                continue

            if not self.has(key):
                val[key] = None
                continue

            if elt is not None and (
                isinstance(elt, str) or elt not in self.elts
            ):
                elt = self.equivalent_elt(elt)

            val[key] = recursive_getter(
                key,
                vars(self),
                to_numpy=False,
                none_to_nan=False,
                elt=elt,
                **kwargs,
            )

        out = [val[key] for key in keys]
        if to_numpy:
            out = [
                np.array(val) if isinstance(val, list) else val for val in out
            ]
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
            "M_11": lambda self: self.simulation_output.tm_cumul[:, 0, 0],
            "M_12": lambda self: self.simulation_output.tm_cumul[:, 0, 1],
            "M_21": lambda self: self.simulation_output.tm_cumul[:, 1, 0],
            "M_22": lambda self: self.simulation_output.tm_cumul[:, 1, 1],
            "element number": lambda self: self.get("elt_idx") + 1,
        }
        return _special_getters

    def keep_settings(
        self,
        simulation_output: SimulationOutput,
        exported_phase: EXPORT_PHASES_T,
    ) -> None:
        """Save cavity parameters in Elements and new .dat file."""
        set_of_cavity_settings = simulation_output.set_of_cavity_settings
        for cavity, settings in set_of_cavity_settings.items():
            cavity.cavity_settings = settings

        original_dat_file = self.elts.files_info["dat_file"]
        assert isinstance(original_dat_file, Path)
        filename = original_dat_file.name
        dat_file = (
            self.accelerator_path / simulation_output.out_folder / filename
        )

        self.elts.store_settings_in_dat(
            dat_file, exported_phase=exported_phase, save=True
        )

    def keep_simulation_output(
        self, simulation_output: SimulationOutput, beam_calculator_id: str
    ) -> None:
        """
        Save `SimulationOutput`. Store info on current `Accelerator` in it.

        In particular, we want to save a results path in the `SimulationOutput`
        so we can study it and save Figures/study results in the proper folder.

        """
        simulation_output.out_path = (
            self.accelerator_path / simulation_output.out_folder
        )
        self.simulation_outputs[beam_calculator_id] = simulation_output

    def elt_at_this_s_idx(
        self, s_idx: int, show_info: bool = False
    ) -> Element | None:
        """Give the element where the given index is."""
        return elt_at_this_s_idx(self.elts, s_idx, show_info)

    def equivalent_elt(self, elt: Element | str) -> Element:
        """Return element from ``self.elts`` with the same name as ``elt``."""
        return equivalent_elt(self.elts, elt)

    def pickle(
        self, pickler: MyPickler, path: Path | str | None = None
    ) -> Path:
        """Pickle (save) the object.

        This is useful for debug and temporary saves; do not use it for long
        time saving.

        """
        if path is None:
            path = self.accelerator_path / self.name
            path = path.with_suffix(".pkl")
        pickler.pickle(self, path)

        if isinstance(path, str):
            path = Path(path)
        return path

    @classmethod
    def from_pickle(cls, pickler: MyPickler, path: Path | str) -> Self:
        """Instantiate object from previously pickled file."""
        accelerator = pickler.unpickle(path)
        return accelerator  # type: ignore
