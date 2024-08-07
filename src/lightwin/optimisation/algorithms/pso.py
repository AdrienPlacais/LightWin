"""Legacy."""

import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pymoo.algorithms.moo.ctaea import CTAEA
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.core.callback import Callback
from pymoo.core.problem import ElementwiseProblem
from pymoo.decomposition.asf import ASF
from pymoo.factory import get_reference_directions, get_termination
from pymoo.indicators.hv import Hypervolume
from pymoo.mcdm.pseudo_weights import PseudoWeights
from pymoo.optimize import minimize
from pymoo.visualization.pcp import PCP

from lightwin.visualization import anim, plot

# from pymoo.util.running_metric import RunningMetricAnimation


STR_ALGORITHM = "NSGA-III"
# Messages from algorithm
FLAG_VERBOSE = True
# Needed by most debug tools
SAVE_HISTORY = True
# Convergence criterion. Needs a reference point.
FLAG_HYPERVOLUME = False
# Show evolution of objective evaluations with number of generations
FLAG_RUNNING = True
FLAG_CONVERGENCE_CALLBACK = False
# Show evolution of Constraint Violation with number of generations
FLAG_CV = True
# Show the cavity parameters that were tried, discriminating feasible solutions
# from unfeasible
FLAG_DESIGN_SPACE = False


class MyCallback(Callback):
    """Class to receive notification from algo at each iteration."""

    def __init__(self) -> None:
        super().__init__()
        self.n_evals = []
        self.opt = []

    def notify(self, algorithm):
        """Notify."""
        self.n_evals.append(algorithm.evaluator.n_eval)
        self.opt.append(algorithm.opt[0].F)


class MyProblem(ElementwiseProblem):
    """Class holding PSO."""

    def __init__(self, wrapper_fun, wrapper_args, **kwargs):
        self.wrapper_pso = wrapper_fun
        self.fault = wrapper_args[0]
        self.fun_residual = wrapper_args[1]

        info = self.fault.info
        n_var = info["X_0"].shape[0]
        _xl = info["X_lim"][:, 0]
        _xu = info["X_lim"][:, 1]
        n_obj = len(self.fault.wtf["objective"])
        # n_constr = 2 * info['G'].shape[0]
        logging.warning("k_e constraint manually added.")
        n_constr = 2 * info["G"].shape[0] + 1
        self.phi_s_limits = info["G"]

        logging.info(f"Number of objectives: {n_obj}")
        super().__init__(
            n_var=n_var,
            n_obj=n_obj,
            n_constr=n_constr,
            xl=_xl,
            xu=_xu,
            **kwargs,
        )
        if n_constr > 0:
            logging.info(f"{n_constr} constraints on phi_s:\n{info['G']}")

    def _evaluate(self, x, out, *args, **kwargs):
        """
        Compute residues and constraints.

        Parameters
        ----------
        x : np.array
            Holds phases (first half) and norms (second half) of cavities.
        out : dict
            Holds function values in "F" key and constraints in "G".
        """
        out["F"], results = self.wrapper_pso(x, self.fault, self.fun_residual)

        out_g = []
        for i in range(len(results["phi_s"])):
            out_g.append(self.phi_s_limits[i][0] - results["phi_s"][i])
            out_g.append(results["phi_s"][i] - self.phi_s_limits[i][1])

        # Add a constraint on the k_e.
        # We want the norms to globally increase
        n_cav = int(x.shape[0] / 2)
        n_faults = 1
        sum_of_nominal_k_e = (n_cav + n_faults) * 0.775356  # FIXME
        sum_of_this_iteration_k_e = np.sum(x[n_cav:])
        out_g.append(sum_of_nominal_k_e - sum_of_this_iteration_k_e)

        out["G"] = np.array(out_g)


def perform_pso(problem):
    """Perform the PSO."""
    if STR_ALGORITHM == "NSGA-II":
        algorithm = NSGA2(pop_size=200, eliminate_duplicates=True)

    elif STR_ALGORITHM == "NSGA-III":
        # ref_dirs = get_reference_directions("das-dennis", problem.n_obj,
        #                                     n_partitions=6)
        ref_dirs = get_reference_directions("energy", problem.n_obj, 90)
        algorithm = NSGA3(
            pop_size=200,  # 500
            ref_dirs=ref_dirs,
        )

    elif STR_ALGORITHM == "try":
        # ref_dirs = get_reference_directions("energy", problem.n_obj, 12)
        ref_dirs = get_reference_directions(
            "das-dennis", problem.n_obj, n_partitions=12
        )
        algorithm = CTAEA(ref_dirs=ref_dirs)

    termination = _set_termination()
    res = minimize(
        problem,
        algorithm,
        termination,
        seed=1,
        save_history=SAVE_HISTORY,
        verbose=FLAG_VERBOSE,
        callback=MyCallback(),
    )
    return res


