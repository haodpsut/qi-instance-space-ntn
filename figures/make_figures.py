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
A2P = os.path.join(HERE, "..", "results", "a2_underpowered.json")
A2 = json.load(io.open(A2P, encoding="utf-8")) if os.path.exists(A2P) else None
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


# ---------------------------------------- Fig 4: mot nghien cuu co thong thuong ket luan gi
def fig_underpowered():
    """⭐ Hinh trung tam cua bai: cung mot bai toan, ket luan doi theo VI TRI SANG va theo
    BASELINE duoc chon. Ca hai truc deu la lua chon cua nguoi lam thi nghiem, khong phai tinh
    chat cua the gioi."""
    if not A2:
        return
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.6, 2.25))

    # trai: theo doi thu
    rivals = ["de", "cmaes", "restart-lbfgs"]
    lbl = {"de": "vs DE", "cmaes": "vs CMA-ES", "restart-lbfgs": "vs restart-L-BFGS"}
    y = np.arange(len(rivals))
    ah = [100 * A2["small_study_verdicts"][r]["QI ahead"] / A2["n_studies"] for r in rivals]
    ti = [100 * A2["small_study_verdicts"][r]["tie"] / A2["n_studies"] for r in rivals]
    be = [100 * A2["small_study_verdicts"][r]["QI behind"] / A2["n_studies"] for r in rivals]
    ax1.barh(y, ah, color=C_QPSO, height=.55, label="reports QI ahead")
    ax1.barh(y, ti, left=ah, color="#bfbfbf", height=.55, label="reports tie")
    ax1.barh(y, be, left=np.array(ah) + np.array(ti), color=C_RESTART, height=.55,
             label="reports QI behind")
    ax1.set_yticks(y); ax1.set_yticklabels([lbl[r] for r in rivals], fontsize=7)
    ax1.set_xlabel("% of reconstructed small studies"); ax1.set_xlim(0, 100)
    ax1.set_title("choice of baseline", fontsize=8)
    ax1.legend(fontsize=5.6, loc="lower left", framealpha=.95)
    ax1.invert_yaxis()

    # phai: theo vi tri sang
    mixes = [("toan don cuc tri", "all 4 unimodal"), ("hon hop", "mixed"),
             ("toan da cuc tri", "all 4 multimodal")]
    y = np.arange(len(mixes))
    v = [A2["verdict_by_mix"][k] for k, _ in mixes]
    tot = [max(1, sum(x.values())) for x in v]
    ah = [100 * x["QI ahead"] / t for x, t in zip(v, tot)]
    ti = [100 * x["tie"] / t for x, t in zip(v, tot)]
    be = [100 * x["QI behind"] / t for x, t in zip(v, tot)]
    ax2.barh(y, ah, color=C_QPSO, height=.55)
    ax2.barh(y, ti, left=ah, color="#bfbfbf", height=.55)
    ax2.barh(y, be, left=np.array(ah) + np.array(ti), color=C_RESTART, height=.55)
    for i, (a, t_, b) in enumerate(zip(ah, ti, be)):
        for val, off in ((a, a / 2), (t_, a + t_ / 2), (b, a + t_ + b / 2)):
            if val > 8:
                ax2.text(off, i, "%.0f%%" % val, ha="center", va="center", fontsize=6.4,
                         color="white" if val > 25 else "#333")
    ax2.set_yticks(y); ax2.set_yticklabels([e for _, e in mixes], fontsize=7)
    ax2.set_xlabel("% of reconstructed small studies"); ax2.set_xlim(0, 100)
    ax2.set_title("where the study screened", fontsize=8)
    ax2.invert_yaxis()
    fig.savefig(os.path.join(OUT, "fig4-underpowered.pdf"))
    plt.close(fig)


def tab_methods(nums):
    """⭐ Bang DU BON phuong phap. Cong check_headline_baseline_coverage bat duoc rang abstract
    noi "so bon bo giai" nhung bang ket qua chi trinh bay HAI. Doi thu manh phai NHIN THAY duoc,
    khong chi nam trong du lieu."""
    names = ["qpso", "cmaes", "de", "restart-lbfgs"]
    pretty = {"qpso": "QI particle swarm", "cmaes": "CMA-ES",
              "de": "Differential evolution", "restart-lbfgs": "Restart L-BFGS-B"}
    tex = ["\\begin{tabular}{lrrr}", "\\toprule",
           "method & best or tied & mean rank & median seed s.d. \\\\", "\\midrule"]
    ranks = {n: [] for n in names}
    best = {n: 0 for n in names}
    sds = {n: [] for n in names}
    for c in D["methods"]:
        vals = {n: c["methods"][n]["mean"] for n in names}
        top = max(vals.values())
        order = sorted(names, key=lambda n: -vals[n])
        for i, n in enumerate(order):
            ranks[n].append(i + 1)
        for n in names:
            best[n] += vals[n] >= top - 1e-9
            sds[n].append(c["methods"][n]["std"])
    for n in names:
        tex.append("%s & %d/%d & %.2f & %.4f \\\\"
                   % (pretty[n], best[n], len(D["methods"]),
                      float(np.mean(ranks[n])), float(np.median(sds[n]))))
        nums["numBest%s" % n.replace("-", "").capitalize()] = best[n]
        nums["numRank%s" % n.replace("-", "").capitalize()] = "%.2f" % float(np.mean(ranks[n]))
    tex += ["\\bottomrule", "\\end{tabular}"]
    io.open(os.path.join(OUT, "tab3-methods.tex"), "w", encoding="utf-8").write("\n".join(tex))
    return nums


