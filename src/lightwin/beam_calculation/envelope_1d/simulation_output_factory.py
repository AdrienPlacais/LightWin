"""Define a class to easily generate the :class:`.SimulationOutput`."""

from abc import ABCMeta
from dataclasses import dataclass
from pathlib import Path
from scipy.optimize import brentq
from typing import Callable
from scipy.constants import c

import numpy as np

from lightwin.beam_calculation.envelope_1d.beam_parameters_factory import (
    BeamParametersFactoryEnvelope1D,
)
from lightwin.beam_calculation.envelope_1d.transfer_matrix_factory import (
    TransferMatrixFactoryEnvelope1D,
)
from lightwin.beam_calculation.simulation_output.factory import (
    SimulationOutputFactory,
)
from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.core.list_of_elements.list_of_elements import ListOfElements
from lightwin.core.particle import ParticleFullTrajectory
from lightwin.core.transfer_matrix.transfer_matrix import TransferMatrix
from lightwin.failures.set_of_cavity_settings import SetOfCavitySettings


@dataclass
class SimulationOutputFactoryEnvelope1D(SimulationOutputFactory):
    """A class for creating simulation outputs for :class:`.Envelope1D`."""

    out_folder: Path

    def __post_init__(self) -> None:
        """Create the factories.

        The created factories are :class:`.TransferMatrixFactory` and
        :class:`.BeamParametersFactory`. The sub-class that is used is declared
        in :meth:`._transfer_matrix_factory_class` and
        :meth:`._beam_parameters_factory_class`.

        """
        # Factories created in ABC's __post_init__
        return super().__post_init__()

    @property
    def _transfer_matrix_factory_class(self) -> ABCMeta:
        """Give the **class** of the transfer matrix factory."""
        return TransferMatrixFactoryEnvelope1D

    @property
    def _beam_parameters_factory_class(self) -> ABCMeta:
        """Give the **class** of the beam parameters factory."""
        return BeamParametersFactoryEnvelope1D

    def run(
        self,
        elts: ListOfElements,
        single_elts_results: list[dict],
        set_of_cavity_settings: SetOfCavitySettings,
    ) -> SimulationOutput:
        """Transform the outputs of BeamCalculator to a SimulationOutput.

        .. todo::
            Patch in transfer matrix to get proper input transfer matrix. In
            future, input beam will not hold transf mat in anymore.

        """
        w_kin = [
            energy
            for results in single_elts_results
            for energy in results["w_kin"]
        ]
        w_kin.insert(0, elts.w_kin_in)

        phi_abs_array = [elts.phi_abs_in]
        for elt_results in single_elts_results:
            phi_abs = [
                phi_rel + phi_abs_array[-1]
                for phi_rel in elt_results["phi_rel"]
            ]
            phi_abs_array.extend(phi_abs)
        synch_trajectory = ParticleFullTrajectory(
            w_kin=w_kin,
            phi_abs=phi_abs_array,
            synchronous=True,
            beam=self._beam_kwargs,
        )

        gamma_kin = synch_trajectory.gamma
        assert isinstance(gamma_kin, np.ndarray)

        cav_params = {
            "v_cav_mv": [
                (
                    set_of_cavity_settings[elt].v_cav_mv
                    if elt in set_of_cavity_settings
                    else None
                )
                for elt in elts
            ],
            "phi_s": [
                (
                    set_of_cavity_settings[elt].phi_s
                    if elt in set_of_cavity_settings
                    else None
                )
                for elt in elts
            ],
        }

        element_to_index = self._generate_element_to_index_func(elts)
        transfer_matrix: TransferMatrix = self.transfer_matrix_factory.run(
            elts.tm_cumul_in,
            single_elts_results,
            element_to_index,
        )

        z_abs = elts.get("abs_mesh", remove_first=True)
        beam_parameters = self.beam_parameters_factory.factory_method(
            elts.input_beam.sigma,
            z_abs,
            gamma_kin,
            transfer_matrix,
            element_to_index,
        )

        phi_s = np.array([x if x is not None else np.nan for x in cav_params['phi_s']])
        phi_acceptance = compute_phase_acceptance(phi_s)

        e_rest_mev = synch_trajectory.beam["e_rest_mev"]
        q_adim = synch_trajectory.beam["q_adim"]
        v_cav_mv = np.array([x if x is not None else np.nan for x in cav_params['v_cav_mv']])
        freq_cavity_mhz = np.array([set_of_cavity_settings[elt].freq_cavity_mhz
                           if elt in set_of_cavity_settings
                           else np.nan
                           for elt in elts
                           ])
        length_m = np.array([elt.length_m
                    for elt in elts
        ])
        beta_kin = beam_parameters.beta_kin
        assert isinstance(beta_kin, np.ndarray)
        e_acc_mvpm = v_cav_mv/length_m
        s_out = elts.get("s_out")
        s_in_0 = elts.get("s_in")[0]
        s_out_corrected = s_out - s_in_0

        gamma_kin_converted = index_to_param(s_out=s_out_corrected, param=gamma_kin,)
        beta_kin_converted = index_to_param(s_out=s_out_corrected, param=beta_kin,)

        energy_acceptance_mev = compute_energy_acceptance_mev(
            q_adim=q_adim,
            freq_cavity_mhz=freq_cavity_mhz,
            e_acc_mvpm=e_acc_mvpm,
            beta_kin=beta_kin_converted,
            gamma_kin=gamma_kin_converted,
            e_rest_mev=e_rest_mev,
            phi_s=phi_s,
        )       

        simulation_output = SimulationOutput(
            out_folder=self.out_folder,
            is_multiparticle=False,  # FIXME
            is_3d=False,
            synch_trajectory=synch_trajectory,
            cav_params=cav_params,
            beam_parameters=beam_parameters,
            element_to_index=element_to_index,
            transfer_matrix=transfer_matrix,
            set_of_cavity_settings=set_of_cavity_settings,
            phi_acceptance=phi_acceptance,
            energy_acceptance=energy_acceptance_mev,
        )
        return simulation_output

