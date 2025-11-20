"""Define a class to store outputs from different :class:`.BeamCalculator`.

.. todo::
    Do I really need the `r_zz_elt` key??

.. todo::
    Do I really need z_abs? Envelope1D does not uses it while TraceWin does.

.. todo::
    Transfer matrices are stored in :class:`.TransferMatrix`, but also in
    ``BeamParameters.zdelta``.

.. todo::
    Maybe the synchronous phase model should appear somewhere in here?

"""

import logging
import math
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from numpy.typing import NDArray

from lightwin.core.beam_parameters.beam_parameters import BeamParameters
from lightwin.core.elements.element import ELEMENT_TO_INDEX_T, Element
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.core.particle import ParticleFullTrajectory
from lightwin.core.transfer_matrix.transfer_matrix import TransferMatrix
from lightwin.failures.set_of_cavity_settings import SetOfCavitySettings
from lightwin.util.dicts_output import markdown
from lightwin.util.helper import (
    flatten,
    range_vals,
    recursive_getter,
    recursive_items,
)
from lightwin.util.pickling import MyPickler
from lightwin.util.typing import (
    CONCATENABLE_ELTS,
    GET_ELT_ARG_T,
    GETTABLE_SIMULATION_OUTPUT_T,
    GETTABLE_STRUCTURE_DEPENDENT,
    NEEDS_3D,
    NEEDS_MULTIPART,
    POS_T,
)


