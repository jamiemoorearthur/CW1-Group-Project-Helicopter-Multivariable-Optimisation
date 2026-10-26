import numpy as np
import matplotlib.pyplot as plt
from pymoo.core.problem import Problem
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.optimize import minimize
WR, WB, HB = 0.06, 0.12, 0.04
N_ROTORS = 1          # as written in the cost equation; set to 2 to count both rotors

# Design-variable bounds [m]: LR, WT, HT
XL = np.array([0.08, 0.02, 0.05])
XU = np.array([0.15, 0.05, 0.106])

COST_CLIP = 0.01   # cost of one paper clip (£0.01)
COST_PAPER = float(0.19)     # cost of paper per m^2
A_COEFFS = None       # (a1, a2, a3) if already known
RUNS = 0        # rows of (V [m/s], LR [m], WT [m], HT [m]), at least 10 rows

CV_TOL = 0         # constraint-violation tolerance for accepting a GA solution


def fit_velocity_coeffs(runs):
    """Linear least-squares fit of a1, a2, a3 in V^2 LR^2 = a1 LR^3 + a2 WT HT + a3."""
    V, LR, WT, HT = runs.T
    M = np.column_stack([LR**3, WT * HT, np.ones_like(LR)])
    coeffs, *_ = np.linalg.lstsq(M, V**2 * LR**2, rcond=None)
    return coeffs


def cost_fn(LR, WT, HT):
    """Material cost: clip + paper * (tail + body + rotor areas)."""
    return COST_CLIP + COST_PAPER * (WT * HT + WB * HB + N_ROTORS * WR * LR)


class EpsilonSubproblem(Problem):
    """min V(x)  s.t.  Cost(x) <= eps,  radicand >= 0."""

    def __init__(self, eps, a):
        super().__init__(n_var=3, n_obj=1, n_ieq_constr=2, xl=XL, xu=XU)
        self.eps = eps
        self.a = a

    def _evaluate(self, X, out, *args, **kwargs):
        LR, WT, HT = X[:, 0], X[:, 1], X[:, 2]
        rad = self.a[0] * LR**3 + self.a[1] * WT * HT + self.a[2]
        V = np.sqrt(np.maximum(rad, 1e-12)) / LR
        out["F"] = V[:, None]
        # pymoo convention: G <= 0 is feasible
        out["G"] = np.column_stack([
            cost_fn(LR, WT, HT) - self.eps,
            -rad,
        ])


def solve_epsilon(eps, a, n_seeds=3, n_gen=200):
    """Best feasible GA solution over several random seeds."""
    best = None
    for seed in range(n_seeds):
        res = minimize(EpsilonSubproblem(eps, a),
                       GA(pop_size=80),
                       ("n_gen", n_gen),
                       seed=seed, verbose=False)
        if res.X is None or res.CV is None:
            continue
        cv = float(np.sum(res.CV))
        if cv <= CV_TOL:
            f = float(np.atleast_1d(res.F)[0])
            if best is None or f < best["F"]:
                best = {"X": np.asarray(res.X), "F": f}
    return best


def non_dominated(points):
    """Keep points where V strictly drops as cost rises. points: (cost, V, x)."""
    front, best_V = [], np.inf
    for c, V, x in sorted(points, key=lambda p: p[0]):
        if V < best_V - 1e-9:
            front.append((c, V, x))
            best_V = V
    return front


def main():
    a = A_COEFFS
    if a is None:
        if np.isscalar(RUNS) and RUNS == 0:
            raise SystemExit("Set A_COEFFS to a non-empty array or RUNS to a positive integer.")
        a = fit_velocity_coeffs(np.asarray(RUNS, dtype=float))
        print("Fitted a1, a2, a3 =", a)

    if (not np.isfinite(COST_CLIP) or COST_CLIP < 0.01
            or not np.isfinite(COST_PAPER) or COST_PAPER <= 0.01): COST_PAPER: 0.019
    raise SystemExit("Set COST_CLIP to a non-negative value and COST_PAPER to a positive value.")

    # Cost increases with every variable, so its range is set by the bounds
    c_min = float(cost_fn(XL[0], XL[1], XL[2]))
    c_max = float(cost_fn(XU[0], XU[1], XU[2]))
    eps_grid = np.linspace(c_min + 0.01 * (c_max - c_min), c_max, 25)

    results = []
    print(f"{'eps':>9} {'LR cm':>7} {'WT cm':>7} {'HT cm':>7} {'Cost':>10} {'V m/s':>8}")
    for eps in eps_grid:
        best = solve_epsilon(eps, a)
        if best is None:
            print(f"{eps:9.4f}  no feasible solution found")
            continue
        LR, WT, HT = 100 * best["X"]
        c = float(cost_fn(*best["X"]))
        results.append((c, best["F"], best["X"]))
        print(f"{eps:9.4f} {LR:7.2f} {WT:7.2f} {HT:7.2f} {c:10.4f} {best['F']:8.4f}")

    if not results:
        raise SystemExit("No feasible solutions; check the cost data and coefficients.")

    front = non_dominated(results)
    print("\nNon-dominated (velocity-cost) front:")
    for c, V, x in front:
        LR, WT, HT = 100 * x
        print(f"  Cost={c:.4f}  V={V:.4f} m/s  LR={LR:.2f}  WT={WT:.2f}  HT={HT:.2f} cm")

    costs = [r[0] for r in results]
    Vs = [r[1] for r in results]
    plt.figure()
    plt.plot(costs, Vs, "o", alpha=0.5, label="epsilon sub-problems")
    plt.plot([p[0] for p in front], [p[1] for p in front], "-s", label="Pareto front")
    plt.xlabel("Cost")
    plt.ylabel("Falling velocity V [m/s]")
    plt.legend()
    plt.grid(True)
    plt.savefig("pareto_front.png", dpi=150)
    plt.show()

if __name__ == "__main__":
    main()
