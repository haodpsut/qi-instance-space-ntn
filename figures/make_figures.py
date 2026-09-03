"""Sinh MOI hinh, bang va macro cua bai tu MOT nguon duy nhat: results/e1_protocol.json.

⛔ LUAT CUA BAI NAY: khong con so nao duoc go tay vao .tex. Moi con so di qua `out/numbers.tex`.
   Ly do da ghi trong so: 49% so trong mot bai truoc la go tay, va mot con so bi chep 12 lan.

⚠ Bo sinh nay KHONG duoc dinh nghia lai bat cu dai luong nao. No chi DOC va DINH DANG. Moi phep
   tinh khoa hoc nam trong code/e1_protocol.py.
"""

import io
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt      # noqa: E402
import numpy as np                   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "results", "e1_protocol.json")
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

# Bang mau: ma hoa vai tro bang SAC DO + KY HIEU, de in den trang van doc duoc
C_MULTI, C_UNI = "#2a5580", "#d9d5cc"
C_QPSO, C_RESTART, C_CMAES, C_DE = "#aa2d2d", "#236e50", "#8a7fb5", "#c08a3e"

plt.rcParams.update({"font.size": 8, "axes.linewidth": 0.6,
                     "xtick.major.width": 0.6, "ytick.major.width": 0.6,
                     "figure.dpi": 300, "savefig.bbox": "tight", "savefig.pad_inches": 0.02})

D = json.load(io.open(SRC, encoding="utf-8"))
MM = {(c["K"], c["gmax"], c["kappa"], c["instance"]): c["multimodal"] for c in D["instance_space"]}
KS = sorted({c["K"] for c in D["instance_space"]})
GM = sorted({c["gmax"] for c in D["instance_space"]})
KA = sorted({c["kappa"] for c in D["instance_space"]})
SPIKE = (8, 0.30, 0.05)              # o ma spike 28/07 da sang


def cell_frac(K, g, k):
    """Ti le thuc the da cuc tri trong mot o."""
    v = [c["multimodal"] for c in D["instance_space"]
         if (c["K"], c["gmax"], c["kappa"]) == (K, g, k)]
    return sum(v) / float(len(v)) if v else 0.0


# ---------------------------------------------------------------- Fig 1: ban do instance space
def fig_map():
    fig, axes = plt.subplots(1, len(KA), figsize=(6.6, 2.15), sharey=True)
    for ax, k in zip(axes, KA):
        M = np.array([[cell_frac(K, g, k) for g in GM] for K in KS])
        ax.imshow(M, cmap=matplotlib.colors.LinearSegmentedColormap.from_list(
            "m", [C_UNI, C_MULTI]), vmin=0, vmax=1, aspect="auto")
        for i, K in enumerate(KS):
            for j, g in enumerate(GM):
                f = M[i, j]
                ax.text(j, i, "%d/3" % round(f * 3), ha="center", va="center",
                        fontsize=6.5, color="white" if f > 0.5 else "#333")
                if (K, g, k) == SPIKE:
                    ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, fill=False,
                                               edgecolor="#cc2200", lw=2.0))
                    ax.text(j, i - 0.40, "spike 28/07", ha="center", va="center",
                            fontsize=5.2, color="#cc2200", fontweight="bold")
        ax.set_xticks(range(len(GM)));  ax.set_xticklabels(["%.2f" % g for g in GM])
        ax.set_yticks(range(len(KS)));  ax.set_yticklabels([str(K) for K in KS])
        ax.set_xlabel(r"$g_{\max}$")
        ax.set_title(r"$\kappa$ = %.2f" % k, fontsize=8)
    axes[0].set_ylabel("beams $K$")
    fig.savefig(os.path.join(OUT, "fig1-instance-space.pdf"))
    plt.close(fig)


# ------------------------------------------- Fig 2: vi tri trong ban do du doan phan quyet
def fig_verdict():
    groups = [("unimodal", False), ("multimodal", True)]
    fig, ax = plt.subplots(figsize=(3.3, 2.0))
    labels, wins, ties, losses = [], [], [], []
    for lab, want in groups:
        w = t = l = 0
        for c in D["methods"]:
            key = (c["K"], c["gmax"], c["kappa"], c["instance"])
            if MM.get(key) != want:
                continue
            dm = c["methods"]["qpso"]["mean"] - c["methods"]["restart-lbfgs"]["mean"]
            w += dm > 1e-9; l += dm < -1e-9; t += abs(dm) <= 1e-9
        labels.append("%s\n(%d units)" % (lab, w + t + l))
        wins.append(w); ties.append(t); losses.append(l)
    y = np.arange(len(labels))
    ax.barh(y, wins, color=C_QPSO, label="QI wins", height=.55)
    ax.barh(y, ties, left=wins, color="#bfbfbf", label="tie", height=.55)
    ax.barh(y, losses, left=np.array(wins) + np.array(ties), color=C_RESTART,
            label="restart-L-BFGS wins", height=.55)
    for i, (w, t, l) in enumerate(zip(wins, ties, losses)):
        for val, off in ((w, w / 2), (t, w + t / 2), (l, w + t + l / 2)):
            if val:
                ax.text(off, i, str(val), ha="center", va="center", fontsize=7,
                        color="white" if val > 8 else "#333")
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlabel("units (configuration $\\times$ instance)")
    ax.legend(fontsize=6, loc="lower right", framealpha=.95)
    ax.invert_yaxis()
    fig.savefig(os.path.join(OUT, "fig2-verdict-by-region.pdf"))
    plt.close(fig)