def _set_termination():
    """Set a termination condition."""
    d_termination = {
        "NSGA-II": get_termination("n_gen", 100),
        "NSGA-III": get_termination("n_gen", 200),  # 200
        "try": get_termination("n_gen", 200),
    }
    termination = d_termination[STR_ALGORITHM]

    # termination = MultiObjectiveSpaceToleranceTermination(
    #     # What is the tolerance in the objective space on average. If the value
    #     # is below this bound, we terminate.
    #     tol=1e-5,
    #     # To make the criterion more robust, we consider the last n generations
    #     # and take the maximum. This considers the worst case in a window.
    #     n_last=10,
    #     # As a fallback, the generation number can be used. For some problems,
    #     # the termination criterion might not be reached; however, an upper
    #     # bound for generations can be defined to stop in that case.
    #     n_max_gen=1000,
    #     # Defines whenever the termination criterion is calculated by default,
    #     # every 10th generation.
    #     nth_gen=10,
    # )
    return termination


def mcdm(res, weights, fault_info, compare=None):
    """Perform Multi-Criteria Decision Making."""
    d_approx = {"ideal": res.F.min(axis=0), "nadir": res.F.max(axis=0)}
    logging.info(f"Nadir and ideal: {d_approx}")

    n_f = (res.F - d_approx["ideal"]) / (d_approx["nadir"] - d_approx["ideal"])
    pd_best_sol, d_asf, d_pw = _best_solutions(
        res, n_f, weights, fault_info, compare=compare
    )
    fault_info["resume"] = pd_best_sol
    d_opti = {"asf": d_asf, "pw": d_pw}

    return d_opti, d_approx


def _best_solutions(res, n_f, weights, fault_info, compare=None):
    """Look for best solutions according to various criteria."""
    # Create a pandas dataframe for the final objective values
    n_var = res.X.shape[1]
    columns = (
        ["Criteria", "i"]
        + fault_info["l_X_str"][:n_var]
        + fault_info["l_F_str"]
    )
    pd_best_sol = pd.DataFrame(columns=(columns))

    # Best solution according to ASF
    min_asf = ASF().do(n_f, 1.0 / weights)
    l_idx = [min_asf.argmin()]
    # Best solution according to Pseudo-Weights
    l_idx.append(PseudoWeights(weights).do(n_f))

    d_opti = {"ASF": None, "PW": None}
    for i, (name, idx) in enumerate(zip(d_opti.keys(), l_idx)):
        # Dict is used to study convergence, design space exploration, etc
        d_opti[name] = {
            "idx": idx,
            "X": res.X[idx].tolist(),
            "F": res.F[idx].tolist(),
        }
        # Pandas datafram is used only for user output
        pd_best_sol.loc[i] = (
            [name, idx] + res.X[idx].tolist() + res.F[idx].tolist()
        )

    for col in pd_best_sol:
        if "phi" in col:
            pd_best_sol[col] = np.rad2deg(pd_best_sol[col])
    logging.info(f"{pd_best_sol[['Criteria', 'i'] + fault_info['l_F_str']]}")

    # Viualize solutions
    _plot_solutions(res.F, d_opti, fault_info["l_F_str"], compare)

    return pd_best_sol, d_opti["ASF"], d_opti["PW"]


def convergence_callback(callback, l_f_str):
    """Plot convergence info using the results of the callback."""
    _, axx = plot.create_fig_if_not_exist(58, [111])
    axx[0].set_title("Convergence")
    axx[0].plot(callback.n_evals, callback.opt, label=l_f_str)
    axx[0].set_xlabel("Number of evaluations")
    axx[0].set_ylabel("res.F[0, :]")
    axx[0].set_yscale("log")
    axx[0].legend()
    axx[0].grid(True)


