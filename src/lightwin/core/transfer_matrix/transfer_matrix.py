"""Hold the transfer matrix along the linac.

.. todo::
    Check if it can be more efficient. Maybe store R_xx, R_yy, R_zz separately?

.. todo::
    Maybe transfer matrices should always be (6, 6)??

.. todo::
    ``_init_from`` methods in factory???

.. todo::
    The SimulationOutput.get method with transfer matrix components fails with
    :class:`.TraceWin` solver.

"""

import logging
from typing import Any

import numpy as np
from numpy.typing import NDArray

from lightwin.core.elements.element import ELEMENT_TO_INDEX_T, POS_T, Element
from lightwin.util.typing import GETTABLE_TRANSFER_MATRIX_T


class TransferMatrix:
    """Hold the ``(n, 6, 6)`` transfer matrix along the linac.

    .. note::
        When the simulation is 1D only, the values corresponding to the
        transverse planes are filled with ``np.nan``.

    Parameters
    ----------
    individual :
        Individual transfer matrices along the linac. Not defined if not
        provided at initialisation.
    cumulated :
        Cumulated transfer matrices along the linac.

    """

    def __init__(
        self,
        is_3d: bool,
        first_cumulated_transfer_matrix: NDArray[np.float64],
        element_to_index: ELEMENT_TO_INDEX_T,
        individual: NDArray[np.float64] | None = None,
        cumulated: NDArray[np.float64] | None = None,
    ) -> None:
        """Create the object and compute the cumulated transfer matrix.

        Parameters
        ----------
        is_3d :
            If the simulation is in 3d or not.
        first_cumulated_transfer_matrix :
            First transfer matrix.
        individual :
            Individual transfer matrices. The default is None, in which case
            the ``cumulated`` transfer matrix must be provided directly.
        cumulated :
            Cumulated transfer matrices. The default is None, in which case the
            ``individual`` transfer matrices must be given.
        element_to_index :
            Takes an :class:`.Element`, its name, ``'first'`` or ``'last'`` as
            argument, and returns corresponding index. Index should be the same
            in all the arrays attributes of this class: ``z_abs``,
            ``beam_parameters`` attributes, etc. Used to easily ``get`` the
            desired properties at the proper position.

        """
        self.is_3d = is_3d

        self.individual: NDArray[np.float64]
        if individual is not None:
            self.individual = individual
            n_points, cumulated = self._init_from_individual(
                individual, first_cumulated_transfer_matrix
            )

        else:
            n_points, cumulated = self._init_from_cumulated(
                cumulated, first_cumulated_transfer_matrix
            )

        self.n_points = n_points

        self.cumulated = cumulated
        self._element_to_index = element_to_index

    def has(self, key: str) -> bool:
        """Check if object has attribute named ``key``."""
        return hasattr(self, key)

    def get(
        self,
        *keys: GETTABLE_TRANSFER_MATRIX_T,
        elt: Element | str | None = None,
        pos: POS_T | None = None,
        to_numpy: bool = True,
        none_to_nan: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Get attributes from this class.

        Optionally, at a specific element/position.

        Parameters
        ----------
        *keys :
            Names of the desired attributes.
        elt :
            Element or its name where the value should be extracted.
        pos :
            Position in the element.
        to_numpy :
            Convert lists to NumPy arrays.
        none_to_nan :
            Replace ``None`` values with ``np.nan``.
        **kwargs :
            Ignored here, but accepted for compatibility.

        Returns
        -------
        Any
            Attribute(s) at the requested location.
        """
        out = []

        for key in keys:
            val = getattr(self, key, None)

            if elt is not None:
                idx = self._element_to_index(elt=elt, pos=pos)
                val = val[idx] if val is not None else None

            if none_to_nan and val is None:
                val = np.nan

            if to_numpy and isinstance(val, list):
                val = np.array(val)
            elif not to_numpy and isinstance(val, np.ndarray):
                val = val.tolist()

            out.append(val)

        return out[0] if len(out) == 1 else tuple(out)

    def get_old(
        self,
        *keys: GETTABLE_TRANSFER_MATRIX_T,
        elt: Element | str | None = None,
        pos: POS_T | None = None,
        **kwargs: Any,
    ) -> Any:
        """Get attributes from this class or its attributes.

        Note
        ----
        We do not define the ``to_numpy`` and ``none_to_nan`` keyword arguments
        here. As transfer matrices are 2D, we expect the user to want a numpy
        array with ``np.nan`` values where invalid.

        .. todo::
            I think could be more compact.

        Parameters
        ----------
        *keys :
            Name of the desired attributes.
        elt :
            If provided, return the attributes only at the considered
            :class:`.Element`.
        pos :
            If you want the attribute at the entry, exit, or in the whole
            :class:`.Element`.
        **kwargs :
            Other arguments passed to recursive getter.

        Returns
        -------
        out :
            Attribute(s) value(s).

        """
        out = [getattr(self, key, None) for key in keys]

        if elt is not None:
            idx = self._element_to_index(elt=elt, pos=pos)
            out = [val[idx] if val is not None else None for val in out]

        out = [
            (
                np.array(np.nan)
                if val is None
                else np.array(val) if isinstance(val, list) else val
            )
            for val in out
        ]

        return out[0] if len(out) == 1 else tuple(out)

    def _init_from_individual(
        self,
        individual: NDArray[np.float64],
        first_cumulated_transfer_matrix: NDArray[np.float64] | None,
    ) -> tuple[int, NDArray[np.float64]]:
        """Compute cumulated transfer matrix from individual.

        Parameters
        ----------
        individual :
            Individual transfer matrices along the linac.
        first_cumulated_transfer_matrix :
            First transfer matrix. It should be None if we study a linac
            from the start (``z_pos == 0.``), and should be the cumulated
            transfer matrix of the previous linac portion otherwise.

        Returns
        -------
        n_points :
            Number of mesh points along the linac.
        cumulated :
            Cumulated transfer matrices.

        """
        n_points = individual.shape[0] + 1
        if self.is_3d:
            shape = (n_points, 6, 6)
        else:
            shape = (n_points, 2, 2)

        if first_cumulated_transfer_matrix is None:
            first_cumulated_transfer_matrix = np.eye(shape[1])

        cumulated = self._compute_cumulated(
            first_cumulated_transfer_matrix, shape, self.is_3d, n_points
        )
        return n_points, cumulated

    def _init_from_cumulated(
        self,
        cumulated: NDArray[np.float64] | None,
        first_cumulated_transfer_matrix: NDArray[np.float64],
        tol: float = 1e-8,
    ) -> tuple[int, NDArray[np.float64]]:
        """Check that the given cumulated matrix is valid.

        Parameters
        ----------
        cumulated :
            Cumulated transfer matrices along the linac.
        first_cumulated_transfer_matrix :
            The first of the cumulated transfer matrices.
        tol :
            The max allowed difference between ``cumulated`` and
            ``first_cumulated_transfer_matrix`` when determining if they are
            the same or not.

        Returns
        -------
        n_points :
            Number of mesh points along the linac.
        cumulated :
            Cumulated transfer matrices.

        """
        if cumulated is None:
            logging.error(
                "You must provide at least one of the two arrays: individual "
                "transfer matrices or cumulated transfer matrices."
            )
            raise OSError("Wrong input")
        n_points = cumulated.shape[0]

        if (
            np.abs(cumulated[0] - first_cumulated_transfer_matrix)
        ).any() > tol:
            n_points += 1
            cumulated = np.vstack(
                (first_cumulated_transfer_matrix[np.newaxis], cumulated)
            )

        return n_points, cumulated

    def _compute_cumulated(
        self,
        first_cumulated_transfer_matrix: NDArray[np.float64],
        shape: tuple[int, int, int],
        is_3d: bool,
        n_points: int,
    ) -> NDArray[np.float64]:
        """Compute cumulated transfer matrix from individual.

        Parameters
        ----------
        first_cumulated_transfer_matrix :
            First transfer matrix. It should be eye matrix if we study a linac
            from the start (``z_pos == 0.``), and should be the cumulated
            transfer matrix of the previous linac portion otherwise.
        shape :
            Shape of the output ``cumulated`` array.
        is_3d :
            If the simulation is in 3D or not.
        n_points :
            Number of mesh points along the linac.

        Returns
        -------
        cumulated :
            Cumulated transfer matrix.

        .. todo::
            I think the 3D/1D handling may be smarter?

        """
        cumulated = np.full(shape, np.nan)
        cumulated[0] = first_cumulated_transfer_matrix

        for i in range(n_points - 1):
            cumulated[i + 1] = self.individual[i] @ cumulated[i]

        if is_3d:
            return cumulated

        cumulated_1d = cumulated
        cumulated = np.full((n_points, 6, 6), np.nan)
        cumulated[:, 4:, 4:] = cumulated_1d
        return cumulated

    @property
    def r_xx(self) -> NDArray[np.float64]:
        """Return the transfer matrix of :math:`[x-x']` plane."""
        return self.cumulated[:, :2, :2]

    @r_xx.setter
    def r_xx(self, r_xx: NDArray[np.float64]) -> None:
        """Set the transfer matrix of :math:`[x-x']` plane."""
        self.cumulated[:, :2, :2] = r_xx

    @property
    def r_yy(self) -> NDArray[np.float64]:
        """Return the transfer matrix of :math:`[y-y']` plane."""
        return self.cumulated[:, 2:4, 2:4]

    @r_yy.setter
    def r_yy(self, r_yy: NDArray[np.float64]) -> None:
        """Set the transfer matrix of :math:`[y-y']` plane."""
        self.cumulated[:, 2:4, 2:4] = r_yy

    @property
    def r_zz(self) -> NDArray[np.float64]:
        r"""Return the transfer matrix of :math:`[z-\delta]` plane.

        .. deprecated:: v3.2.2.3
            Use ``r_zdelta`` instead. Although it is called ``r_zz`` in the
            TraceWin doc, it is a transfer matrix in the :math:`[z-\delta]`
            plane.

        """
        return self.cumulated[:, 4:, 4:]

    @r_zz.setter
    def r_zz(self, r_zz: NDArray[np.float64]) -> None:
        r"""Set the transfer matrix of :math:`[z-\delta]` plane.

        .. deprecated:: v3.2.2.3
            Use ``r_zdelta`` instead. Although it is called ``r_zz`` in the
            TraceWin doc, it is a transfer matrix in the :math:`[z-\delta]`
            plane.

        """
        self.cumulated[:, 4:, 4:] = r_zz

    @property
    def r_zdelta(self) -> NDArray[np.float64]:
        r"""Return the transfer matrix of :math:`[z-\delta]` plane."""
        return self.cumulated[:, 4:, 4:]

    @r_zdelta.setter
    def r_zdelta(self, r_zdelta: NDArray[np.float64]) -> None:
        r"""Set the transfer matrix of :math:`[z-\delta]` plane."""
        self.cumulated[:, 4:, 4:] = r_zdelta
