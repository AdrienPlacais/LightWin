"""Define a factory to easily create :class:`.Accelerator`."""

import logging
from pathlib import Path
from typing import Any, Sequence
from warnings import warn

from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.util.typing import BeamKwargs


class AcceleratorFactory:
    """A class to create accelerators."""

    def __init__(
        self,
        beam_calculators: BeamCalculator | Sequence[BeamCalculator | None],
        files: dict[str, Any],
        beam: BeamKwargs,
        **kwargs,
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
        self.beam_calculators = beam_calculators

        main_beam_calculator = beam_calculators[0]
        if main_beam_calculator is None:
            raise ValueError("Need at least one working BeamCalculator.")
        #: :class:`.BeamCalculator` that will be used to find compensation
        #: settings.
        self.main_beam_calculator = main_beam_calculator
        self._elts_factory = main_beam_calculator.list_of_elements_factory
        self._beam = beam

    def _create_instances(
        self, n_objects: int, is_reference: bool
    ) -> list[Accelerator]:
        r"""Create object.

        Parameters
        ----------
        n_objects :
            Number of objects to create.
        is_reference :
            If the reference accelerator should be created.

        """
        accelerator_paths = self._create_output_dirs(
            n_objects=n_objects, with_reference=is_reference
        )
        name = "Working" if is_reference else "Broken"
        accelerators: list[Accelerator] = []
        for path in accelerator_paths:
            acc = Accelerator(
                name=name,
                dat_file=self.dat_file,
                accelerator_path=path,
                list_of_elements_factory=self._elts_factory,
                **self._beam,
            )
            self._check_consistency_reference_phase_policies(acc.l_cav)
            accelerators.append(acc)
        return accelerators

    def create_nominal(self) -> Accelerator:
        """Create the nominal linac."""
        return self._create_instances(n_objects=1, is_reference=True)[0]

    def create_failed(self, n_objects: int) -> list[Accelerator]:
        """Create failed linac(s)."""
        return self._create_instances(n_objects, is_reference=False)

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

    def _create_output_dirs(
        self, n_objects: int, with_reference: bool = True
    ) -> list[Path]:
        """Create the proper out directories for every :class:`.Accelerator`.

        The default structure looks like::

           YYYY.MM.DD_HHhMM_SSs_MILLIms/
           ├── 000000_ref
           │   ├── 0_Envelope1D/
           │   └── 1_TraceWin/
           ├── 000001
           │   ├── 0_Envelope1D/
           │   └── 1_TraceWin/
           ├── 000002
           │   ├── 0_Envelope1D/
           │   └── 1_TraceWin/
           ├── 000003
           │   ├── 0_Envelope1D/
           │   └── 1_TraceWin/
           └── lightwin.log

        - The main ``YYYY.MM.DD_HHhMM_SSs_MILLIms/`` directory is created at
          the same location as the original ``DAT`` file. You can override its
          name with the ``project_folder`` key in the ``[files]`` ``TOML``
          section.

        - In every ``accelerator_path`` (eg ``000002/``), you will find one
          directory per :class:`.BeamCalculator`. In this example, compensation
          settings were found with :class:`.Envelope1D` and a second simulation
          was made with :class:`.TraceWin`.

        Parameters
        ----------
        n_objects :
            Number of :class:`.Accelerator` to create.
        with_reference :
            If first directory should be the nominal dir called ``000000_ref/``
            .

        Returns
        -------
            Output path for every accelerator: ``000000_ref/`` (if
            ``with_reference``), ``000001/``, ...

        """
        accelerator_paths: list[Path] = []
        first_index = 0 if with_reference else 1
        for i in range(first_index, n_objects + first_index):
            path = self.project_folder / f"{i:06d}"
            if i == 0:
                path = path.with_name(f"{path.name}_ref")

            path.mkdir(parents=True, exist_ok=True)
            accelerator_paths.append(path)

            for beam_calculator in self.beam_calculators:
                if beam_calculator is None:
                    continue
                beam_calculator_dir = path / beam_calculator.out_folder
                beam_calculator_dir.mkdir(parents=True, exist_ok=True)
        return accelerator_paths


class NoFault(AcceleratorFactory):
    """Create single accelerator without failure.

    .. deprecated:: 0.15.0
       Prefer :class:`AcceleratorFactory`.

    """

    def __init__(self, *args, **kwargs) -> None:
        warn(
            "The class NoFault is deprecated. Prefer using AcceleratorFactory.",
            DeprecationWarning,
            stacklevel=2,
        )
        return super().__init__(*args, **kwargs)

    def run(self, *args, **kwargs) -> Accelerator:
        return self.create_nominal()


class WithFaults(AcceleratorFactory):
    """Create accelerators with failures.

    .. deprecated:: 0.15.0
       Prefer :class:`AcceleratorFactory`.

    """

    def __init__(self, *args, wtf: dict[str, Any], **kwargs) -> None:
        warn(
            "The class WithFaults is deprecated. Prefer using "
            "AcceleratorFactory.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._wtf = wtf
        return super().__init__(*args, **kwargs)

    def run_all(self, *args, **kwargs) -> list[Accelerator]:
        reference = self.create_nominal()
        n_objects = len(self._wtf["failed"])
        return [reference] + self.create_failed(n_objects)
