"""Define a ``list`` of :class:`.Element`, with some additional methods.

Two objects can have a :class:`ListOfElements` as attribute:

* :class:`.Accelerator`: holds all the :class:`.Element` of the linac.
* :class:`.Fault`: it holds only a fraction of the linac
  :class:`.Element`. Beam will be propagated a huge number of times during
  optimisation process, so we recompute only the strict necessary.

.. todo::
    Delete ``dat_filecontent``, which does the same thing as ``elts_n_cmds`` but
    less good

"""

import logging
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Literal, Self, TypedDict, overload

import numpy as np
import pandas as pd

from lightwin.core.beam_parameters.initial_beam_parameters import (
    InitialBeamParameters,
)
from lightwin.core.elements.element import Element
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.core.elements.field_maps.superposed_field_map import (
    SuperposedFieldMap,
    unpack_superposed,
)
from lightwin.core.instruction import Instruction
from lightwin.core.list_of_elements.helper import (
    first,
    group_elements_by_lattice,
    group_elements_by_section,
    group_elements_by_section_and_lattice,
)
from lightwin.core.particle import ParticleInitialState
from lightwin.tracewin_utils.dat_files import export_dat_filecontent
from lightwin.tracewin_utils.interface import list_of_elements_to_command
from lightwin.tracewin_utils.line import DatLine
from lightwin.util.helper import recursive_getter, recursive_items
from lightwin.util.pickling import MyPickler
from lightwin.util.typing import (
    CONCATENABLE_ELTS,
    EXPORT_PHASES_T,
    GETTABLE_ELTS_T,
    ID_NATURE_T,
    REFERENCE_PHASES_T,
)

ELEMENT_ID_T = int | str
ELEMENTS_ID_T = Sequence[int] | list[str]
NESTED_ELEMENTS_ID = Sequence[Sequence[int]] | list[list[str]]


class FilesInfo(TypedDict):
    """Keep information on the loaded dat file."""

    dat_file: Path
    dat_filecontent: list[DatLine]
    accelerator_path: Path
    elts_n_cmds: list[Instruction]


