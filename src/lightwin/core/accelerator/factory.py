"""Define a factory to easily create :class:`.Accelerator`."""

import logging
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.util.typing import BeamKwargs


@dataclass
class AcceleratorFactory(ABC):
    """A class to create accelerators."""

    def __init__(
        self,
        beam_calculators: BeamCalculator | Sequence[BeamCalculator | None],
        files: dict[str, Any],
        beam: BeamKwargs,
        **kwargs: dict,
    ) -> None:
        """Facilitate creation of :class:`.Accelerator` objects.

        Parameters
        ----------
        beam_calculators :
            Objects that will compute propagation of the beam.
        files :
            Configuration entries for the input/output paths.
        beam :
            Configuration dictionary holding the initial beam parameters.
        kwargs :
            Other configuration dictionaries.

        """
        self.dat_file = files["dat_file"]
        self.project_folder = files["project_folder"]

        if isinstance(beam_calculators, BeamCalculator):
            beam_calculators = (beam_calculators,)
        assert (
            beam_calculators[0] is not None
        ), "Need at least one working BeamCalculator."
        self.beam_calculators = beam_calculators
        self._beam = beam

    def run(self, *args, **kwargs) -> Accelerator:
        """Create the object."""
        accelerator = Accelerator(*args, **kwargs)
        self._check_consistency_reference_phase_policies(accelerator.l_cav)
        return accelerator

    def _generate_folders_tree_structure(
        self,
        out_folders: Sequence[Path],
        n_simulations: int,
    ) -> list[Path]:
        """Create the proper folders for every :class:`.Accelerator`.

        The default structure is:

        - ``where_original_dat_is/``

          - ``YYYY.MM.DD_HHhMM_SSs_MILLIms/``     <- ``project_folder``
            (absolute)

            - ``000000_ref/``                     <- ``accelerator_path``
              (absolute)

              - ``0_FirstBeamCalculatorName/``    <- ``out_folder`` (relative)
              - (``1_SecondBeamCalculatorName/``) <- ``out_folder`` (relative)

            - ``000001/``

              - ``0_FirstBeamCalculatorName/``
              - (``1_SecondBeamCalculatorName/``)

            - ``000002/``

              - ``0_FirstBeamCalculatorName/``
              - (``1_SecondBeamCalculatorName/``)

            - etc

        Parameters
        ----------
        out_folders :
            Name of the folders that will store outputs. By default, it is the
            name of the solver, preceeded by its position in the list of
            :class:`.BeamCalculator`.

        """
        accelerator_paths = [
            self.project_folder / f"{i:06d}" for i in range(n_simulations)
        ]
        accelerator_paths[0] = accelerator_paths[0].with_name(
            f"{accelerator_paths[0].name}_ref"
        )
        for accel_path in accelerator_paths:
            for out_folder in out_folders:
                path = accel_path / out_folder
                path.mkdir(parents=True, exist_ok=True)
        return accelerator_paths

    def _check_consistency_reference_phase_policies(
        self, cavities: Sequence[FieldMap]
    ) -> None:
        """Check that solvers phases are consistent with ``DAT`` file."""
        if len(cavities) == 0:
            return
        beam_calculators = [x for x in self.beam_calculators if x is not None]
        policies = {
            beam_calculator: beam_calculator.reference_phase_policy
            for beam_calculator in beam_calculators
        }

        n_unique = len(set(policies.values()))
        if n_unique > 1:
            logging.warning(
                "The different BeamCalculator objects have different "
                "reference phase policies. This may lead to inconsistencies "
                f"when cavities fail.\n{policies = }"
            )
            return

        references = {x.cavity_settings.reference for x in cavities}
        if len(references) > 1:
            logging.info(
                "The cavities do not all have the same reference phase."
            )


class NoFault(AcceleratorFactory):
    """Factory used to generate a single accelerator, no faults."""

    def __init__(
        self,
        beam_calculators: BeamCalculator,
        files: dict[str, Any],
        beam: BeamKwargs,
        **kwargs: dict,
    ) -> None:
        """Facilitate creation of :class:`.Accelerator`.

        Parameters
        ----------
        beam_calculators :
            A unique object to compute propagation of the field. Even if there
            is a ``s`` at the end of the variable name.
        files :
            Configuration entries for the input/output paths.
        beam :
            Configuration dictionary holding the initial beam parameters.
        kwargs :
            Other configuration dictionaries.

        """
        super().__init__(
            beam_calculators=beam_calculators, files=files, beam=beam, **kwargs
        )

    @property
    def beam_calculator(self) -> BeamCalculator:
        """Shortcut to get the only existing :class:`.BeamCalculator`."""
        return self.beam_calculators[0]

    def run(self, *args, **kwargs) -> Accelerator:
        """Create a single accelerator."""
        out_folders = (self.beam_calculator.out_folder,)
        accelerator_path = self._generate_folders_tree_structure(
            out_folders,
            n_simulations=1,
        )[0]
        list_of_elements_factory = (
            self.beam_calculator.list_of_elements_factory
        )
        name = "Working"

        accelerator = super().run(
            name=name,
            dat_file=self.dat_file,
            accelerator_path=accelerator_path,
            list_of_elements_factory=list_of_elements_factory,
            **self._beam,
        )
        return accelerator


class StudyWithoutFaultsAcceleratorFactory(NoFault):
    """Alias for :class:`.NoFault`."""


class WithFaults(AcceleratorFactory):
    """Factory used to generate several accelerators for a fault study."""

    def __init__(
        self,
        beam_calculators: BeamCalculator | Sequence[BeamCalculator | None],
        files: dict[str, Any],
        beam: BeamKwargs,
        wtf: dict[str, Any],
        **kwargs: dict,
    ) -> None:
        """Facilitate creation of :class:`.Accelerator` objects.

        Parameters
        ----------
        beam_calculators :
            Objects that will compute propagation of the beam.
        files :
            Configuration entries for the input/output paths.
        beam :
            Configuration dictionary holding the initial beam parameters.
        wtf :
            Dictionary holding the information on what to fit.
        kwargs :
            Other configuration dictionaries.

        """
        super().__init__(
            beam_calculators=beam_calculators, files=files, beam=beam, **kwargs
        )
        self.failed = wtf["failed"]
        self._n_simulations = 0

    @property
    def n_simulations(self) -> int:
        """Determine how much simulations will be made."""
        if self._n_simulations > 0:
            return self._n_simulations

        self._n_simulations = 1

        if self.failed is not None:
            self._n_simulations += len(self.failed)

        return self._n_simulations

    def run_all(self, **kwargs) -> list[Accelerator]:
        """Create the required Accelerators as well as their output folders."""
        out_folders = [
            beam_calculator.out_folder
            for beam_calculator in self.beam_calculators
            if beam_calculator is not None
        ]

        accelerator_paths = self._generate_folders_tree_structure(
            out_folders, n_simulations=self.n_simulations
        )

        names = [
            "Working" if i == 0 else "Broken"
            for i in range(self.n_simulations)
        ]

        list_of_elements_factory = self.beam_calculators[
            0
        ].list_of_elements_factory

        accelerators = [
            self.run(
                name=name,
                dat_file=self.dat_file,
                accelerator_path=accelerator_path,
                list_of_elements_factory=list_of_elements_factory,
                **self._beam,
            )
            for name, accelerator_path in zip(names, accelerator_paths)
        ]
        return accelerators


class FullStudyAcceleratorFactory(WithFaults):
    """Alias for :class:`WithFaults`."""