def compute_phi_1(phi_s: np.ndarray) -> np.ndarray:
    """Compute the right boundary of the phase acceptance (phi_1)

    Parameters
    ----------
    phi_s : np.ndarray
        Synchronous phase in radians

    Returns
    -------
    np.ndarray
        Right boundary of phase acceptance (phi_1) in radians
    """
    return -phi_s

def compute_phi_2(phi_2: float, phi_s: float) -> float:
    """Function whose root gives the left boundary of the phase acceptance (phi_2)

    Parameters
    ----------
    phi_2 : float
        Phase value in radians to test as boundary
    phi_s : float
        Synchronous phase in radians

    Returns
    -------
    float
        Function value to find the root of (zero crossing gives phi_2)
    """
    term1 = np.sin(phi_2) - phi_2 * np.cos(phi_s)
    term2 = np.sin(phi_s) - phi_s * np.cos(phi_s)
    return term1 + term2
    
def solve_scalar_equation_brent(
    func: Callable[[float, float], float],
    param_values: np.ndarray,
    x_bounds: tuple[float, float]
) -> np.ndarray:
    """Solve a scalar equation for multiple parameters using Brent's method

    Parameters
    ----------
    func : Callable[[float, float], float]
        Function f(x, param) whose root is to be found for each param
    param_values : np.ndarray
        Array of parameter values for which to solve the equation
    x_bounds : tuple
        Interval in which to search for the root

    Returns
    -------
    np.ndarray
        Array of roots found (NaN if no root found in interval)
    """
    solutions = []

    for param in param_values:
        f = lambda x: func(x, param)
        x_left, x_right = x_bounds

        try:
            if f(x_left) * f(x_right) > 0:
                solutions.append(np.nan)
                continue

            sol = brentq(f, x_left, x_right)
            solutions.append(sol)

        except Exception:
            solutions.append(np.nan)

    return np.array(solutions)

def compute_phase_acceptance(phi_s: np.ndarray) -> np.ndarray:
    """Compute the phase acceptance in radians

    Parameters
    ----------
    phi_s : np.ndarray
        Synchronous phase in radians

    Returns
    -------
    np.ndarray
        Phase acceptance in radians (phi_1 - phi_2)
    """
    phi_1 = compute_phi_1(phi_s)
    phi_2 = solve_scalar_equation_brent(compute_phi_2, phi_s, (-np.pi, 0))
    phi_acceptance = phi_1 - phi_2

    return np.where(np.isnan(phi_acceptance), None, phi_acceptance)

def index_to_param(s_out: np.ndarray, param: np.ndarray) -> np.ndarray:
    """
    Retrieves the parameter values corresponding to the provided element indices.

    Parameters
    ----------
    s_out : np.ndarray
        Mapping from element indices to parameter indices.
    param : np.ndarray
        Array of parameter values (e.g., z_abs) to extract from.

    Returns
    -------
    np.ndarray
        Array of parameter values corresponding to the given element indices.
    """
    return np.array([param[idx] for idx in s_out])

def compute_energy_acceptance_mev(
    q_adim: float,
    freq_cavity_mhz: np.ndarray,
    e_acc_mvpm: np.ndarray,
    beta_kin: np.ndarray,
    gamma_kin: np.ndarray,
    e_rest_mev: float,
    phi_s: np.ndarray
) -> np.ndarray:
    """
    Compute the energy acceptance of an accelerating cavity in MeV.

    Parameters
    ----------
    q_adim : float
        Particle charge in units of the elementary charge (e).
    freq_cavity_mhz : np.ndarray
        Cavity frequency in megahertz (MHz).
    e_acc_mvpm : np.ndarray
        Accelerating gradient of the cavity in megavolts per meter (MV/m).
    beta_kin : np.ndarray
        Kinetic relativistic beta (v/c) of the particle.
    gamma_kin : np.ndarray
        Kinetic relativistic gamma factor of the particle.
    e_rest_mev : float
        Rest energy of the particle in MeV.
    phi_s : np.ndarray
        Synchronous phase in radians.

    Returns
    -------
    np.ndarray
        Energy acceptance of the cavity in MeV.
    """

    factor = 2 * q_adim * e_acc_mvpm * beta_kin**3 * gamma_kin**3 * e_rest_mev * c/ (np.pi * freq_cavity_mhz* 1e6)
    trig_term = phi_s * np.cos(phi_s) - np.sin(phi_s)
    energy_acceptance = np.sqrt(factor * trig_term) 

    return np.where(np.isnan(energy_acceptance), None, energy_acceptance)