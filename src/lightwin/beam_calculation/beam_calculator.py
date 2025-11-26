"""Define a base class for beam propagation computing tools.

The base class :class:`BeamCalculator` allows to compute the propagation of
the beam in a :class:`.ListOfElements`, possibly with a specific
:class:`.SetOfCavitySettings` (optimisation process). It should return a
:class:`.SimulationOutput`.

.. todo::
    Precise that BeamParametersFactory and TransferMatrixFactory are mandatory.

"""

import datetime
import logging
import time
from abc import ABC, abstractmethod
from itertools import count
from pathlib import Path

from lightwin.beam_calculation.parameters.factory import (
    ElementBeamCalculatorParametersFactory,
)
from lightwin.beam_calculation.simulation_output.factory import (
    SimulationOutputFactory,
)
from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.accelerator.accelerator import Accelerator
from lightwin.core.elements.field_maps.cavity_settings_factory import (
    CavitySettingsFactory,
)
from lightwin.core.list_of_elements.factory import ListOfElementsFactory
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.failures.set_of_cavity_settings import SetOfCavitySettings
from lightwin.util.typing import (
    EXPORT_PHASES_T,
    REFERENCE_PHASE_POLICY_T,
    REFERENCE_PHASES,
    REFERENCE_PHASES_T,
    BeamKwargs,
)


