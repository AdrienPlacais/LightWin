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
        #: Parsed dictionary holding path to the different pickles. Typical
        #: structure:
        #:
        #: .. code-block:: toml
        #:
        #:    {
        #:        "Reference": "reference.pkl",
        #:        "scenarios": {
        #:            # Scenario 1: pre-computed solution (skips optimization)
        #:            1: {"Solution": "solution-000001.pkl"},
        #:            # Scenario 2: alternatives with custom names
        #:            # (optimization still runs, the pickled Accelerators
        #:            # will be appended)
        #:            2: {
        #:                "Solution": None,
        #:                "Conservative approach": "design-conservative.pkl",
        #:                "Aggressive tuning": "design-aggressive.pkl",
        #:            },
        #:            # Scenario 3: solution + alternatives
        #:            3: {
        #:                "Solution": "solution-000003.pkl",
        #:                "Tweaked design": "tweaked.pkl",
        #:                "Experimental config": "experimental.pkl",
        #:            }
        #:        }
        #:    }
        #:
        self._pickle_paths = self._parse_pickle_config(
            files.get("pickle_paths", {})
        )

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
    ) -> tuple[dict[int, list[Accelerator]], dict[str, Any] | None]:
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
            Dictionary where keys are :class:`.FaultScenario` indexes, and
            values are lists of corresponding :class:`.Accelerator`. First
            index corresponds to reference accelerator (no failure).
        updated_wtf :
            The resolved ``wtf`` configuration with explicit cavity failures.
            None if no wtf was provided.

        """
        reference = self.create_reference()
        accelerators = {0: [reference]}
        updated_wtf = None

        if wtf is not None:
            n_scenarios, updated_wtf = determine_cavities(reference.elts, wtf)
            accelerators.update(self.create_all_broken(n_scenarios))

        additional = self._load_additional_pickles(
            reserved_names={"Reference", "Solution"}
        )
        if len(additional) > 0:
            logging.warning(
                "Behavior of additional Accelerator is not well defined. In "
                "particular if there are several FaultScenario."
            )

        for index in accelerators:
            to_add = additional.get(index)
            if to_add is None:
                continue
            accelerators[index].extend(to_add)

        return accelerators, updated_wtf

    def create_reference(self) -> Accelerator:
        """Unpickle or create from scratch the reference (nominal) accelerator.

        Returns
        -------
            The nominal accelerator without failures.

        """
        return self._create_one_accelerator(
            name="Reference",
            status="reference",
            index=0,
            output_path=self.project_folder / "000000_ref",
        )

    def create_all_broken(
        self, n_scenarios: int
    ) -> dict[int, list[Accelerator]]:
        """Unpickle or create from scratch several broken accelerators.

        Parameters
        ----------
        n_scenarios :
            Number of broken accelerators to create. This is also the number
            of :class:`.FaultScenario` we will create.

        Returns
        -------
            Dict associating :class:`.FaultScenario` index to corresponding
            broken :class:`.Accelerator`.

        """
        return {
            i: [
                self._create_one_accelerator(
                    name="Solution",
                    status="broken",
                    index=i,
                    output_path=self.project_folder / f"{i:06d}",
                )
            ]
            for i in range(1, n_scenarios + 1)
        }

    def _create_one_accelerator(
        self,
        name: str,
        status: ACCELERATOR_STATUS_T,
        index: int,
        output_path: Path,
    ) -> Accelerator:
        """Create or load a single accelerator.

        Parameters
        ----------
        name :
            Accelerator name (e.g., ``"Reference"``, ``"Solution"``).
        status :
            Current status design.
        index :
            Corresponding :class:`.FaultScenario` index. A null index is
            reserved for reference accelerator.
        output_path :
            Path where accelerator data will be stored.

        Returns
        -------
            Loaded from pickle if available, otherwise freshly created.

        """
        pickle_path = self._get_pickle_path(name, index)

        if pickle_path is not None:
            accelerator = self._load_from_pickle(
                name, index=index, pickle_path=pickle_path
            )
            if accelerator is not None:
                logging.info(
                    f"Created {accelerator.id} Accelerator by unpickling "
                    f"'{pickle_path}'."
                )
                return accelerator

        accelerator = self._build_accelerator(
            name,
            status,
            index=index,
            output_path=output_path,
            pickle_path=pickle_path,
        )
        info = f"Created {accelerator.id} Accelerator"
        if pickle_path:
            info += f" (will be pickled to '{pickle_path}')"
        logging.info(info + ".")
        return accelerator

    # =========================================================================
    # Build Accelerator from scratch
    # =========================================================================
    def _build_accelerator(
        self,
        name: str,
        status: ACCELERATOR_STATUS_T,
        index: int,
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
        index :
            Corresponding :class:`.FaultScenario` index. A null index is
            reserved for reference accelerator.
        output_path :
            Path where accelerator data will be stored.
        pickle_path :
            Optional path where accelerator will be pickled after creation.

        Returns
        -------
            Newly created accelerator instance.

        """
        self._create_output_directories(output_path)

        accelerator = Accelerator(
            name=name,
            status=status,
            index=index,
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
            beam_calculator_dir = output_path / beam_calculator.id
            beam_calculator_dir.mkdir(parents=True, exist_ok=True)

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
    # Related to pickling/unpickling Accelerators
    # =========================================================================
    def _parse_pickle_config(
        self, pickle_config: dict[str, Any]
    ) -> dict[str, str | dict[int, dict[str, str]]]:
        """Parse pickle paths configuration from ``TOML``.

        Note
        ----
        When a Reference/Solution ``PKL`` is provided but does not exist,
        the associated :class:`.Accelerator` will be pickled at the end of
        the simulation.

        Parameters
        ----------
        pickle_config :
            Configuration ``TOML`` ``[files.pickle_paths]`` sub-dictionary. The
            expected structure is:

            .. code-block:: toml

                [files.pickle_paths]
                reference = "reference.pkl"

                # Scenario 1: pre-computed solution (skips optimization)
                [files.pickle_paths.scenarios.000001]
                solution = "solution-000001.pkl"

                # Scenario 2: alternatives with custom names (optimization
                # still runs, the pickled Accelerators will be appended)
                [files.pickle_paths.scenarios.000002.alternatives]
                "Conservative approach" = "design-conservative.pkl"
                "Aggressive tuning" = "design-aggressive.pkl"

                # Scenario 3: solution + alternatives
                [files.pickle_paths.scenarios.000003]
                solution = "solution-000003.pkl"

                [files.pickle_paths.scenarios.000003.alternatives]
                "Tweaked design" = "tweaked.pkl"
                "Experimental config" = "experimental.pkl"

        Returns
        -------
            Parsed configuration with structure:

            .. code-block:: python

                {
                    "Reference": "reference.pkl",
                    "scenarios": {
                        # Scenario 1: pre-computed solution (skips
                        # optimization)
                        1: {"Solution": "solution-000001.pkl"},
                        # Scenario 2: alternatives with custom names
                        # (optimization still runs, the pickled Accelerators
                        # will be appended)
                        2: {
                            "Solution": None,
                            "Conservative approach": "design-conservative.pkl",
                            "Aggressive tuning": "design-aggressive.pkl",
                        },
                        # Scenario 3: solution + alternatives
                        3: {
                            "Solution": "solution-000003.pkl",
                            "Tweaked design": "tweaked.pkl",
                            "Experimental config": "experimental.pkl",
                        }
                    }
                }

            - ``Reference``: Path to reference accelerator pickle, or None.
            - ``scenarios``: Dictionary where keys are :class:`.FaultScenario`
              indexes.
            - ``scenarios[index]``: Sub-dictionary where keys are
              :attr:`.Accelerator.name`, values are corresponding ``PKL``
              :class:`.Accelerator` pickle files. The key ``"Solution"`` will
              always be present.

        """
        parsed = {
            "Reference": pickle_config.get("Reference"),
            "scenarios": {},
        }

        scenarios_config = pickle_config.get("scenarios", {})

        for scenario_key, scenario_data in scenarios_config.items():
            try:
                index = int(scenario_key)
            except (ValueError, TypeError):
                logging.error(
                    f"Invalid scenario '{scenario_key = }' in pickle_paths. "
                    "Expected format: '000001', '000002', etc."
                )
                continue

            alternatives_config = scenario_data.get("alternatives", {})
            scenario_paths = {
                custom_name: self._get_pickle_path(
                    custom_name, alternatives_config
                )
                for custom_name in alternatives_config
            }
            if "Solution" in scenario_paths:
                logging.warning(
                    "A 'Solution' entry was given in '[files.pickle_paths."
                    f"{scenario_key}.alternatives]' and will be ignored. The "
                    "proper way to set a pre-computed solution accelerator is "
                    "to set the 'solution' key in [files.pickle_paths."
                    f"{scenario_key}]."
                )

            scenario_paths["Solution"] = scenario_data.get("Solution")

            parsed["scenarios"][index] = scenario_paths

        return parsed

    def _get_pickle_path(self, name: str, index: int = 0) -> Path | None:
        """Get pickle path for a named accelerator in :attr:`_pickle_paths`.

        Parameters
        ----------
        name :
            Accelerator name to look up in pickle paths configuration.
        index :
            :class:`.FaultScenario` index. If not null, we look for ``name``
            key in ``self._pickle_paths[index]`` subdict.

        Returns
        -------
            Resolved absolute path if configured, None otherwise.

        """
        if name == "Reference":
            path = self._pickle_paths.get("Reference")
            if path is None:
                return
            if isinstance(path, str):
                return Path(path).resolve().absolute()
            raise TypeError(
                f"Reference Accelerator pickle {path = } could not be resolved"
                "to a string."
            )
        scenarios = self._pickle_paths.get("scenarios")
        if scenarios is None or isinstance(scenarios, str):
            return

        scenario = scenarios.get(index)
        if scenario is None:
            return

        path = scenario.get(name)
        if path is None:
            return
        return Path(path).resolve().absolute()

    def _load_from_pickle(
        self, name: str, index: int, pickle_path: Path
    ) -> Accelerator | None:
        """Load accelerator from pickle file if it exists.

        Parameters
        ----------
        name :
            Accelerator name.
        index :
            Corresponding :class:`.FaultScenario` index. A null index is
            reserved for reference accelerator.
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
            self.pickler, pickle_path, name=name, index=index
        )

    def _load_additional_pickles(
        self, reserved_names: set[str] = {"Reference", "Solution"}
    ) -> dict[int, list[Accelerator]]:
        """Unpickle additional :class:`.Accelerator`.

        Parameters
        ----------
        reserved_names :
            Names already used for Reference/Solution accelerators; associated
            paths are not unpickled.

        Returns
        -------
            Additional accelerators loaded from pickle files, associated with
            their :class:`.FaultScenario` index.

        """
        scenarios: dict[int, dict[str, str]] | str | None
        scenarios = self._pickle_paths.get("scenarios")
        if scenarios is None or isinstance(scenarios, str):
            return {}

        additional: dict[int, list[Accelerator]] = {}
        for index, names_paths in scenarios.items():
            accelerators = []
            for pickle_name, raw_path in names_paths.items():
                if pickle_name in reserved_names or raw_path is None:
                    continue

                pickle_path = Path(raw_path).resolve().absolute()
                accelerator = self._load_from_pickle(
                    pickle_name, index=index, pickle_path=pickle_path
                )
                if accelerator is None:
                    logging.debug(
                        f"Not unpickling '{pickle_name}' key in [files."
                        f"pickle_paths.scenarios.{index}.alternatives] because"
                        f" '{pickle_path}' does not exist."
                    )
                    continue

                logging.info(
                    f"Loading additional accelerator '{accelerator.id}' from "
                    "pickle."
                )
                accelerators.append(accelerator)
            additional[index] = accelerators
        return additional

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
        accelerators = [
            accelerator
            for sorted_by_fault_scenario in self.create_all_broken(
                n_objects
            ).values()
            for accelerator in sorted_by_fault_scenario
        ]
        return accelerators


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
        return [reference] + self.create_failed(n_objects)
