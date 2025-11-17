"""Define a class to easily generate the :class:`.SimulationOutput`.

This class should be subclassed by every :class:`.BeamCalculator` to match its
own specific outputs.

"""

import logging
from abc import ABC, ABCMeta, abstractmethod
from dataclasses import dataclass
from functools import partial

from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.elements.element import ELEMENT_TO_INDEX_T, Element
from lightwin.core.list_of_elements.helper import equivalent_elt
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.util.typing import GET_ELT_ARG_T, POS_T, BeamKwargs


@dataclass
class SimulationOutputFactory(ABC):
    """A base class for creation of :class:`.SimulationOutput`."""

    _is_3d: bool
    _is_multipart: bool
    _solver_id: str
    _beam_kwargs: BeamKwargs

    def __post_init__(self) -> None:
        """Create the factories.

        The created factories are :class:`.TransferMatrixFactory` and
        :class:`.BeamParametersFactory`. The sub-class that is used is declared
        in :meth:`._transfer_matrix_factory_class` and
        :meth:`._beam_parameters_factory_class`.

        """
        self.transfer_matrix_factory = self._transfer_matrix_factory_class(
            self._is_3d
        )
        self.beam_parameters_factory = self._beam_parameters_factory_class(
            self._is_3d,
            self._is_multipart,
            beam_kwargs=self._beam_kwargs,
        )

    @property
    @abstractmethod
    def _transfer_matrix_factory_class(self) -> ABCMeta:
        """Declare the **class** of the transfer matrix factory."""

    @property
    @abstractmethod
    def _beam_parameters_factory_class(self) -> ABCMeta:
        """Declare the **class** of the beam parameters factory."""

    @abstractmethod
    def run(self, elts: ListOfElements, *args, **kwargs) -> SimulationOutput:
        """Create the :class:`.SimulationOutput`."""
        pass

    def _generate_element_to_index_func(
        self, elts: ListOfElements
    ) -> ELEMENT_TO_INDEX_T:
        """Create the func to easily get data at proper mesh index."""
        shift = elts[0].beam_calc_param[self._solver_id].s_in
        element_to_index = partial(
            _element_to_index,
            _elts=elts,
            _shift=shift,
            _solver_id=self._solver_id,
        )
        return element_to_index


def _element_to_index(
    _elts: ListOfElements,
    _shift: int,
    _solver_id: str,
    elt: Element | str | GET_ELT_ARG_T,
    pos: POS_T | None = None,
    return_elt_idx: bool = False,
    handle_missing_elt: bool = False,
) -> int | slice:
    """Convert ``elt`` and ``pos`` into a mesh index.

    This way, you can call ``get('w_kin', elt='FM5', pos='out')`` and
    systematically get the energy at the exit of FM5, whatever the
    :class:`.BeamCalculator` or the mesh size is.

    .. todo::
        different functions, for different outputs. At least, an
        _element_to_index and a _element_to_indexes. And also a different
        function for when the index element is desired.

    Parameters
    ----------
    _elts :
        List of :class:`.Element` where ``elt`` should be. Must be set by a
        ``functools.partial``.
    _shift :
        Mesh index of first :class:`.Element`. Used when the first
        :class:`.Element` of ``_elts`` is not the first of the
        :class:`.Accelerator`. Must be set by ``functools.partial``.
    _solver_id :
        Name of the solver, to identify and take the proper
        :class:`.ElementBeamCalculatorParameters`.
    elt :
        Element of which you want the index.
    pos :
        Index of entry or exit of the :class:`.Element`. If None, return full
        indexes array.
    return_elt_idx :
        If True, the returned index is the position of the element in
        ``_elts``.
    handle_missing_elt :
        Look for an equivalent element when ``elt`` is not in ``_elts``.

    Returns
    -------
    int | slice
        Index of range of indexes where ``elt`` is.

    """
    if isinstance(elt, str):
        elt = equivalent_elt(elts=_elts, elt=elt)
    elif elt not in _elts and handle_missing_elt:
        logging.debug(
            f"{elt = } is not in _elts. Trying to take an element in _elts "
            "with the same name..."
        )
        elt = equivalent_elt(elts=_elts, elt=elt)

    beam_calc_param = elt.beam_calc_param[_solver_id]
    if return_elt_idx:
        return _elts.index(elt)

    if pos is None:
        return slice(
            beam_calc_param.s_in - _shift, beam_calc_param.s_out - _shift + 1
        )
    if pos == "in":
        return beam_calc_param.s_in - _shift
    if pos == "out":
        return beam_calc_param.s_out - _shift

    logging.error(f"{pos = }, while it must be 'in', 'out' or None")
    raise OSError(f"{pos = }, while it must be 'in', 'out' or None")