class BeamCalculator(ABC):
    """Store a beam dynamics solver and its results."""

    _ids = count(0)

    def __init__(
        self,
        reference_phase_policy: REFERENCE_PHASE_POLICY_T,
        out_folder: Path | str,
        default_field_map_folder: Path | str,
        beam_kwargs: BeamKwargs,
        export_phase: EXPORT_PHASES_T,
        flag_cython: bool = False,
        **kwargs,
    ) -> None:
        r"""Set ``id``, some generic parameters such as results folders.

        Parameters
        ----------
        reference_phase_policy :
            How reference phase of :class:`.CavitySettings` will be
            initialized.
        out_folder :
            Name of the folder where results should be stored, for each
            :class:`.Accelerator` under study. This is the name of a folder,
            not a full path.
        default_field_map_folder :
            Where to look for field map files by default.
        flag_cython :
            If the beam calculator involves loading cython field maps.
        beam_kwargs :
            The config dictionary holding all the initial beam properties.
        export_phase :
            The type of phase you want to export for your ``FIELD_MAP``.

        """
        #: How reference phase of :class:`.CavitySettings` will be initialized.
        self.reference_phase_policy: REFERENCE_PHASE_POLICY_T = (
            reference_phase_policy
        )
        self.flag_cython = flag_cython
        self.id: str = f"{self.__class__.__name__}_{next(self._ids)}"
        self._export_phase = export_phase

        if isinstance(out_folder, str):
            out_folder = Path(out_folder)
        self.out_folder = out_folder

        if isinstance(default_field_map_folder, str):
            default_field_map_folder = Path(default_field_map_folder)
        self.default_field_map_folder = (
            default_field_map_folder.resolve().absolute()
        )
        self._beam_kwargs = beam_kwargs

        self.simulation_output_factory: SimulationOutputFactory
        self.list_of_elements_factory: ListOfElementsFactory
        self.beam_calc_parameters_factory: (
            ElementBeamCalculatorParametersFactory
        )
        self._set_up_common_factories()
        self._set_up_specific_factories()

    def _set_up_common_factories(self) -> None:
        """Create the factories declared in :meth:`__init__`.

        .. note::
            Was used to set the :class:`.ListOfElementsFactory`. But now, every
            :class:`.BeamCalculator` instantiates it differently, so it is
            created in ``_set_up_specific_factories``.

        .. todo::
            ``default_field_map_folder`` has a wrong default value. Should take
            path to the ``DAT`` file, that is not known at this point. Maybe
            handle this directly in the :class:`.InstructionsFactory` or
            whatever.

        """
        pass

    @abstractmethod
    def _set_up_specific_factories(self) -> None:
        """Set up the factories specific to the :class:`.BeamCalculator`."""

    def run(
        self,
        elts: ListOfElements,
        update_reference_phase: bool = False,
        **kwargs,
    ) -> SimulationOutput:
        """Perform a simulation with default settings.

        .. todo::
            ``update_reference_phase`` is currently unused, because it is not
            useful once the propagation has been calculated. So... should I
            keep it? Maybe it can be useful in post_optimisation_run_with_this,
            or in scripts to convert the phase between the different
            references, or when I want to save the .dat?

        Parameters
        ----------
        elts :
            List of elements in which the beam must be propagated.
        update_reference_phase :
            To change the reference phase of cavities when it is different from
            the one asked in the ``TOML``. To use after the first calculation,
            if :attr:`.BeamCalculator.reference_phase_policy` does not align
            with :attr:`.CavitySettings.reference`.
        kwargs
            Other keyword arguments passed to :meth:`run_with_this`. As for
            now, only used by :class:`.TraceWin`.

        Returns
        -------
            Holds energy, phase, transfer matrices (among others) packed into a
            single object.

        """
        simulation_output = self.run_with_this(
            None, elts, use_a_copy_for_nominal_settings=False, **kwargs
        )
        if update_reference_phase:
            if self.reference_phase == "phi_s":
                logging.warning(
                    "Did not check how elts.force_reference_phases_to handles "
                    "synch phase"
                )
            elts.force_reference_phases_to(self.reference_phase)
        return simulation_output

    @abstractmethod
    def run_with_this(
        self,
        set_of_cavity_settings: SetOfCavitySettings | None,
        elts: ListOfElements,
        use_a_copy_for_nominal_settings: bool = True,
    ) -> SimulationOutput:
        """Perform a simulation with new cavity settings.

        Calling it with ``set_of_cavity_settings = None`` shall be the same as
        calling the plain ``run`` method.

        Parameters
        ----------
        set_of_cavity_settings :
            Holds the norms and phases of the compensating cavities.
        elts :
            List of elements in which the beam should be propagated.
        use_a_copy_for_nominal_settings :
            To copy the nominal :class:`.CavitySettings` and avoid altering
            their nominal counterpart. Set it to True during optimisation, to
            False when you want to keep the current settings.

        Returns
        -------
            Holds energy, phase, transfer matrices (among others) packed into a
            single object.

        """

    @abstractmethod
    def post_optimisation_run_with_this(
        self,
        optimized_cavity_settings: SetOfCavitySettings,
        full_elts: ListOfElements,
        **kwargs,
    ) -> SimulationOutput:
        """Run a simulation a simulation after optimization is over.

        With :class:`.Envelope1D`, it just calls the classic
        :meth:`run_with_this`. But with :class:`.TraceWin`, we need to update
        the ``optimized_cavity_settings`` as running an optimisation run on a
        fraction of the linac is pretty different from running a simulation on
        the whole linac.

        """

    @abstractmethod
    def init_solver_parameters(self, accelerator: Accelerator) -> None:
        """Init some :class:`BeamCalculator` solver parameters."""

    def _generate_simulation_output(self, *args, **kwargs) -> SimulationOutput:
        """Transform the output of ``run`` to a :class:`.SimulationOutput`."""
        return self.simulation_output_factory.run(*args, **kwargs)

    @property
    def reference_phase(self) -> REFERENCE_PHASES_T:
        """Give the reference phase.

        .. todo::
            Handle ``"as_in_original_dat"``.

        """
        assert (
            self.reference_phase_policy in REFERENCE_PHASES
        ), "Different reference phase for each cavity not handled yet."
        return self.reference_phase_policy

    @property
    @abstractmethod
    def is_a_multiparticle_simulation(self) -> bool:
        """Tell if the simulation is a multiparticle simulation."""
        pass

    @property
    @abstractmethod
    def is_a_3d_simulation(self) -> bool:
        """Tell if the simulation is in 3D."""
        pass

    def compute(
        self,
        accelerator: Accelerator,
        keep_settings: bool = True,
        recompute_reference: bool = True,
        output_time: bool = True,
        ref_simulation_output: SimulationOutput | None = None,
    ) -> SimulationOutput:
        """Wrap full process to compute propagation of beam in accelerator.

        Parameters
        ----------
        accelerator :
            Accelerator under study.
        keep_settings :
            If settings/simulation output should be saved.
        recompute_reference :
            If results should be taken from a file instead of recomputing
            everything each time.
        output_time :
            To print in log the time the calculation took.
        ref_simulation_output :
            For calculation of mismatch factors. Skipped by default.

        Returns
        -------
            Object holding simulation results.

        """
        start_time = time.monotonic()

        self.init_solver_parameters(accelerator)

        simulation_output = self.run(accelerator.elts)
        simulation_output.compute_indirect_quantities(
            accelerator.elts, ref_simulation_output
        )
        if keep_settings:
            accelerator.keep(
                simulation_output,
                exported_phase=self._export_phase,
                beam_calculator_id=self.id,
            )

        end_time = time.monotonic()
        delta_t = datetime.timedelta(seconds=end_time - start_time)
        if output_time:
            logging.info(f"Elapsed time in beam calculation: {delta_t}")

        if not recompute_reference:
            raise NotImplementedError(
                "idea is to take results from file if simulations are too "
                "long. will be easy for tracewin."
            )
        return simulation_output

    @property
    def cavity_settings_factory(self) -> CavitySettingsFactory:
        """Return the factory with a concise call."""
        _list_elts_factory = self.list_of_elements_factory
        _instruc_factory = _list_elts_factory.instructions_factory
        _element_factory = _instruc_factory.element_factory
        _field_map_factory = _element_factory.field_map_factory
        cavity_settings_factory = _field_map_factory.cavity_settings_factory
        return cavity_settings_factory
