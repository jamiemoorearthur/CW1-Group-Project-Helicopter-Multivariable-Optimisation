from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sympy as sp

RHO_AIR, CD, G, RHO_PAPER, CLIP_MASS = 1.225, 1.0, 9.81, 0.080, 0.0005
WR, LR0, BASE_W, BASE_H = 0.12, 0.08, 0.12, 0.04
LOWER, UPPER = np.array([0.08, 0.02, 0.05]), np.array([0.15, 0.05, 0.106])  # [LR, WT, HT]
PRICE, A4_AREA, N_KKT, N_SWEEP = 5.0, 0.210 * 0.297, 300, 300
G0, GC = WR * LR0 * RHO_PAPER * G, CLIP_MASS * G
A1 = 2 * G0 / (RHO_AIR * CD * np.pi * LR0**3)
A2 = 2 * RHO_PAPER * G / (RHO_AIR * CD * np.pi)
A3 = 2 * (BASE_W * BASE_H * RHO_PAPER * G + GC) / (RHO_AIR * CD * np.pi)
LR, WT, HT = sp.symbols("LR WT HT", positive=True)
F = sp.sqrt(A1 * LR + (A2 * WT * HT + A3) / LR**2)
C = WR * LR + BASE_W * BASE_H + WT * HT
velocity = sp.lambdify((LR, WT, HT), F, "numpy")
area = sp.lambdify((LR, WT, HT), C, "numpy")
gradient = sp.lambdify((LR, WT, HT), [sp.diff(F, x) for x in (LR, WT, HT)], "numpy")

def objectives(designs):
    velocities = np.asarray(velocity(*designs.T))
    paper_areas = np.asarray(area(*designs.T))
    return velocities, paper_areas

def results_table(designs, status):
    v, c = objectives(designs)
    return pd.DataFrame({
        "LR_cm": 100 * designs[:, 0], "WR_cm": 100 * WR, "WT_cm": 100 * designs[:, 1], "HT_cm": 100 * designs[:, 2],
        "velocity_m_s": v, "cost_cm2": 1e4 * c,
        "material_cost_gbp": c / A4_AREA * PRICE / 100, "material_cost_pence": c / A4_AREA * PRICE,
        "pareto_status": status,
    })

def print_best(label, row):
    print(f"\n{label}: LR={row.LR_cm:.3f} cm, WR={row.WR_cm:.3f} cm, WT={row.WT_cm:.3f} cm, HT={row.HT_cm:.3f} cm\n"
          f"  Velocity={row.velocity_m_s:.5f} m/s, area={row.cost_cm2:.2f} cm^2, "
          f"cost=GBP {row.material_cost_gbp:.5f} ({row.material_cost_pence:.3f}p)")

