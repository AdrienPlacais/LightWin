"""Define :class:`Accelerator`, the highest-level class of LightWin.

It holds, well... an accelerator. This accelerator has a
:class:`.ListOfElements`. For each :class:`.BeamCalculator` defined, it has a
:class:`.SimulationOutput` stored in :attr:`Accelerator.simulation_outputs`.
Additionally, it has a :class:`.ParticleInitialState`, which describes energy,
phase, etc of the beam at the entry of its :class:`.ListOfElements`.

"""

import logging
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Literal, Self

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from numpy.typing import NDArray

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
from lightwin.util.pickling import MyCloudPickler, MyPickler
from lightwin.util.typing import (
    CONCATENABLE_ELTS,
    EXPORT_PHASES_T,
    GETTABLE_ACCELERATOR_T,
    GETTABLE_SIMULATION_OUTPUT,
    GETTABLE_SIMULATION_OUTPUT_T,
    POS_T,
)

ACCELERATOR_STATUS_T = Literal["reference", "broken", "fix"]


class Accelerator:
    """Class holding a :class:`.ListOfElements`."""

    def __init__(
        self,
        name: str,
        status: ACCELERATOR_STATUS_T,
        dat_file: Path,
        accelerator_path: Path,
        list_of_elements_factory: ListOfElementsFactory,
        e_mev: float,
        sigma: NDArray[np.float64],
        pickle_path: Path | None = None,
        index: int = 0,
        **kwargs,
    ) -> None:
        r"""Create object.

        Parameters
        ----------
        name :
            Name of the accelerator, used in plots.
        status :
            Current status design.
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
        pickle_path :
            Where to pickle object. Used in :meth:`.keep`.
        index :
            Corresponding :class:`.FaultScenario` index. A null index is
            reserved for reference accelerator.

        """
        #: Name for the object. The default will be ``"Reference"`` or
        #: ``"Solution"``. If object is unpickled, the name will be taken from
        #: the ``TOML`` configuration dictionary.
        self.name = name
        self.status: ACCELERATOR_STATUS_T = status
        #: Corresponding :class:`.FaultScenario` index. A null index
        #: is reserved for reference accelerator.
        self.index = index
        #: Every :class:`.SimulationOutput` instance, associated with the name
        #: of the :class:`.BeamCalculator` that created it. This dictionary is
        #: filled by :meth:`keep`.
        self.simulation_outputs: dict[str, SimulationOutput] = {}
        self.data_in_tw_fashion: pd.DataFrame
        #: Absolute path where results for each :class:`.BeamCalculator` will
        #: be stored. Typically, this is a `000001/`-like folder.
        self.accelerator_path = accelerator_path

        kwargs = {
            "w_kin": e_mev,
            "phi_abs": 0.0,
            "z_in": 0.0,
            "sigma_in": sigma,
        }
        #: The list of elements contained in the accelerator.
        self.elts: ListOfElements
        self.elts = list_of_elements_factory.whole_list_run(
            dat_file, accelerator_path, **kwargs
        )
        logging.info(
            "Created a ListOfElements ecompassing all linac. Created with:\n"
            f"{dat_file = }\nw_kin_in = {self.elts.w_kin_in:.2f} MeV\n"
            f"phi_abs_in = {self.elts.phi_abs_in:.2f} rad"
        )

        self._special_getters = self._create_special_getters()

        self._l_cav = self.elts.l_cav
        self._tracewin_command: list[str] | None = None
        #: Internal variable telling if this instance was create by unpickling
        #: a ``PKL`` file.
        self._is_unpickled: bool = False
        #: If set, :meth:`.keep` will also pickle current instance
        self._pickle_path: Path | None = pickle_path

    @property
    def l_cav(self):
        """Shortcut to easily get list of cavities."""
        return self.elts.l_cav

    @property
    def is_unpickled(self) -> bool:
        """Tell if current object was created by unpickling a ``PKL`` file.

        If this flag is ``True``, the main consequence is that the
        :class:`.BeamCalculator` instances will not re-create new
        :class:`.SimulationOutput`, and instead return the ones that should
        already be in :attr:`.simulation_outputs`.

        See Also
        --------
        :meth:`.BeamCalculator.compute`

        """
        return self._is_unpickled

    @is_unpickled.setter
    def is_unpickled(self, value: bool) -> None:
        """Update internal value, and also raise a warning."""
        logging.warning(
            "You have no reason to modify the value of this attribute. I'll do"
            " what you ask nonetheless."
        )
        self._is_unpickled = value

    def has(self, key: str) -> bool:
        """Tell if the required attribute is in this class."""
        return key in recursive_items(vars(self))

    def get(
        self,
        *keys: GETTABLE_ACCELERATOR_T,
        to_numpy: bool = True,
        none_to_nan: bool = False,
        elt: str | Element | None = None,
        pos: POS_T | None = None,
        **kwargs: Any,
    ) -> Any:
        """Get attributes from this instance or its attributes.

        .. note::
            Simulation-related quantities (e.g., beam parameters, transfer
            matrices) are stored in the :attr:`simulation_outputs` dictionary,
            where each key is the name of a :class:`.BeamCalculator` solver
            (e.g., ``"CyEnvelope1D_0"``, ``"TraceWin_1"``), and each value is a
            corresponding :class:`.SimulationOutput` object.

            If simulations have been performed using multiple solvers,
            :meth:`Accelerator.get` becomes ambiguous and should be avoided
            for solver-dependent data. In that case, prefer calling
            ``accelerator.simulation_outputs[solver_name].get(...)`` directly.

        Parameters
        ----------
        *keys :
            Names of the desired attributes.
        to_numpy :
            Convert list outputs to NumPy arrays.
        none_to_nan :
            Replace ``None`` values with ``np.nan``.
        elt :
            Target element name or instance, passed to recursive_getter.
        pos :
            Position key for slicing data arrays.
        **kwargs :
            Additional arguments for recursive_getter.

        Returns
        -------
        Any
            A single value or tuple of values.

        """
        results = []

        for key in keys:
            if key in GETTABLE_SIMULATION_OUTPUT:
                msg = (
                    f"{key = }: use `SimulationOutput.get()` for "
                    "simulation-related attributes. `Accelerator.get()` may be"
                    " ambiguous when multiple outputs exist."
                )
                log = (
                    logging.error
                    if len(self.simulation_outputs) > 1
                    else logging.warning
                )
                log(msg)

            if key in self._special_getters:
                if elt is not None:
                    logging.error(
                        f"Cannot resolve special getter with {elt = }."
                    )
                value = self._special_getters[key](self)

            elif key in CONCATENABLE_ELTS:
                value = self.elts.get(
                    key,
                    to_numpy=to_numpy,
                    none_to_nan=none_to_nan,
                    elt=elt,
                    pos=pos,
                    **kwargs,
                )

            elif not self.has(key):
                value = None

            else:
                if elt is not None and (
                    isinstance(elt, str) or elt not in self.elts
                ):
                    elt = self.equivalent_elt(elt)
                value = recursive_getter(
                    key,
                    vars(self),
                    to_numpy=False,
                    none_to_nan=False,
                    elt=elt,
                    pos=pos,
                    **kwargs,
                )

            if value is None and none_to_nan:
                value = np.nan

            if to_numpy and isinstance(value, list):
                value = np.array(value)
            elif not to_numpy and isinstance(value, np.ndarray):
                value = value.tolist()

            results.append(value)

        return results[0] if len(results) == 1 else tuple(results)

    def _create_special_getters(self) -> dict[str, Callable]:
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

    def keep(
        self,
        simulation_output: SimulationOutput,
        exported_phase: EXPORT_PHASES_T,
        beam_calculator_id: str,
    ) -> None:
        """Save simulation and settings.

        In particular:
           - Store the cavity settings in the appropriate :class:`.FieldMap`.
           - Save the settings in a ``DAT`` file.
           - Store the :class:`.SimulationOutput` in the
             :attr:`.simulation_outputs` dictionary.

        Parameters
        ----------
        simulation_output :
            The instance to keep.
        exported_phase :
            The reference phase in the output ``DAT`` file.
        beam_calculator_id :
            Unique ID for the :class:`.BeamCalculator` that created
            ``simulation_output``. Will be the key to access
            ``simulation_output`` in :attr:`.simulation_outputs`.

        """
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

        simulation_output.out_path = (
            self.accelerator_path / simulation_output.out_folder
        )
        self.simulation_outputs[beam_calculator_id] = simulation_output

        if self._pickle_path:
            my_pickler = MyCloudPickler()
            self.pickle(my_pickler, self._pickle_path)

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
    ) -> Path | None:
        """Pickle (save) the object.

        This is useful for debug and temporary saves; do not use it for long
        time saving.

        """
        return pickler.pickle(
            my_object=self,
            path=path,
            initialfile=self.name + ".pkl",
            initialdir=self.accelerator_path,
            title=f"Choose where to save Accelerator: {self.name}",
        )

    def plot(
        self,
        key: GETTABLE_SIMULATION_OUTPUT_T,
        to_deg: bool = True,
        grid: bool = True,
        x: Literal["z_abs", "elt_idx"] | None = None,
        legend_entry: str | None = None,
        ax: Axes | None = None,
        **kwargs,
    ) -> Axes | None:
        """Plot ``key`` for every stored :class:`.SimulationOutput`.

        This method does not use the default plotting module, but pandas
        dataframe plotting method.

        """
        for solver, simulation_output in self.simulation_outputs.items():
            ax = simulation_output.plot(
                key,
                to_deg=to_deg,
                grid=grid,
                x=x,
                legend_entry=legend_entry
                or f"{simulation_output.linac_id} ({solver})",
                ax=ax,
                **kwargs,
            )
        return ax

    @classmethod
    def from_pickle(
        cls,
        pickler: MyPickler,
        path: Path | str | None = None,
        name: str | None = None,
        linac_id: str | Sequence[str] | None = None,
        index: int = 0,
    ) -> Self:
        """Instantiate object from previously pickled file.

        .. note::
           Also sets the "private" attribute :attr:`.Accelerator._is_unpickled`
           to ``True``.

        .. todo::
            The GUI may also ask for the new :class:`Accelerator` name? I think
            it would be too much intricated because I have no GUI specific
            module. Maybe one day...

        Parameters
        ----------
        pickler :
            Pickler object.
        path :
            Path to the pickled object file. If not provided, use ``Tk`` to
            open GUI and let user choose.
        name :
            To override the unpickled :attr:`.Accelerator.name`.
        linac_id :
            Use this to override the :func:`.SimulationOutput.linac_id` stored
            in unpickled :attr:`Accelerator.simulation_outputs`. In particular,
            used to legend plots.
        index :
            Corresponding :class:`.FaultScenario` index. A null index is
            reserved for reference accelerator. Will override the ``index``
            already stored in the unpickled object.

        """
        accelerator = pickler.unpickle(path, expected=Accelerator)
        if accelerator is None:
            raise TypeError(f"Unpickling {path} failed.")
        elif not isinstance(accelerator, cls):
            raise TypeError("Unpickled object is not an Accelerator instance.")

        logging.info(f"Created an Accelerator by unpickling {path}.")
        accelerator._is_unpickled = True
        if name:
            accelerator.name = name
        accelerator.index = index

        simulation_outputs = list(accelerator.simulation_outputs.values())

        if linac_id is None:
            return accelerator

        if isinstance(linac_id, str):
            linac_id = [linac_id for _ in simulation_outputs]
        for so, id in zip(simulation_outputs, linac_id, strict=True):
            so.linac_id = id

        return accelerator