class ListOfElements(list):
    """Class holding the elements of a fraction or of the whole linac."""

    def __init__(
        self,
        elts: list[Element],
        input_particle: ParticleInitialState,
        input_beam: InitialBeamParameters,
        tm_cumul_in: np.ndarray,
        files: FilesInfo,
        first_init: bool = True,
    ) -> None:
        """Create the object, encompassing all the linac or only a fraction.

        The first case is when you initialize an Accelerator and compute the
        baseline energy, phase, etc values.
        The second case is when you only recompute a fraction of the linac,
        which is part of the optimisation process.

        Parameters
        ----------
        elts :
            List containing the element objects.
        input_particle :
            An object to hold initial energy and phase of the particle at the
            entry of the first element.
        input_beam :
            An object to hold emittances, Twiss, sigma beam matrix, etc at the
            entry of the first element.
        first_init :
            To indicate if this a full linac or only a portion (fit process).
        files :
            A dictionary to hold information on the source and output
            files/folders of the object.

            * ``dat_file``: absolute path to the ``DAT`` file
            * ``elts_n_cmds``: list of objects representing dat content
            * ``accelerator_path``: where calculation results for each
              :class:`.BeamCalculator` will be stored.
            * ``dat_filecontent``: list of list of str, holding content of the
              ``DAT``.

        """
        self.input_particle = input_particle
        self.input_beam = input_beam
        self.files = files
        assert tm_cumul_in.shape == (6, 6)
        self.tm_cumul_in = tm_cumul_in

        super().__init__(elts)
        self.by_section_and_lattice: list[list[list[Element]]] | None = None
        self.by_lattice: list[list[Element]]
        self.by_section: list[list[Element]]

        if first_init:
            self._first_init()

        self._l_cav: list[FieldMap] = list(
            filter(lambda cav: isinstance(cav, FieldMap), self)
        )

    @property
    def w_kin_in(self):
        """Get kinetic energy at entry of first element of self."""
        return self.input_particle.w_kin

    @property
    def phi_abs_in(self):
        """Get absolute phase at entry of first element of self."""
        return self.input_particle.phi_abs

    @property
    def l_cav(self) -> list[FieldMap]:
        """Easy access to the list of cavities."""
        return self._l_cav

    def cavities(
        self, superposed: Literal["unpack", "remove", "keep"] = "unpack"
    ) -> list[FieldMap]:
        """Give the list of cavities, with special treatment for superposed.

        Parameters
        ----------
        superposed :
           How superposed field maps should be treated.

           - If ``"unpack"``, we insert the :class:`.FieldMap` contained in
             the :class:`.SuperposedFieldMap`.
           - If ``"remove"``, we remove the :class:`.SuperposedFieldMap` from
             the output.
           - If ``"keep"``, we return the :class:`.SuperposedFieldMap` along
             with the :class:`.FieldMap`.

        """
        cavities = self._l_cav
        if superposed == "keep":
            return cavities
        if superposed == "unpack":
            return unpack_superposed(cavities)
        return [
            cavity
            for cavity in cavities
            if not isinstance(cavity, SuperposedFieldMap)
        ]

    @property
    def tunable_cavities(self) -> list[FieldMap]:
        """All the elements that can be used for compensation.

        For now, only :class:`.FieldMap`. But in the future... Who knows?

        """
        return [cavity for cavity in self.l_cav if cavity.can_be_retuned]

    @property
    def tracewin_command(self) -> list[str]:
        """Create the command to give proper initial parameters to TraceWin."""
        dat_file = self.files["dat_file"]
        assert isinstance(dat_file, Path)
        _tracewin_command = [
            command_bit
            for command in [
                list_of_elements_to_command(dat_file),
                self.input_particle.tracewin_command,
                self.input_beam.tracewin_command,
            ]
            for command_bit in command
        ]

        return _tracewin_command

    def has(self, key: str) -> bool:
        """Tell if the required attribute is in this class."""
        return key in recursive_items(vars(self)) or key in recursive_items(
            vars(self[0])
        )

    def get(
        self,
        *keys: GETTABLE_ELTS_T,
        to_numpy: bool = True,
        none_to_nan: bool = False,
        remove_first: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Get attributes from this class or its contained elements.

        If the desired attribute belongs to :data:`.GETTABLE_ELT` or
        :data:`.GETTABLE_FIELD_MAP`, we concatenate the value of every element
        in a single list.

        Parameters
        ----------
        *keys :
            Names of the desired attributes.
        to_numpy :
            Convert list outputs to NumPy arrays.
        none_to_nan :
            Replace ``None`` values with ``np.nan``.
        remove_first :
            Remove the first item of each element's attribute except for the
            first element itself.
        **kwargs :
            Passed to recursive getter or :meth:`.Element.get`.

        Returns
        -------
        Any
            A single value or tuple of values.

        """
        results = []

        for key in keys:
            if key in CONCATENABLE_ELTS:
                values = []
                for i, elt in enumerate(self):
                    data = elt.get(key, to_numpy=False, **kwargs)
                    if remove_first and i > 0:
                        data = data[1:]
                    if isinstance(data, list):
                        values.extend(data)
                    else:
                        values.append(data)
                val = values

            elif not self.has(key):
                val = np.nan if none_to_nan else None

            else:  # get from self
                val = recursive_getter(key, vars(self), **kwargs)

            if val is None and none_to_nan:
                val = np.nan
            if to_numpy and isinstance(val, list):
                val = np.array(val)
            elif not to_numpy and isinstance(val, np.ndarray):
                val = val.tolist()

            results.append(val)

        return results[0] if len(results) == 1 else tuple(results)

    def _first_init(self) -> None:
        """Set structure, elements name, some indexes."""
        self.by_section = group_elements_by_section(self)
        self.by_lattice = group_elements_by_lattice(self)
        self.by_section_and_lattice = group_elements_by_section_and_lattice(
            self.by_section
        )
        self._set_element_indexes()

    def _set_element_indexes(self) -> None:
        """Set the element index."""
        elts_with_a_number = list(
            filter(lambda elt: elt.increment_elt_idx, self)
        )

        for i, elt in enumerate(elts_with_a_number):
            elt.idx["elt_idx"] = i

    def force_reference_phases_to(self, reference: REFERENCE_PHASES_T) -> None:
        """Change the reference phase of the cavities in ``self``.

        This method is called by the :class:`.BeamCalculator`. It is used after
        the first propagation of the beam in the full :class:`ListOfElements`,
        to force every :class:`.CavitySettings` to use the reference phase
        specified by the ``beam_calculator`` entry of the ``TOML``.

        """
        for cavity in self.l_cav:
            settings = cavity.cavity_settings
            if settings.reference == reference:
                continue
            settings.set_reference(reference)

    def store_settings_in_dat(
        self,
        dat_file: Path,
        exported_phase: EXPORT_PHASES_T,
        save: bool = True,
    ) -> None:
        r"""Update the ``DAT`` file, save it if asked.

        This method is called several times:

        * Once per :class:`.Fault` (only the compensation zone is saved).
        * When all the :class:`.Fault` were dealt with.

        It is also called by :meth:`.Accelerator.keep` method.

        Parameters
        ----------
        dat_file :
            Where the output ``DAT`` should be saved.
        export_phase :
            Which phase should be put in the output DAT file.
        save :
            If the output file should be created.

        Note
        ----
        LightWin rephases cavities if the first :class:`.Element`
        in ``self`` is not the first of the linac. This way, the beam enters
        each cavity with the intended phase in :class:`.TraceWin` (no effect
        if the phases are exported as relative phase).

        Raises
        ------
        NotImplementedError
            If ``which_phase`` is ``"as_in_original_dat"``.

        """
        if exported_phase in ("as_in_original_dat",):
            raise NotImplementedError
        self.files["dat_file"] = dat_file
        dat_filecontent = [
            instruction.to_line(which_phase=exported_phase, inplace=False)
            for instruction in self.files["elts_n_cmds"]
        ]
        if save:
            export_dat_filecontent(dat_filecontent, dat_file)

    @overload
    def take(self, ids: int, id_nature: Literal["cavity"]) -> FieldMap: ...

    @overload
    def take(
        self, ids: Sequence[int], id_nature: Literal["cavity"]
    ) -> list[FieldMap]: ...

    @overload
    def take(
        self, ids: Sequence[Sequence[int]], id_nature: Literal["cavity"]
    ) -> list[list[FieldMap]]: ...

    @overload
    def take(self, ids: int, id_nature: Literal["element"]) -> Element: ...

    @overload
    def take(
        self, ids: Sequence[int], id_nature: Literal["element"]
    ) -> list[Element]: ...

    @overload
    def take(
        self, ids: Sequence[Sequence[int]], id_nature: Literal["element"]
    ) -> list[list[Element]]: ...

    @overload
    def take(self, ids: str, id_nature: Literal["name"]) -> Element: ...

    @overload
    def take(
        self, ids: list[str], id_nature: Literal["name"]
    ) -> list[Element]: ...

    @overload
    def take(
        self, ids: list[list[str]], id_nature: Literal["name"]
    ) -> list[list[Element]]: ...

    @overload
    def take(
        self, ids: int, id_nature: Literal["section", "lattice"]
    ) -> list[Element]: ...

    @overload
    def take(
        self, ids: Sequence[int], id_nature: Literal["section", "lattice"]
    ) -> list[list[Element]]: ...

    def take(
        self,
        ids: ELEMENT_ID_T | ELEMENTS_ID_T | NESTED_ELEMENTS_ID,
        id_nature: ID_NATURE_T,
    ) -> (
        Element
        | list[Element]
        | list[list[Element]]
        | FieldMap
        | list[FieldMap]
        | list[list[FieldMap]]
    ):
        """Convert list of indexes or names to a list of :class:`.Element`."""
        if isinstance(ids, (Sequence, list)) and not isinstance(ids, str):
            return [self.take(idx, id_nature) for idx in ids]

        match id_nature:
            case "cavity":
                assert isinstance(ids, int)
                try:
                    output = self.l_cav[ids]
                except IndexError:
                    logging.error(
                        f"{ids = } is outside of list of elements of length "
                        f"{len(self)}"
                    )
                    raise IndexError

            case "element":
                assert isinstance(ids, int)
                try:
                    output = self[ids]
                except IndexError:
                    logging.error(
                        f"{ids = } is outside of list of cavities of length "
                        f"{len(self.l_cav)}"
                    )
                    raise IndexError
            case "name":
                name = ids
                assert isinstance(name, str)
                try:
                    output = first(
                        self, condition=lambda elt: elt.name == name
                    )
                except StopIteration:
                    logging.error(
                        f"No element named {name} was found in self."
                    )
                    raise StopIteration
            case "lattice":
                assert isinstance(ids, int)
                try:
                    output = self.by_lattice[ids]
                except IndexError as e:
                    msg = (
                        f"{ids = } is outside of list of lattices of length "
                        f"{len(self.by_lattice)}\n{e}"
                    )
                    logging.error(msg)
                    raise IndexError(msg)
            case "section":
                assert isinstance(ids, int)
                try:
                    output = self.by_section[ids]
                except IndexError as e:
                    msg = (
                        f"{ids = } is outside of list of sections of length "
                        f"{len(self.by_section)}\n{e}"
                    )
                    logging.error(msg)
                    raise IndexError(msg)
            case _:
                raise OSError(f"{id_nature = } not understood.")
        return output

    def pickle(
        self, pickler: MyPickler, path: Path | str | None = None
    ) -> Path:
        """Pickle (save) the object.

        This is useful for debug and temporary saves; do not use it for long
        time saving.

        """
        if path is None:
            path = self.files["accelerator_path"] / "list_of_elements.pkl"
        assert isinstance(path, Path)
        pickler.pickle(self, path)

        if isinstance(path, str):
            path = Path(path)
        return path

    @classmethod
    def from_pickle(cls, pickler: MyPickler, path: Path | str) -> Self:
        """Instantiate object from previously pickled file."""
        list_of_elements = pickler.unpickle(path)
        return list_of_elements  # type: ignore

    @property
    def files_info(self) -> FilesInfo:
        """Return the ``files`` attribute.

        .. deprecated::
            This is just an alias to the ``files`` dict; ``files_info`` should
            not be used anymore.

        """
        return self.files


def sumup_cavities(
    elts: ListOfElements, filter: Callable[[FieldMap], bool] | None = None
) -> pd.DataFrame:
    """Extract main cavities information."""
    columns = (
        "name",
        "status",
        "k_e",
        "phi_0_abs",
        "phi_0_rel",
        "v_cav_mv",
        "phi_s",
    )
    df = pd.DataFrame(
        [
            cav.get(*columns, to_deg=True, to_numpy=False, none_to_nan=True)
            for cav in elts.l_cav
            if (not filter or filter(cav))
        ],
        columns=columns,
    )
    return df