def convergence_history(hist, d_approx, str_obj, lsq_f):
    """Study the convergence of the algorithm."""
    # Convergence study
    n_evals = []  # Num of func evaluations
    hist_f = []  # Objective space values in each generation
    hist_cv = []  # Constraint violation in each generation
    hist_cv_avg = []  # Average contraint violation in the whole population

    for algo in hist:
        n_evals.append(algo.evaluator.n_eval)
        opt = algo.opt
        hist_cv.append(opt.get("CV").min())
        hist_cv_avg.append(algo.pop.get("CV").mean())

        # Filter out only the feasible and append and objective space values
        feas = np.where(opt.get("feasible"))[0]
        hist_f.append(opt.get("F")[feas])

    k = np.where(np.array(hist_cv) <= 0.0)[0].min()
    logging.info(
        f"At least one feasible solution in Generation {k} after "
        + f"{n_evals[k]} evaluations."
    )
    vals = hist_cv_avg
    # Can be replaced by hist_cv to analyse the least feasible optimal solution
    # instead of the population

    k = np.where(np.array(vals) <= 0.0)[0].min()
    logging.info(
        f"Whole population feasible in Generation {k} after "
        + f"{n_evals[k]} evaluations."
    )

    if FLAG_CV:
        fig, axx = plot.create_fig_if_not_exist(61, [211, 212])

        axx[0].plot(
            n_evals,
            hist_cv_avg,
            marker="o",
            c="k",
            lw=0.7,
            label="Avg. CV of pop.",
        )
        axx[0].axvline(n_evals[k], ls="--", label="All feasible", c="r")
        axx[0].set_title("Convergence")

        axx[1].plot(
            n_evals,
            hist_cv,
            marker="o",
            c="b",
            lw=0.7,
            label="Least feasible opt. sol.",
        )
        for i in range(2):
            axx[i].set_xlabel("Function evaluations")
            axx[i].set_ylabel("Constraint Violation")
            axx[i].legend()
            axx[i].grid(True)
        fig.show()

    if FLAG_HYPERVOLUME:
        _convergence_hypervolume(n_evals, hist_f, d_approx, str_obj, lsq_f)

    if FLAG_RUNNING:
        _convergence_running_metrics(hist)


def convergence_design_space(hist, d_opti, lsq_x=None):
    """Represent the variables that were tried during optimisation."""
    # hist_xf = []      # Explored variables (Feasible)
    # hist_xu = []      # Explored variables (Unfeasible)

    # for algo in hist:
    # pop = algo.pop
    # feas = np.where(pop.get("feasible"))[0]
    # hist_xf.append(pop.get("X")[feas])
    # unfeas = np.where(~pop.get("feasible"))[0]
    # hist_xu.append(pop.get("X")[unfeas])

    n_cav = int(np.shape(hist[0].pop.get("X"))[1] / 2)
    # FIXME
    assert n_cav == 6, "Not designed for number of cavities different from 6."
    fig, _ = plot.create_fig_if_not_exist(
        63, range(231, 237), **{"figsize": (15, 10)}
    )

    # Plot solutions (fixed points)
    _plot_variables_final_sol(fig, d_opti, n_cav, lsq_x)
    # Plot evolution of variables that were tried (animation)
    anim.AnimatedScatterDesign(fig, hist, n_cav)


def _convergence_hypervolume(n_eval, hist_f, d_approx, str_obj, lsq_f=None):
    """Study convergence using hypervolume. Not adapted when too many dims."""
    # Dictionary for reference points
    # They must be typical large values for the objective
    d_ref = {
        "w_kin": 70.0,
        "phi_abs_array": 0.5,
        "mismatch_factor": 1.0,
        "M_11": None,
        "M_12": None,
        "M_21": None,
        "M_22": None,
        "eps_zdelta": None,
        "twiss_alpha_zdelta": None,
        "twiss_beta_zdelta": None,
        "twiss_gamma_zdelta": None,
    }
    ref_point = [d_ref[obj] for obj in str_obj]
    metric = Hypervolume(
        ref_point=ref_point,
        ideal=d_approx["ideal"],
        nadir=d_approx["nadir"],
    )

    h_v = [metric.do(_F) for _F in hist_f]

    _, axx = plot.create_fig_if_not_exist(60, [111])
    axx = axx[0]

    axx.plot(n_eval, h_v, lw=0.7, marker="o", c="k")

    # FIXME
    lsq_f = None
    if lsq_f is not None:
        axx.axhline(
            metric.do(lsq_f), -n_eval, 1.1 * n_eval, label="Least-squares"
        )
        axx.legend()
    axx.set_title("Objective space")
    axx.set_xlabel("Function evaluations")
    axx.set_ylabel("Hypervolume")
    axx.grid(True)


