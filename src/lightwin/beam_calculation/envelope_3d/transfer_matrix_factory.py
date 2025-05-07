"""Provide an easy way to generate :class:`.TransferMatrix`."""

import logging
from typing import Any

import numpy as np

from lightwin.core.elements.element import ELEMENT_TO_INDEX_T
from lightwin.core.transfer_matrix.factory import TransferMatrixFactory
from lightwin.core.transfer_matrix.transfer_matrix import TransferMatrix


class TransferMatrixFactoryEnvelope3D(TransferMatrixFactory):
    """Provide a method for easy creation of :class:`.TransferMatrix`."""

    def _preprocess(
        self, single_elt_results: list[dict[str, Any]]
    ) -> np.ndarray:
        """Preprocess the data given by the :class:`.BeamCalculator`."""
        individual = [
            results["transfer_matrix"][i]
            for results in single_elt_results
            for i in range(results["transfer_matrix"].shape[0])
        ]
        return np.array(individual)

    def run(
        self,
        first_cumulated_transfer_matrix: np.ndarray,
        single_elts_results: list[dict[str, Any]],
        element_to_index: ELEMENT_TO_INDEX_T,
    ) -> TransferMatrix:
        """Create the transfer matrix from a simulation.

        Parameters
        ----------
        first_cumulated_transfer_matrix :
            Cumulated transfer matrix at beginning of :class:`.ListOfElements`
            under study.
        single_elts_results :
            Results of the solver.

        Returns
        -------
        transfer_matrix
            Holds all cumulated transfer matrices in all the planes.

        """
        if first_cumulated_transfer_matrix.shape != (6, 6):
            logging.warning(
                "Here I should initialize TransferMatrix with an initial "
                "transfer matrix, but I have a shape mismatch. It is ok for "
                "now."
            )
            first_cumulated_transfer_matrix = None
        individual = self._preprocess(single_elts_results)
        transfer_matrix = TransferMatrix(
            individual=individual,
            first_cumulated_transfer_matrix=first_cumulated_transfer_matrix,
            is_3d=self.is_3d,
            element_to_index=element_to_index,
        )
        return transfer_matrix
