"""Define a factory to easily create :class:`.Accelerator`."""

import logging
from pathlib import Path
from typing import Any, Sequence
from warnings import warn

from lightwin.beam_calculation.beam_calculator import BeamCalculator
from lightwin.core.accelerator.accelerator import (
    ACCELERATOR_STATUS_T,
    Accelerator,
)
from lightwin.core.elements.field_maps.field_map import FieldMap
from lightwin.failures.strategy import determine_cavities
from lightwin.util.pickling import MyCloudPickler, MyPickler
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
        self._pickle_paths = files.get("pickle_paths", {})

        if isinstance(beam_calculators, BeamCalculator):
            beam_calculators = (beam_calculators,)
        self.beam_calculators = beam_calculators

        main_beam_calculator = beam_calculators[0]
        if main_beam_calculator is None:
            raise ValueError("Need at least one working BeamCalculator.")
        self.main_beam_calculator = main_beam_calculator
        self._elts_factory = main_beam_calculator.list_of_elements_factory
        self._beam = beam

        self._pickler: MyPickler | None = None

    @property
    def pickler(self) -> MyPickler:
        if self._pickler is None:
            self._pickler = MyCloudPickler()
        return self._pickler

    def create_all(
        self, wtf: dict[str, Any] | None = None
    ) -> tuple[list[Accelerator], dict[str, Any] | None]:
        """Create reference and broken accelerators.

        Also loads any additional pre-computed accelerators from pickle files
        specified in the configuration.

        Parameters
        ----------
        wtf :
            "What To Fail/Fit" configuration. Can contain automatic fault
            generation parameters that will be resolved into specific cavity
            failures.

        Returns
        -------
        accelerators :
            Reference accelerator (index 0), fault scenario accelerators
            (if any), followed by any additional pickled accelerators.
        updated_wtf :
            The resolved ``wtf`` configuration with explicit cavity failures.
            None if no wtf was provided.

        """
        reference = self.create_reference()
        accelerators = [reference]
        updated_wtf = None

        if wtf is not None:
            n_scenarios, updated_wtf = determine_cavities(reference.elts, wtf)
            broken = self.create_all_broken(n_scenarios)
            accelerators.extend(broken)

        additional = self._load_additional_pickles({"Reference", "Solution"})
        if len(additional) > 0:
            logging.warning(
                "Behavior of additional Accelerator is not well defined. In "
                "particular if there are several FaultScenario."
            )
        accelerators.extend(additional)

        return accelerators, updated_wtf

    def create_reference(self) -> Accelerator:
        """Create the reference (nominal) accelerator.

        Returns
        -------
            The nominal accelerator without failures.

        """
        return self._create_one_accelerator(
            name="Reference",
            status="reference",
            output_path=self.project_folder / "000000_ref",
        )

    def create_all_broken(self, n_scenarios: int) -> list[Accelerator]:
        """Create multiple broken accelerators.

        Parameters
        ----------
        n_scenarios :
            Number of broken accelerators to create. This is also the number
            of :class:`.FaultScenario` we will create.

        Returns
        -------
            List of accelerators, one per fault scenario.

        """
        return [
            self._create_one_accelerator(
                name="Solution",
                status="broken",
                output_path=self.project_folder / f"{i + 1:06d}",
            )
            for i in range(n_scenarios)
        ]

    def _create_one_accelerator(
        self, name: str, status: ACCELERATOR_STATUS_T, output_path: Path
    ) -> Accelerator:
        """Create or load a single accelerator.

        Parameters
        ----------
        name :
            Accelerator name (e.g., "Reference", "Solution").
        status :
            Current status design.
        output_path :
            Path where accelerator data will be stored.

        Returns
        -------
            Loaded from pickle if available, otherwise freshly created.

        """
        pickle_path = self._get_pickle_path(name)

        if pickle_path is not None:
            accelerator = self._load_from_pickle(name, pickle_path)
            if accelerator is not None:
                return accelerator

        return self._build_accelerator(name, status, output_path, pickle_path)

    def _build_accelerator(
        self,
        name: str,
        status: ACCELERATOR_STATUS_T,
        output_path: Path,
        pickle_path: Path | None,
    ) -> Accelerator:
        """Build a new accelerator from scratch.

        Parameters
        ----------
        name :
            Accelerator name.
        status :
            Current status design.
        output_path :
            Path where accelerator data will be stored.
        pickle_path :
            Optional path where accelerator will be pickled after creation.

        Returns
        -------
            Newly created accelerator instance.

        """
        self._create_output_directories(output_path)

        info = f"Creating {name} accelerator"
        if pickle_path:
            info += f" (will save to {pickle_path})"
        logging.info(info)

        accelerator = Accelerator(
            name=name,
            status=status,
            dat_file=self.dat_file,
            accelerator_path=output_path,
            list_of_elements_factory=self._elts_factory,
            pickle_path=pickle_path,
            **self._beam,
        )

        self._check_consistency_reference_phase_policies(accelerator.l_cav)
        return accelerator

    def _create_output_directories(self, output_path: Path) -> None:
        """Create output directory structure for an accelerator.

        Creates the main accelerator directory and subdirectories for each
        beam calculator.

        The default structure will look like::

           YYYY.MM.DD_HHhmm_SSs_MILLIms/
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
            Base path for the accelerator's output files.

        """
        output_path.mkdir(parents=True, exist_ok=True)

        for beam_calculator in self.beam_calculators:
            if beam_calculator is None:
                continue
            beam_calculator_dir = output_path / beam_calculator.out_folder
            beam_calculator_dir.mkdir(parents=True, exist_ok=True)

    def _get_pickle_path(self, name: str) -> Path | None:
        """Get the pickle path for a named accelerator.

        Parameters
        ----------
        name :
            Accelerator name to look up in pickle paths configuration.

        Returns
        -------
            Resolved absolute path if configured, None otherwise.

        """
        pickle_path_str = self._pickle_paths.get(name)
        if pickle_path_str is None:
            return None
        return Path(pickle_path_str).resolve().absolute()

    def _load_from_pickle(
        self, name: str, pickle_path: Path
    ) -> Accelerator | None:
        """Load accelerator from pickle file if it exists.

        Parameters
        ----------
        name :
            Accelerator name for logging.
        pickle_path :
            Path to pickle file.

        Returns
        -------
            Loaded accelerator if file exists, None otherwise.

        """
        if not pickle_path.is_file():
            return None

        logging.info(f"Loading {name} from pickle: {pickle_path}")
        return Accelerator.from_pickle(
            self.pickler, pickle_path, linac_id=name
        )

    def _load_additional_pickles(
        self, used_names: set[str]
    ) -> list[Accelerator]:
        """Load accelerators from unused pickle paths.

        Parameters
        ----------
        used_names :
            Names already used for Reference/Solution accelerators.

        Returns
        -------
            Additional accelerators loaded from pickle files.

        """
        additional = []

        for name in self._pickle_paths:
            if name in used_names:
                continue

            pickle_path = self._get_pickle_path(name)
            if pickle_path is None:
                continue

            accelerator = self._load_from_pickle(name, pickle_path)
            if accelerator is None:
                logging.debug(
                    f"Skipping '{name}': pickle file does not exist at "
                    "{pickle_path}"
                )
                continue

            logging.info(
                f"Loading additional accelerator '{name}' from pickle"
            )
            additional.append(accelerator)

        return additional

    def _check_consistency_reference_phase_policies(
        self, cavities: Sequence[FieldMap]
    ) -> None:
        """Check that solvers phases are consistent with ``DAT`` file.

        Parameters
        ----------
        cavities :
            Sequence of cavity field maps to check.

        """
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

    # =========================================================================
    # Deprecated kept for backward compatibility.
    # =========================================================================
    def create_nominal(self) -> Accelerator:
        """Create the nominal linac.

        .. deprecated:: 0.15.1
           Prefer :meth:`.create_reference`.

        """
        warn(
            "The method create_nominal is deprecated. Prefer using "
            "create_reference.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.create_reference()

    def create_failed(self, n_objects: int) -> list[Accelerator]:
        """Create failed linac(s).

        .. deprecated:: 0.15.1
           Prefer :meth:`.create_all_broken`.

        """
        warn(
            "The method create_failed is deprecated. Prefer using "
            "create_all_broken.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.create_all_broken(n_scenarios=n_objects)


# =========================================================================
# Deprecated kept for backward compatibility.
# =========================================================================
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
        return self.create_reference()


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
        reference = self.create_reference()
        n_objects = len(self._wtf["failed"])
        return [reference] + self.create_all_broken(n_objects)