def _convergence_running_metrics(hist):
    """Study convergence using running metrics."""
    raise IOError("func not available anymore")
    # running = RunningMetricAnimation(
    #     delta_gen=10,
    #     n_plots=10,
    #     # only_if_n_plots=True,
    #     key_press=True,
    #     do_show=True,)
    # for algorithm in hist:
    #     running.update(algorithm)


def _plot_solutions(res_f, d_opti, labels, compare=None):
    """Represent the value of the objective functions."""
    d_colors = {"ASF": "green", "PW": "blue"}
    assert d_colors.keys() == d_opti.keys(), (
        "You need to set a color per " + "solution and vice-versa."
    )

    # Specific case of 3 objectives: we make a 3d plot
    if res_f.shape[1] == 3:
        fig = plt.figure(2)
        axx = fig.add_subplot(projection="3d")
        kwargs = {"marker": "^", "alpha": 1, "s": 30}

        # Sometimes it is easier to take the log of the obj functions to
        # compare different solutions
        flag_log = False
        tmp = res_f
        if flag_log:
            tmp = np.log(tmp)
            if compare is not None:
                compare = np.log(compare)

        # Plot all solutions
        axx.scatter(tmp[:, 0], tmp[:, 1], tmp[:, 2])
        # Plot best solutions according to MCDM
        for key, val in d_opti.items():
            idx = val["idx"]
            axx.scatter(
                tmp[idx, 0],
                tmp[idx, 1],
                tmp[idx, 2],
                color=d_colors[key],
                label=key,
                **kwargs,
            )
        # If provided, plot least-squares solution
        if compare is not None:
            axx.scatter(
                compare[0],
                compare[1],
                compare[2],
                color="k",
                label="Least-squares",
                **kwargs,
            )
        axx.set_xlabel(labels[0])
        axx.set_ylabel(labels[1])
        axx.set_zlabel(labels[2])
        axx.legend()
        fig.show()
        return

    # General case: Parallel Coordinate Plot
    kwargs = {"close_on_destroy": False}
    fig = PCP(
        title=("Run", {"pad": 30}),
        n_ticks=10,
        legend=(True, {"loc": "upper left"}),
        labels=labels,
        **kwargs,
    )
    fig.set_axis_style(color="grey", alpha=0.5)
    fig.add(res_f, color="grey", alpha=0.3)
    for key, val in d_opti.items():
        fig.add(val["F"], linewidth=5, color=d_colors[key], label=key)
    if compare is not None:
        fig.add(compare, linewidth=5, color="k", label="Least-squares")
    fig.show()
    fig.ax.grid(True)


def _plot_variables_final_sol(fig, d_opti, n_cav, lsq_x=None):
    """Plot for each cavity the norm and phase that were tried."""
    axx = fig.get_axes()
    sol_color = ["g", "b"]

    # First we plot the solutions
    for i in range(n_cav):
        # Plot solution(s) X found in mcdm:
        for k, key in enumerate(d_opti.keys()):
            axx[i].scatter(
                d_opti[key]["X"][i],
                d_opti[key]["X"][i + n_cav],
                marker="^",
                c=sol_color[k],
                alpha=1,
                label=key,
            )
        # Plot solution found by LSQ
        if lsq_x is not None:
            axx[i].scatter(
                np.mod(lsq_x[i], 2.0 * np.pi),
                lsq_x[i + n_cav],
                marker="^",
                c="k",
                alpha=1,
                label="LSQ",
            )
        axx[i].grid(True)
        axx[i].set_xlim([0.0, 2.0 * np.pi])
        axx[i].set_ylim([0.387678, 0.9304272])
    axx[0].set_ylabel(r"$k_e$")
    axx[0].legend()
    axx[3].set_ylabel(r"$k_e$")
    axx[4].set_xlabel(r"$\phi_0$")
    logging.warning("Limits manually entered.")


def set_weights(l_obj_str):
    """Set array of weights for the different objectives."""
    d_weights = {
        "w_kin": 1.0,
        "phi_abs_array": 1.0,
        "eps_zdelta": 1.0,
        "twiss_alpha_zdelta": 1.0,
        "twiss_beta_zdelta": 1.0,
        "twiss_gamma_zdelta": 1.0,
        "M_11": 1.0,
        "M_12": 1.0,
        "M_21": 1.0,
        "M_22": 1.0,
        "mismatch_factor": 1,
    }
    weights = [d_weights[obj] for obj in l_obj_str]
    return np.array(weights)