def tab_knobs(nums):
    """Yeu to nao sinh ra da cuc tri? Ti le o da cuc tri theo tung muc cua tung nut van."""
    rows = []
    for knob, key, vals in (("$K$", "K", KS), (r"$g_{\max}$", "gmax", GM),
                            (r"$\kappa$", "kappa", KA)):
        for v in vals:
            sub = [c for c in D["instance_space"] if c[key] == v]
            frac = 100.0 * sum(1 for c in sub if c["multimodal"]) / len(sub)
            rows.append((knob if v == vals[0] else "", ("%g" % v), len(sub), frac))
    tex = ["\\begin{tabular}{llrr}", "\\toprule",
           "knob & level & units & multimodal (\\%) \\\\", "\\midrule"]
    prev = None
    for knob, lvl, n, frac in rows:
        if knob and prev is not None:
            tex.append("\\midrule")
        tex.append("%s & %s & %d & %.0f \\\\" % (knob, lvl, n, frac))
        prev = knob or prev
    tex += ["\\bottomrule", "\\end{tabular}"]
    io.open(os.path.join(OUT, "tab2-knobs.tex"), "w", encoding="utf-8").write("\n".join(tex))
    # nut van nao co bien thien lon nhat
    spans = {}
    for key, vals, nm in ((("K"), KS, "K"), ("gmax", GM, "Gmax"), ("kappa", KA, "Kappa")):
        f = [100.0 * sum(1 for c in D["instance_space"] if c[key] == v and c["multimodal"])
             / max(1, len([c for c in D["instance_space"] if c[key] == v])) for v in vals]
        spans[nm] = max(f) - min(f)
        nums["numKnob%sLo" % nm] = "%.0f" % min(f)
        nums["numKnob%sHi" % nm] = "%.0f" % max(f)
    nums["numKnobStrongest"] = {"K": "K", "Gmax": "g_max", "Kappa": "kappa"}[
        max(spans, key=spans.get)]
    return nums


def a2_macros(nums):
    if not A2:
        return nums
    N = float(A2["n_studies"])
    nums["numStudies"] = "{:,}".format(A2["n_studies"]).replace(",", ".")
    nums["numStudyCells"] = A2["study_cells"]
    nums["numStudySeeds"] = A2["study_seeds"]
    for r, key in (("restart-lbfgs", "Restart"), ("cmaes", "Cmaes"), ("de", "De")):
        v = A2["small_study_verdicts"][r]
        nums["numSmall%sAhead" % key] = "%.1f" % (100 * v["QI ahead"] / N)
        nums["numSmall%sBehind" % key] = "%.1f" % (100 * v["QI behind"] / N)
        nums["numSmall%sTie" % key] = "%.1f" % (100 * v["tie"] / N)
    for mix, key in (("toan don cuc tri", "AllUni"), ("toan da cuc tri", "AllMulti")):
        v = A2["verdict_by_mix"][mix]
        t = float(max(1, sum(v.values())))
        nums["num%sTie" % key] = "%.1f" % (100 * v["tie"] / t)
        nums["num%sBehind" % key] = "%.1f" % (100 * v["QI behind"] / t)
        nums["num%sN" % key] = sum(v.values())
    return nums


if __name__ == "__main__":
    fig_map()
    fig_verdict()
    fig_effect_vs_noise()
    fig_underpowered()
    n = tables_and_macros()
    n = tab_methods(n)
    n = tab_knobs(n)
    n = a2_macros(n)
    io.open(os.path.join(OUT, "numbers.tex"), "w", encoding="utf-8").write(
        "".join("\\newcommand{\\%s}{%s}\n" % (k, v) for k, v in sorted(n.items())))
    print("  ✅ 3 hình · 1 bảng · %d macro" % len(n))
    for k in sorted(n):
        print("     %-22s %s" % (k, n[k]))
