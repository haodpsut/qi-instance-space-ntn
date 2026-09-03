"""Does the quantum-inspired metaheuristic actually win where there is something to search?

The 28/07 spike compared QPSO against CMA-ES and DE on a UNIMODAL instance and reported
"QI competitive/wins" from 6.1237 vs 6.1237. On a unimodal landscape every method finds the single
optimum, so that comparison could only ever return a tie, and reading a tie as a win is the same
proxy-scoring mistake the CGA spike made on the same day.

spike_multimodal_sweep.py showed 24 of 48 configurations ARE multimodal, with up to 27% sum-rate
between the best and worst local optimum. So the decisive question can finally be asked properly:

    on the configurations where local search demonstrably gets stuck, does QPSO beat CMA-ES?

BASELINE CHOICE IS THE WHOLE TEST. The Gap Card names CMA-ES as the real threat, and the memory rule
learned from the QML branch is that a claim must be matched by a baseline that could actually beat
it. So this includes RANDOM-RESTART L-BFGS-B at the same budget -- the honest version of "what SCA
does if you simply restart it" -- because that is the baseline a reviewer reaches for first, and the
one that has historically killed metaheuristic papers. All four methods get the SAME number of
objective evaluations.

Unit of analysis is the (configuration, instance) pair. Seeds are repetitions WITHIN a unit, not
independent units, so they are averaged before any comparison across units.
"""
import csv
import os
import sys

import numpy as np
from cmaes import CMA
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__))
SIGMA2 = 1.0
BUDGET = 20000
SEEDS = 5
N_INST = 3
# multimodal cells taken from spike_multimodal_sweep.py, spanning weak to strong spread
CONFIGS = [(8, 0.90, 0.50), (16, 0.60, 0.50), (32, 0.60, 0.00), (32, 0.90, 0.50)]


def make_instance(seed, K, gmax):
    rng = np.random.default_rng(seed)
    G = rng.uniform(0.0, gmax, size=(K, K))
    np.fill_diagonal(G, rng.uniform(1.0, 2.0, size=K))
    return G


class Objective:
    """Wraps the sum-rate and COUNTS evaluations, so the budget is enforced, not assumed."""

    def __init__(self, G, P_tot, kappa):
        self.G, self.P_tot, self.kappa = G, P_tot, kappa
        self.n = 0
        self.dg = np.diag(G)

    def __call__(self, p):
        self.n += 1
        if not np.all(np.isfinite(p)):
            return -np.inf
        p = np.clip(p, 0.0, self.P_tot)
        s = p.sum()
        if s > self.P_tot:
            p = p * (self.P_tot / s)
        with np.errstate(all="ignore"):
            interf = self.G @ p - self.dg * p
            distort = self.kappa * (self.G @ (p ** 3))
            sinr = (self.dg * p) / (SIGMA2 + interf + distort)
            v = float(np.sum(np.log2(1.0 + sinr)))
        return v if np.isfinite(v) else -np.inf


def qpso(f, K, P_tot, seed, M=30):
    rng = np.random.default_rng(seed)
    X = rng.uniform(0, P_tot / K * 2, size=(M, K))
    pbest = X.copy()
    pbest_f = np.array([f(x) for x in X])
    gi = int(np.argmax(pbest_f))
    gbest, gbest_f = pbest[gi].copy(), pbest_f[gi]
    while f.n < BUDGET:
        beta = 1.0 - 0.5 * f.n / BUDGET
        mbest = pbest.mean(axis=0)
        for i in range(M):
            phi = rng.random(K)
            att = phi * pbest[i] + (1 - phi) * gbest
            u = np.clip(rng.random(K), 1e-12, 1)
            sign = np.where(rng.random(K) < 0.5, 1.0, -1.0)
            X[i] = np.clip(att + sign * beta * np.abs(mbest - X[i]) * np.log(1.0 / u), 0, P_tot)
            v = f(X[i])
            if v > pbest_f[i]:
                pbest_f[i], pbest[i] = v, X[i].copy()
                if v > gbest_f:
                    gbest_f, gbest = v, X[i].copy()
            if f.n >= BUDGET:
                break
    return gbest_f


def cmaes_opt(f, K, P_tot, seed):
    opt = CMA(mean=np.full(K, P_tot / K), sigma=P_tot / K * 0.5, seed=seed,
              bounds=np.array([[0, P_tot]] * K))
    best = -np.inf
    while f.n < BUDGET:
        sols = []
        for _ in range(opt.population_size):
            x = opt.ask()
            v = f(x)
            sols.append((x, -v))
            best = max(best, v)
            if f.n >= BUDGET:
                break
        if len(sols) == opt.population_size:
            opt.tell(sols)
    return best