@dataclass(eq=False)
class SimulationOutput:
    """Store the information produced by a :class:`.BeamCalculator`.

    Used for fitting, post-processing, plotting.

    Parameters
    ----------
    out_folder :
        Results folder used by the :class:`.BeamCalculator` that created this.
    is_multiparticle :
        Tells if the simulation is a multiparticle simulation.
    is_3d :
        Tells if the simulation is in 3D.
    synch_trajectory :
        Holds energy, phase of the synchronous particle.
    cav_params :
        Holds amplitude, synchronous phase, absolute phase, relative phase of
        cavities, phase acceptance, energy acceptance.
    beam_parameters :
        Holds emittance, Twiss parameters, envelopes in the various phase
        spaces.
    element_to_index :
        Takes an :class:`.Element`, its name, 'first' or 'last' as argument,
        and returns corresponding index. Index should be the same in all the
        arrays attributes of this class: ``z_abs``, ``beam_parameters``
        attributes, etc.  Used to easily ``get`` the desired properties at the
        proper position.
    set_of_cavity_settings :
        The cavity parameters used for the simulation.
    transfer_matrix :
         Holds absolute and relative transfer matrices in all planes.
    z_abs :
        Absolute position in the linac in m. The default is None.
    in_tw_fashion :
        A way to output the :class:`.SimulationOutput` in the same way as the
        ``Data`` tab of TraceWin. The default is None.
    r_zz_elt :
        Cumulated transfer matrices in the [z-delta] plane. The default is
        None.
    """

    out_folder: Path
    is_multiparticle: bool
    is_3d: bool

    synch_trajectory: ParticleFullTrajectory

    cav_params: dict[str, list[float | None]] | None

    beam_parameters: BeamParameters

    element_to_index: ELEMENT_TO_INDEX_T | None
    set_of_cavity_settings: SetOfCavitySettings

    transfer_matrix: TransferMatrix | None = None
    z_abs: np.ndarray | None = None
    in_tw_fashion: pd.DataFrame | None = None
    r_zz_elt: list[np.ndarray] | None = None

    def __post_init__(self) -> None:
        """Save complementary data, such as :class:`.Element` indexes."""
        self.elt_idx: list[int]
        if self.cav_params is None:
            logging.error(
                "Failed to init SimulationOutput.elt_idx as .cav_params was "
                "not provided."
            )
        else:
            self.elt_idx = [
                i for i, _ in enumerate(self.cav_params["v_cav_mv"], start=1)
            ]
        self.out_path: Path

    def __str__(self) -> str:
        """Give a resume of the data that is stored."""
        out = "SimulationOutput:\n"
        out += "\t" + range_vals("z_abs", self.z_abs)
        out += self.synch_trajectory.__str__()
        out += self.beam_parameters.__str__()
        return out

    def __repr__(self) -> str:
        """Return str, in order have more concise info."""
        return self.__str__()

    @property
    def beam_calculator(self) -> str:
        """Use ``out_path`` to retrieve name of :class:`.BeamCalculator`."""
        if not hasattr(self, "out_path"):
            return str(self.out_folder)
        return self.out_path.name

    @property
    def is_reference(self) -> bool:
        """Tell whether this objects concerns a nominal linac.

        .. todo::
           MMMh

        """
        return self.linac_id == "000000_ref"

    @property
    def linac_id(self) -> str:
        """Tell which linac is studied.

        .. todo::
           Fix this monstruosity.

        """
        return self.out_path.parent.stem

    def has(self, key: str) -> bool:
        """Tell if the required attribute is in this class.

        We also call the :meth:`.InitialBeamParameters.has`, as it is designed
        to handle the alias (such as ``twiss_zdelta`` <=> ``zdelta.twiss``).

        """
        return (
            key in recursive_items(vars(self))
            or self.beam_parameters.has(key)
            or (
                self.transfer_matrix is not None
                and self.transfer_matrix.has(key)
            )
        )

    def get(
        self,
        *keys: GETTABLE_SIMULATION_OUTPUT_T,
        to_numpy: bool = True,
        to_deg: bool = False,
        elt: (
            str
            | Element
            | GET_ELT_ARG_T
            | Collection[str | Element | GET_ELT_ARG_T]
            | None
        ) = None,
        pos: POS_T | None = None,
        none_to_nan: bool = False,
        handle_missing_elt: bool = False,
        warn_structure_dependent: bool = True,
        _remove_first: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Get attributes from this class or its subcomponents.

        See class docstring for parameter descriptions.

        Parameters
        ----------
        *keys :
            Names of the desired attributes.
        to_numpy :
            Convert list outputs to NumPy arrays.
        to_deg :
            Multiply keys with ``"phi"`` by ``180 / pi``.
        elt :
            Target element name or instance, passed to recursive_getter. If
            several elements are provided, they must be contiguous.
        pos :
            Position key for slicing data arrays.
        none_to_nan :
            Replace ``None`` values with ``np.nan``.
        handle_missing_elt :
            Look for an equivalent element when ``elt`` is not in
            :attr:`.SimulationOutput.element_to_index` 's ``_elts``.
        warn_structure_dependent :
            Raise a warning when trying to access data which is
            structure-related rather than simulation-related.
        _remove_first :
            Remove the first item of each element's attribute except for the
            first element itself. Used when ``elt`` consists of several
            elements, in order to avoid some data to be represented twice.
        **kwargs :
            Additional arguments for recursive_getter.

        Returns
        -------
        Any
            A single value or tuple of values.

        """
        if not isinstance(elt, str) and isinstance(elt, Collection):
            concat = [
                flatten(
                    [
                        self.get(
                            key,
                            to_numpy=False,
                            to_deg=to_deg,
                            elt=e,
                            pos=pos,
                            none_to_nan=False,
                            warn_structure_dependent=warn_structure_dependent,
                            _remove_first=i > 0,
                            **kwargs,
                        )
                        for i, e in enumerate(elt)
                    ]
                )
                for key in keys
            ]
            out = [list(x) for x in concat]
            if to_numpy:
                out = [np.array(x) for x in out]
            if none_to_nan:
                if not to_numpy:
                    logging.error(
                        f"{none_to_nan = } while {to_numpy = }, which is not "
                        "supported. Forcing to_numpy = True and hoping for the "
                        "best."
                    )
                    to_numpy = True
                out = [
                    (
                        np.array(np.nan)
                        if val is None
                        else np.asarray(val, dtype=float)
                    )
                    for val in out
                ]
            elif to_numpy:
                out = [
                    np.array(val) if not isinstance(val, str) else val
                    for val in out
                ]
            return out[0] if len(out) == 1 else tuple(out)

        out: list[Any] = []
        for key in keys:
            if (
                warn_structure_dependent
                and key in GETTABLE_STRUCTURE_DEPENDENT
            ):
                logging.warning(
                    f"{key = } is structure-dependent and does not vary from "
                    "simulation to simulation. You may be better of calling "
                    "`Accelerator.get` or `ListOfElements.get`."
                )

            # Special case: transfer matrix
            if (
                "r_" in key
                and "mismatch_factor_" not in key
                and self.transfer_matrix
            ):
                val = self.transfer_matrix.get(
                    key, to_numpy=False  # type: ignore[arg-type]
                )
            elif key in NEEDS_3D and not self.is_3d:
                val = None
            elif key in NEEDS_MULTIPART and not self.is_multiparticle:
                val = None
            else:
                val = recursive_getter(
                    key, vars(self), to_numpy=False, **kwargs
                )

            if val is not None:
                if to_deg and "phi" in key:
                    val = _to_deg(val)
                if elt is not None and self.element_to_index:
                    return_elt_idx = False
                    if key in CONCATENABLE_ELTS:
                        # With these keys, `val` holds one value per
                        # :class:`.Element`, not one per mesh point.
                        return_elt_idx = True
                    idx = self.element_to_index(
                        elt=elt,
                        pos=pos,
                        return_elt_idx=return_elt_idx,
                        handle_missing_elt=handle_missing_elt,
                    )
                    val = val[idx]
                if (
                    _remove_first
                    and isinstance(val, (list, np.ndarray))
                    and len(val) > 1
                ):
                    val = val[1:]

                if not to_numpy and isinstance(val, np.ndarray):
                    val = val.tolist()

            out.append(val)

        if none_to_nan:
            if not to_numpy:
                logging.error(
                    f"{none_to_nan = } while {to_numpy = }, which is not "
                    "supported. Forcing to_numpy = True and hoping for the "
                    "best."
                )
                to_numpy = True
            out = [
                (
                    np.array(np.nan)
                    if val is None
                    else np.asarray(val, dtype=float)
                )
                for val in out
            ]
        elif to_numpy:
            out = [
                np.array(val) if not isinstance(val, str) else val
                for val in out
            ]

        return out[0] if len(out) == 1 else tuple(out)

    def compute_indirect_quantities(
        self, elts: ListOfElements, ref_simulation_output: Self | None = None
    ) -> None:
        """Compute indirect quantities, such as mismatch factor.

        .. todo::
            Fix output_data_in_tw_fashion

        Parameters
        ----------
        elts :
            A full :class:`.ListOfElements`, containing all the elements of the
            linac.
        ref_simulation_output :
            Reference simulation output; providing it allows calculation of
            mismatch factor.

        """
        if self.z_abs is None:
            self.z_abs = elts.get("abs_mesh", remove_first=True)
        self.synch_trajectory.compute_reduced_velocity()

        # self.in_tw_fashion = tracewin.interface.output_data_in_tw_fashion()
        if ref_simulation_output is None:
            return

        mismatch_kw = {
            "raise_missing_phase_space_error": True,
            "raise_missing_mismatch_error": True,
            "raise_missing_twiss_error": True,
        }

        phase_space_names = ("zdelta",)
        if self.is_3d:
            phase_space_names = ("zdelta", "x", "y", "t")
        # if self.is_multiparticle:
        #     phase_space_names = ('zdelta', 'x', 'y', 't',
        #                          'x99', 'y99', 'phiw99')

        self.beam_parameters.set_mismatches(
            ref_simulation_output.beam_parameters,
            *phase_space_names,
            **mismatch_kw,
        )

    def pickle(
        self, pickler: MyPickler, path: Path | str | None = None
    ) -> Path:
        """Pickle (save) the object.

        This is useful for debug and temporary saves; do not use it for long
        time saving.

        """
        if path is None:
            path = self.out_path / "simulation_output.pkl"
        assert isinstance(path, Path)
        pickler.pickle(self, path)

        if isinstance(path, str):
            path = Path(path)
        return path

    @classmethod
    def from_pickle(cls, pickler: MyPickler, path: Path | str) -> Self:
        """Instantiate object from previously pickled file."""
        simulation_output = pickler.unpickle(path)
        return simulation_output  # type: ignore

    def plot(
        self, key: str, to_deg: bool = True, grid: bool = True, **kwargs
    ) -> Axes | np.ndarray:
        """Plot the key."""
        x_axis = markdown["z_abs"]
        df = pd.DataFrame(
            {
                x_axis: self.z_abs,
                markdown[key]: self.get(key, to_deg=to_deg, **kwargs),
            }
        )
        return df.plot(x=x_axis, grid=grid, ylabel=markdown[key], **kwargs)

    def elts(self) -> ListOfElements:
        """Retrieve the elements associated with this object."""
        assert (
            self.element_to_index is not None
        ), "SimulationOutput.element_to_index should be set"
        keywords = getattr(self.element_to_index, "keywords", None)
        assert isinstance(
            keywords, dict
        ), "SimulationOutput.element_to_index must be set with functools.paritial"
        _elts = keywords.get("_elts", None)
        assert _elts is not None, "SimulationOutput._elts incorrectly set"
        return _elts


def _to_deg(
    val: NDArray[np.float64] | list[float | None] | float,
) -> NDArray[np.float64] | list[float | None]:
    """Convert the ``val[key]`` into deg if it is not None."""
    if isinstance(val, list):
        return [
            math.degrees(angle) if angle is not None else None for angle in val
        ]
    return np.rad2deg(val)
