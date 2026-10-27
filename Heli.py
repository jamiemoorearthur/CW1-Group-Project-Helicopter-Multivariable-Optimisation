import numpy as np
import matplotlib.pyplot as plt
from pymoo.core.problem import Problem
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.optimize import minimize
# Step 1: Set dimensions in metres. A 5 mm step means only buildable sizes are tested.
WR, WB, HB, STEP = 0.06, 0.12, 0.04, 0.005
XL = np.array([0.08, 0.02, 0.05])  # Minimum LR, WT, HT
XU = np.array([0.15, 0.05, 0.106])  # Maximum LR, WT, HT
A_COEFFS, COST_CLIP, COST_PAPER = np.array([0., 0., 1.]), 0.01, 0.19
# A_COEFFS is synthetic: replace it with coefficients fitted from measured flight tests.
# Step 2: Snap each design to the nearest grid point and calculate its material cost.
def snap(x): return np.clip(np.round(np.asarray(x) / STEP) * STEP, XL, XU)
def cost(x):
    LR, WT, HT = x
    return COST_CLIP + COST_PAPER * (WT * HT + WB * HB + WR * LR)
# Step 3: Minimize predicted speed; reject designs over budget or with a negative radicand.
class DesignProblem(Problem):
    def __init__(self, budget):
        super().__init__(n_var=3, n_obj=1, n_ieq_constr=2, xl=XL, xu=XU)
        self.budget = budget
    def _evaluate(self, X, out, *args, **kwargs):
        LR, WT, HT = snap(X).T
        rad = A_COEFFS[0] * LR**3 + A_COEFFS[1] * WT * HT + A_COEFFS[2]
        out["F"] = (np.sqrt(np.maximum(rad, 1e-12)) / LR)[:, None]
        out["G"] = np.column_stack([cost([LR, WT, HT]) - self.budget, -rad])
# Step 4: Sweep possible budgets and use a genetic algorithm to find feasible designs.
def main():
    if np.array_equal(A_COEFFS, [0., 0., 1.]):
        print("Warning: coefficients are synthetic; use measured test data for real results.")
    low, high = cost(snap(XL)), cost(snap(XU))
    results = []
    for budget in np.linspace(low + 0.01 * (high - low), high, 20):
        res = minimize(DesignProblem(budget), GA(pop_size=80), ("n_gen", 200), verbose=False)
        if res.X is None or res.CV is None or float(np.sum(res.CV)) > 0: continue
        x = snap(res.X)
        results.append((cost(x), float(np.atleast_1d(res.F)[0])))
    if not results: raise SystemExit("No feasible designs; check bounds and coefficients.")
    # Step 5: Keep the Pareto front: lower speed without spending more.
    results.sort()
    front, best = [], np.inf
    for c, v in results:
        if v < best - 1e-9: front.append((c, v)); best = v
    # Step 6: Plot the Pareto front (the best velocity found at each cost).
    plt.plot(*np.array(front).T, "-s", label="Pareto front")
    plt.xlabel("Cost (£)"); plt.ylabel("Falling velocity (m/s)")
    plt.grid(True); plt.legend(); plt.savefig("pareto_front.png", dpi=150); plt.show()
if __name__ == "__main__": main()