def de_opt(f, K, P_tot, seed, NP=None):
    rng = np.random.default_rng(seed)
    NP = NP or max(15, 4 * K)
    X = rng.uniform(0, P_tot, size=(NP, K))
    fit = np.array([f(x) for x in X])
    while f.n < BUDGET:
        for i in range(NP):
            r = rng.choice([j for j in range(NP) if j != i], 3, replace=False)
            mut = np.clip(X[r[0]] + 0.8 * (X[r[1]] - X[r[2]]), 0, P_tot)
            cross = rng.random(K) < 0.9
            cross[rng.integers(K)] = True
            trial = np.where(cross, mut, X[i])
            v = f(trial)
            if v > fit[i]:
                fit[i], X[i] = v, trial
            if f.n >= BUDGET:
                break
    return float(fit.max())


def restart_lbfgs(f, K, P_tot, seed):
    """Random-restart local search at the same budget: the baseline reviewers reach for first."""
    rng = np.random.default_rng(seed)
    best = -np.inf
    while f.n < BUDGET:
        x0 = rng.uniform(0, P_tot / K * 2, size=K)
        r = minimize(lambda p: -f(p), x0, method="L-BFGS-B", bounds=[(0, P_tot)] * K,
                     options={"maxiter": 2000, "ftol": 1e-14, "gtol": 1e-12})
        best = max(best, -float(r.fun))
    return best


METHODS = (("qpso", qpso), ("cmaes", cmaes_opt), ("de", de_opt), ("restart-lbfgs", restart_lbfgs))


def main():
    print(f"NGAN SACH KHOP: {BUDGET} lan goi ham cho MOI phuong phap (dem trong ham, khong uoc luong)")
    print(f"{SEEDS} seed moi o; don vi phan tich = (cau hinh, thuc the), seed la LAP LAI trong don vi\n")
    print(f"{'cau hinh':>22s}  " + "  ".join(f"{n:>13s}" for n, _ in METHODS))
    rows, per_unit = [], []
    for (K, gmax, kappa) in CONFIGS:
        P_tot = float(K)
        for inst in range(N_INST):
            G = make_instance(100 + inst, K, gmax)
            means = {}
            for name, fn in METHODS:
                vals = []
                for s in range(SEEDS):
                    f = Objective(G, P_tot, kappa)
                    vals.append(fn(f, K, P_tot, 1000 + s))
                    rows.append({"K": K, "gmax": gmax, "kappa": kappa, "instance": inst,
                                 "seed": s, "method": name, "sum_rate": round(vals[-1], 6),
                                 "unit_of_analysis": "cau-hinh-x-thuc-the"})
                means[name] = float(np.mean(vals))
            per_unit.append(((K, gmax, kappa, inst), means))
            label = f"K{K} g{gmax} k{kappa} #{inst}"
            best = max(means.values())
            cells = [f"{means[n]:.4f}{'*' if means[n] >= best - 1e-9 else ' '}" for n, _ in METHODS]
            print(f"{label:>22s}  " + "  ".join(f"{c:>13s}" for c in cells))

    print(f"\n{'':>22s}  " + "  ".join(f"{n:>13s}" for n, _ in METHODS))
    wins = {n: 0 for n, _ in METHODS}
    for _, means in per_unit:
        b = max(means.values())
        for n, _ in METHODS:
            wins[n] += means[n] >= b - 1e-9
    print(f"{'so don vi tot nhat':>22s}  "
          + "  ".join(f"{str(wins[n]) + '/' + str(len(per_unit)):>13s}" for n, _ in METHODS))

    # paired: QPSO vs each rival, clustered by unit (seeds already averaged inside the unit)
    print()
    for rival in ("cmaes", "de", "restart-lbfgs"):
        d = [m["qpso"] - m[rival] for _, m in per_unit]
        w = sum(1 for x in d if x > 1e-9)
        l = sum(1 for x in d if x < -1e-9)
        print(f"  QPSO vs {rival:14s}: thang {w} / hoa {len(d)-w-l} / thua {l} don vi;"
              f" chenh trung binh {np.mean(d):+.4f} ({100*np.mean(d)/np.mean([m[rival] for _, m in per_unit]):+.2f}%)")

    out = os.path.join(HERE, "..", "raw", "qi-on-multimodal.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\n# da ghi raw/qi-on-multimodal.csv ({len(rows)} dong)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