def main():
    WT, HT = LOWER[1:]
    LR_star = np.clip((2 * (A2 * WT * HT + A3) / A1) ** (1 / 3), LOWER[0], UPPER[0])
    budgets = np.linspace(area(LOWER[0], WT, HT), area(LR_star, WT, HT), N_KKT)
    designs = np.column_stack(((budgets - BASE_W * BASE_H - WT * HT) / WR,
                               np.full(N_KKT, WT), np.full(N_KKT, HT)))
    v, c = objectives(designs)
    grad = np.asarray(gradient(*designs.T)).T
    lam = np.maximum(0, -grad[:, 0] / WR)
    mu_WT, mu_HT = grad[:, 1] + lam * HT, grad[:, 2] + lam * WT
    residual = np.maximum(
        np.max(np.abs(grad + lam[:, None] * [WR, HT, WT]
                      - np.c_[np.zeros(N_KKT), mu_WT, mu_HT]), axis=1),
        np.abs(lam * (c - budgets)))
    assert max(residual) < 1e-7 and min(lam.min(), mu_WT.min(), mu_HT.min()) >= 0
    front = results_table(designs, "Non-dominated (KKT)").assign(
        KKT_residual=residual, lambda_cost=lam, mu_WT_lower=mu_WT,
        mu_HT_lower=mu_HT, area_budget_cm2=1e4 * c)
    samples = np.random.default_rng(42).uniform(LOWER, UPPER, (N_SWEEP, 3))
    sv, sc = objectives(samples)
    candidates = np.column_stack((
        np.clip((sc - BASE_W * BASE_H - WT * HT) / WR, LOWER[0], LR_star),
        np.full(N_SWEEP, WT), np.full(N_SWEEP, HT)))
    cv, cc = objectives(candidates)
    dominated = ((cv <= sv + 1e-9) & (cc <= sc + 1e-9)
                 & ((cv < sv - 1e-9) | (cc < sc - 1e-9)))
    sweep = results_table(samples, np.where(dominated, "Dominated", "Check / near Pareto"))
    out = Path(__file__).resolve().parent / "helicopter_KKT_results"
    out.mkdir(exist_ok=True)
    front.to_csv(out / "pareto_KKT_designs.csv", index=False)
    pd.concat([front, sweep], ignore_index=True).to_csv(out / "all_designs_and_dominance.csv", index=False)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(sv, 1e4 * sc, s=18, alpha=0.35, color="#94a3b8", label="Feasible designs (300-point sweep)")
    ax.scatter(v, 1e4 * c, s=20, color="#1769aa", zorder=4)
    ax.plot(v, 1e4 * c, color="#1769aa", lw=2.5, label="KKT Pareto front", zorder=5)
    for i, label, offset in [(0, "Minimum cost", (10, 10)), (-1, "Minimum velocity", (12, -18))]:
        ax.annotate(label, (v[i], 1e4 * c[i]), xytext=offset, textcoords="offset points")
    ax.set(xlabel="Descent velocity (m/s)", ylabel="Paper area (cm^2)", title="KKT Pareto front")
    ax.grid(alpha=0.23)
    ax.legend()
    rate = PRICE / (A4_AREA * 1e4)
    cost_axis = ax.secondary_yaxis("right", functions=(lambda x: x * rate, lambda x: x / rate))
    cost_axis.set_ylabel("Cost (pence)")
    fig.tight_layout()
    fig.savefig(out / "pareto_KKT.png", dpi=200)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(1e4 * c, lam, color="#1769aa", lw=2)
    ax.set(xlabel="Permitted paper-area budget (cm^2)", ylabel="KKT multiplier lambda (m/s per m^2)",
           title="Cost constraint shadow price from KKT conditions")
    ax.grid(alpha=0.23)
    fig.tight_layout()
    fig.savefig(out / "KKT_multipliers.png", dpi=200)
    best_cost = front.loc[front["material_cost_gbp"].idxmin()]
    best_v = front.loc[front["velocity_m_s"].idxmin()]
    cols = {"LR_cm": "LR (cm)", "WR_cm": "WR (cm)", "WT_cm": "WT (cm)", "HT_cm": "HT (cm)",
            "velocity_m_s": "Velocity (m/s)", "cost_cm2": "Area (cm^2)",
            "lambda_cost": "Lambda", "mu_WT_lower": "Mu_WT", "mu_HT_lower": "Mu_HT", "KKT_residual": "Residual"}
    shown = front.iloc[np.linspace(0, len(front) - 1, 11, dtype=int)][list(cols)].rename(columns=cols)
    print(f"{N_KKT} KKT Pareto designs; {N_SWEEP} swept designs; max KKT residual={max(residual):.2e}")
    print(f"Sweep: {int(dominated.sum())} dominated; {int((~dominated).sum())} check / near Pareto.")
    print(f"KKT variables LR/WT/HT; fixed WR={100*WR:.0f} cm; "
          f"active lower bounds WT={100*WT:.0f}, HT={100*HT:.0f} cm.")
    print("Fixed LR: WT*HT raises cost and speed; larger tails are dominated; Mu_WT/Mu_HT are positive.")
    print_best("Lowest cost", best_cost)
    print_best("Lowest descent velocity", best_v)
    print(f"\nRepresentative KKT solutions ({len(shown)} of {len(front)}):\n"
          + shown.to_string(index=False, float_format=lambda x: f"{x:.4g}"))
    print(f"\nAll KKT solutions: {out / 'pareto_KKT_designs.csv'}\nSaved graphs and CSV files to: {out}")
    plt.show()

if __name__ == "__main__":
    main()
