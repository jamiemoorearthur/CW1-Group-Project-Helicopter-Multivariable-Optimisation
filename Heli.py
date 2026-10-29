import numpy as np
import matplotlib.pyplot as plt
from pymoo.core.problem import Problem
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.optimize import minimize
# Step 1: Set LR, WT, and HT bounds and steps in metres.
WR, WB, HB = 0.06, 0.12, 0.04
STEP = np.array([0.001, 0.005, 0.005])  # LR, WT, HT
XL = np.array([0.08, 0.02, 0.05])  # Minimum LR, WT, HT
XU = np.array([0.15, 0.05, 0.106])  # Maximum LR, WT, HT
A_COEFFS, COST_CLIP, COST_PAPER = np.array([0., 0., 1.]), 0.01, 0.19
AIR_DENSITY, PAPER_AREAL_DENSITY = 1.225, 0.08
CLIP_MASS, GRAVITY = 0.05, 9.81
# A_COEFFS is synthetic: replace it with coefficients fitted from measured flight tests.
# Step 2: Snap each design to the nearest grid point or an exact bound.
def snap(x):
    x = np.asarray(x)
    grid_value = np.clip(np.round(x / STEP) * STEP, XL, XU)
    return np.where(np.abs(x - XU) < np.abs(x - grid_value), XU, grid_value)

def cost(x):
    LR, WT, HT = x
    return COST_CLIP + COST_PAPER * (WT * HT + WB * HB + WR * LR)
def drag_coefficient(x, velocity):
    LR, WT, HT = x
    paper_area = 2 * WR * LR + WB * HB + WT * HT
    weight = (PAPER_AREAL_DENSITY * paper_area + CLIP_MASS) * GRAVITY
    reference_area = 2 * WR * LR
    return weight / (0.5 * AIR_DENSITY * velocity**2 * reference_area)
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
    seen_designs = set()
    for iteration, budget in enumerate(np.linspace(low + 0.01 * (high - low), high, 20), start=1):
        res = minimize(DesignProblem(budget), GA(pop_size=80), ("n_gen", 200), verbose=False)
        if res.X is None or res.CV is None or float(np.sum(res.CV)) > 0: continue
        x = snap(res.X)
        design = tuple(float(value) for value in x)
        if design in seen_designs:
            print(f"Stopping at iteration {iteration}: repeated design {design}.")
            break
        seen_designs.add(design)
        velocity = float(np.atleast_1d(res.F)[0])
        cd = drag_coefficient(x, velocity)
        results.append((iteration, cost(x), velocity, cd, design))
    if not results: raise SystemExit("No feasible designs; check bounds and coefficients.")
    print("\nDrag coefficient by iteration:")
    print("Iteration | LR (m) | WT (m) | HT (m) | Velocity (m/s) | Cd")
    for iteration, _, velocity, cd, (lr, wt, ht) in results:
        print(f"{iteration:9d} | {lr:6.3f} | {wt:6.3f} | {ht:6.3f} | {velocity:14.6f} | {cd:.6f}")
    cd_values = [result[3] for result in results]
    print(f"\nMinimum Cd: {min(cd_values):.6f}")
    print(f"Maximum Cd: {max(cd_values):.6f}")
    # Step 5: Keep the Pareto front: lower speed without spending more.
    results.sort(key=lambda result: (result[1], result[2]))
    front, best = [], np.inf
    for _, c, v, _, _ in results:
        if v < best - 1e-9: front.append((c, v)); best = v
    # Step 6: Plot the Pareto front (the best velocity found at each cost).
    plt.plot(*np.array(front).T, "-s", label="Pareto front")
    plt.xlabel("Cost (£)"); plt.ylabel("Falling velocity (m/s)")
    plt.grid(True); plt.legend(); plt.savefig("pareto_front.png", dpi=150); plt.show()
if __name__ == "__main__": main()