# ------------------------------------------- Fig 3: hieu ung so voi nhieu seed
def fig_effect_vs_noise():
    fig, ax = plt.subplots(figsize=(3.3, 2.0))
    for lab, want, col in (("unimodal", False, C_UNI), ("multimodal", True, C_MULTI)):
        r = []
        for c in D["methods"]:
            key = (c["K"], c["gmax"], c["kappa"], c["instance"])
            if MM.get(key) != want:
                continue
            a, b = c["methods"]["qpso"], c["methods"]["restart-lbfgs"]
            sd = max(a["std"], b["std"])
            if sd > 1e-12:
                r.append(abs(a["mean"] - b["mean"]) / sd)
        if r:
            ax.hist(r, bins=np.linspace(0, 3, 19), alpha=.75, color=col,
                    edgecolor="#444", linewidth=.4, label="%s (n=%d)" % (lab, len(r)))
    ax.axvline(1.0, color="#cc2200", lw=1.2, ls="--")
    ax.text(1.06, ax.get_ylim()[1] * .88, "effect = seed spread", fontsize=6, color="#cc2200")
    ax.set_xlabel("|mean difference| / seed std.")
    ax.set_ylabel("units")
    ax.legend(fontsize=6)
    fig.savefig(os.path.join(OUT, "fig3-effect-vs-seed-noise.pdf"))
    plt.close(fig)


# ---------------------------------------------------------------- bang + macro
def tables_and_macros():
    rows, nums = [], {}
    for lab, key, want in (("unimodal", "Uni", False), ("multimodal", "Multi", True)):
        w = t = l = 0
        ratios = []
        for c in D["methods"]:
            k = (c["K"], c["gmax"], c["kappa"], c["instance"])
            if MM.get(k) != want:
                continue
            a, b = c["methods"]["qpso"], c["methods"]["restart-lbfgs"]
            dm = a["mean"] - b["mean"]
            w += dm > 1e-9; l += dm < -1e-9; t += abs(dm) <= 1e-9
            sd = max(a["std"], b["std"])
            if sd > 1e-12:
                ratios.append(abs(dm) / sd)
        n = w + t + l
        med = float(np.median(ratios)) if ratios else float("nan")
        rows.append((lab, n, w, t, l, med))
        nums["num%sUnits" % key] = n
        nums["num%sWin" % key] = w
        nums["num%sTie" % key] = t
        nums["num%sLoss" % key] = l
        nums["num%sTiePct" % key] = "%.0f" % (100.0 * t / n) if n else "0"
        nums["num%sLossPct" % key] = "%.0f" % (100.0 * l / n) if n else "0"
        nums["num%sEffectRatio" % key] = "%.2f" % med

    tex = ["\\begin{tabular}{lrrrrr}", "\\toprule",
           "region & units & QI wins & tie & loss & effect / seed spread \\\\",
           "\\midrule"]
    for lab, n, w, t, l, med in rows:
        tex.append("%s & %d & %d & %d & %d & %.2f \\\\" % (lab, n, w, t, l, med))
    tex += ["\\bottomrule", "\\end{tabular}"]
    io.open(os.path.join(OUT, "tab1-verdict.tex"), "w", encoding="utf-8").write("\n".join(tex))

    # macro toan cuc
    cells_mm = D["cells_multimodal"]
    nums.update({
        "numCells": D["cells_total"],
        "numCellsMulti": cells_mm,
        "numSeeds": D["seeds"],
        "numBudget": "{:,}".format(D["budget"]).replace(",", "."),
        "numInst": D["n_inst"],
        "numStarts": D["n_starts"],
        "numUnits": len(D["methods"]),
        "numMinSpread": "%g" % D["min_spread_pct"],
    })
    # restart-lbfgs thang bao nhieu don vi
    best = sum(1 for c in D["methods"]
               if c["methods"]["restart-lbfgs"]["mean"]
               >= max(m["mean"] for m in c["methods"].values()) - 1e-9)
    nums["numRestartBest"] = best
    nums["numQpsoWinTotal"] = sum(
        1 for c in D["methods"]
        if c["methods"]["qpso"]["mean"] > c["methods"]["restart-lbfgs"]["mean"] + 1e-9)
    # o spike
    sp = [c for c in D["instance_space"]
          if (c["K"], c["gmax"], c["kappa"]) == SPIKE]
    nums["numSpikeMulti"] = sum(1 for c in sp if c["multimodal"])
    nums["numSpikeInst"] = len(sp)
    nums["numSpikeK"], nums["numSpikeG"], nums["numSpikeKappa"] = SPIKE[0], "0,30", "0,05"

    io.open(os.path.join(OUT, "numbers.tex"), "w", encoding="utf-8").write(
        "".join("\\newcommand{\\%s}{%s}\n" % (k, v) for k, v in sorted(nums.items())))
    return nums


if __name__ == "__main__":
    fig_map()
    fig_verdict()
    fig_effect_vs_noise()
    n = tables_and_macros()
    print("  ✅ 3 hình · 1 bảng · %d macro" % len(n))
    for k in sorted(n):
        print("     %-22s %s" % (k, n[k]))
