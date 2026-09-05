"""Sinh MOI hinh, bang va macro cua bai tu MOT nguon duy nhat: results/e1_protocol.json.

⛔ LUAT CUA BAI NAY: khong con so nao duoc go tay vao .tex. Moi con so di qua `out/numbers.tex`.
   Ly do da ghi trong so: 49% so trong mot bai truoc la go tay, va mot con so bi chep 12 lan.

⚠ Bo sinh nay KHONG duoc dinh nghia lai bat cu dai luong nao. No chi DOC va DINH DANG. Moi phep
   tinh khoa hoc nam trong code/e1_protocol.py.
"""

import io
import json
import os
import re

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

# Bo style NHA: paper-lab/transaction-figure-kit/results/make_results.py
# serif khop voi bai LaTeX · Type-42 nhung font · net manh deu · hatch de in den trang doc duoc
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["DejaVu Serif"],
    "mathtext.fontset": "dejavuserif",
    "font.size": 8.5, "legend.fontsize": 7,
    "axes.linewidth": 0.6, "axes.grid": False,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "lines.linewidth": 1.1,
    "pdf.fonttype": 42, "ps.fonttype": 42,
    "figure.dpi": 300, "savefig.bbox": "tight", "savefig.pad_inches": 0.02})


# =====================================================================
# ⛔ THEM 05/09/2026. Hao nhin ra bang mat: "sao co hinh tu dung luc nho, co hinh lon vay?"
# Do la that: co chu hieu dung cua sau hinh bai nay chay tu 7,5pt den 9,9pt, lech 24%.
#
# Nguyen nhan: `savefig.bbox="tight"` cat khung theo NOI DUNG, nen be rong tep ra KHAC be rong
# `figsize` da yeu cau, va khac nhau tung hinh tuy nhan truc dai ngan. Dua tat ca vao bai o
# \textwidth thi moi hinh bi co gian MOT HE SO KHAC NHAU.
#
# ⇒ Ghi lap lai cho toi khi be rong THAT bang be rong SE DUNG. Le phai gan nhu co dinh theo
#   inch nen `figw_moi = figw + (dich - do_duoc)` hoi tu sau vai vong.
def save_at(fig, path, target_w):
    got = None
    for _ in range(6):
        fig.savefig(path)
        blob = open(path, "rb").read()
        mm = re.findall(rb"/MediaBox\s*\[([^\]]*)\]", blob)
        if not mm:
            break
        x0, y0, x1, y1 = [float(v) for v in mm[0].split()]
        got = (x1 - x0) / 72.0
        if abs(got - target_w) < 0.005:
            break
        w, h = fig.get_size_inches()
        fig.set_size_inches(w + (target_w - got), h)
    print("     %-30s %.2f in (dich %.2f)" % (os.path.basename(path), got or -1, target_w))


# Be rong THAT se dung trong main.tex. LNCS textwidth = 4.80 in.
W_TEXT_LNCS = 4.80
TARGET = {"fig1-instance-space.pdf": W_TEXT_LNCS,
          "fig2-knobs.pdf": 0.47 * W_TEXT_LNCS,
          "fig3-per-unit.pdf": 0.49 * W_TEXT_LNCS,
          "fig4-effect-vs-seed-noise.pdf": 0.49 * W_TEXT_LNCS,
          "fig5-underpowered.pdf": W_TEXT_LNCS}
ACCENT, INK = "#2C6E9B", "#3A3F47"

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
    """Ban do instance space.

    ⛔ BA LOI CUA BAN TRUOC, tim ra khi ket xuat PNG va NHIN:
      1. nhan o spike dat o `i - 0.40` nen DE LEN o hang tren va bi cat.
      2. nhan ghi "spike 28/07": do la NGAY LAM VIEC NOI BO. Nguoi doc khong hieu, va bai nay
         review DOUBLE-BLIND nen mot moc thoi gian noi bo la chi tiet ro ri.
      3. khong co thang mau, nen sac do khong doc duoc neu khong nho chu n/3.
    ⇒ Nhan dua RA NGOAI luoi kem mui ten, doi chu sang ngon ngu nguoi doc hieu, va them thang mau.
    """
    fig, axes = plt.subplots(1, len(KA), figsize=(5.35, 1.92), sharey=True,
                             gridspec_kw={"wspace": 0.10})
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("m", [C_UNI, C_MULTI])
    im = None
    for ax, k in zip(axes, KA):
        M = np.array([[cell_frac(K, g, k) for g in GM] for K in KS])
        im = ax.imshow(M, cmap=cmap, vmin=0, vmax=1, aspect="auto")
        for i, K in enumerate(KS):
            for j, g in enumerate(GM):
                f = M[i, j]
                ax.text(j, i, "%d/3" % round(f * 3), ha="center", va="center",
                        fontsize=6.4, color="white" if f > 0.5 else "#333")
        # luoi mong giua cac o, de dem o bang mat
        ax.set_xticks(np.arange(-.5, len(GM), 1), minor=True)
        ax.set_yticks(np.arange(-.5, len(KS), 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=0.8)
        ax.tick_params(which="minor", length=0)
        ax.set_xticks(range(len(GM))); ax.set_xticklabels(["%.2f" % g for g in GM], fontsize=6.6)
        ax.set_yticks(range(len(KS))); ax.set_yticklabels([str(K) for K in KS], fontsize=6.6)
        ax.set_xlabel(r"$g_{\max}$", fontsize=7.5, labelpad=1.5)
        ax.set_title(r"$\kappa = %.2f$" % k, fontsize=7.5, pad=3)
        # ⭐ o ma mot lan sang don le da chon
        if any((K, g, k) == SPIKE for K in KS for g in GM):
            i0, j0 = KS.index(SPIKE[0]), GM.index(SPIKE[1])
            ax.add_patch(plt.Rectangle((j0 - .5, i0 - .5), 1, 1, fill=False,
                                       edgecolor="#cc2200", lw=1.6, zorder=5))
            # ⛔ KHONG dat chu trong hinh. Thu HAI lan deu va cham: lan dau nhan de len o hang
            # tren va bi cat, lan hai de len nhan truc g_max va so 0.30. Khung do da du noi bat
            # de tim ngay, va chu thich hinh da noi no la gi. Chu o day chi them mot vat can.
            # ⚠ Va lan go bo dau tien dung str.replace nhung chuoi khong khop nen no KHONG LAM
            # GI va cung khong bao loi; hinh van y nguyen. Sua tep thi phai doc lai de kiem.
    axes[0].set_ylabel("beams $K$", fontsize=7.5)
    cb = fig.colorbar(im, ax=axes, fraction=0.026, pad=0.012, ticks=[0, 1/3, 2/3, 1])
    cb.ax.set_yticklabels(["0/3", "1/3", "2/3", "3/3"], fontsize=6.2)
    cb.set_label("instances that are multimodal", fontsize=6.6, labelpad=2)
    cb.outline.set_linewidth(0.5)
    save_at(fig, os.path.join(OUT, "fig1-instance-space.pdf"), TARGET["fig1-instance-space.pdf"])
    plt.close(fig)


# ---------------------------------- Fig 2: yeu to nao sinh ra da cuc tri
def fig_knobs():
    """Ba nut van tren cung mot truc, de thay ngay rang kappa la buoc nhay chu khong phai doc."""
    fig, ax = plt.subplots(figsize=(2.18, 1.62))   # dat o 0,47 kho chu LNCS = 2,26 in
    styles = [(KS, "K", "$K$ (beams)", "o", "-", INK),
              (GM, "gmax", r"$g_{\max}$ (interference)", "s", "--", ACCENT),
              (KA, "kappa", r"$\kappa$ (distortion)", "^", "-", "#aa2d2d")]
    for vals, key, lab, mk, ls, col in styles:
        x = np.linspace(0, 1, len(vals))
        y = [100.0 * sum(1 for c in D["instance_space"] if c[key] == v and c["multimodal"])
             / max(1, len([c for c in D["instance_space"] if c[key] == v])) for v in vals]
        ax.plot(x, y, marker=mk, ls=ls, color=col, label=lab, markersize=4.2,
                markerfacecolor="white", markeredgewidth=1.0)
        # ⛔ Bo nhan gia tri tren tung diem: ba chuoi nam o cung vi tri x nen chung DE LEN NHAU
        # ("0.1" dinh vao "4", "0.30" dinh vao "8"). Muc cu the da co trong bang ngay canh hinh;
        # hinh nay chi de thay HINH DANG, tuc kappa la buoc nhay con hai cai kia la doc thoai.
    ax.set_xticks([]); ax.set_ylim(-8, 108)
    ax.set_xlabel("knob level, low to high", fontsize=7.5)
    ax.set_ylabel("multimodal units (\\%)", fontsize=7.2)
    ax.grid(True, axis="y", linewidth=0.3, alpha=0.35)
    ax.legend(frameon=False, loc="upper left")
    save_at(fig, os.path.join(OUT, "fig2-knobs.pdf"), TARGET["fig2-knobs.pdf"])
    plt.close(fig)


# ------------------------- Fig 3: TUNG don vi mot, thay vi cot chong
def fig_per_unit():
    """⭐ Ve TAT CA 144 don vi.

    ⛔ Ban truoc co hai loi chi thay khi NHIN: hai nhan "restart better" va "QI better" DINH
    VAO NHAU thanh mot chuoi vo nghia, va o chu giai DE LEN chinh cac diem hang unimodal.
    ⇒ Bo chu giai, dua so luong vao nhan truc y, va chi giu MOT nhan huong.
    """
    fig, ax = plt.subplots(figsize=(2.22, 1.62))
    rng = np.random.default_rng(7)
    counts = {}
    for lab, want, col, mk in (("unimodal", False, "#7f8c9b", "o"),
                               ("multimodal", True, ACCENT, "^")):
        xs, ys = [], []
        for c in D["methods"]:
            k = (c["K"], c["gmax"], c["kappa"], c["instance"])
            if MM.get(k) != want:
                continue
            xs.append(c["methods"]["qpso"]["mean"] - c["methods"]["restart-lbfgs"]["mean"])
            ys.append(rng.normal(0, 0.15) + (1 if want else 0))
        counts[want] = len(xs)
        ax.scatter(xs, ys, s=12, marker=mk, facecolors="none", edgecolors=col, linewidths=0.8)
    ax.axvline(0, color="#aa2d2d", lw=1.0, ls="--")
    lo, hi = ax.get_xlim()
    ax.set_xlim(lo, hi + (hi - lo) * 0.06)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["unimodal\n$n=%d$" % counts[False],
                        "multimodal\n$n=%d$" % counts[True]], fontsize=6.6)
    ax.set_ylim(-0.6, 1.65)
    ax.set_xlabel("QI minus restart L-BFGS", fontsize=7.2)
    ax.text(0.02, 0.965, "no unit lies to the right of zero", transform=ax.transAxes,
            fontsize=6.0, color="#aa2d2d", va="top")
    ax.grid(True, axis="x", linewidth=0.3, alpha=0.35)
    save_at(fig, os.path.join(OUT, "fig3-per-unit.pdf"), TARGET["fig3-per-unit.pdf"])
    plt.close(fig)


# ------------------------- Fig 4: hieu ung so voi nhieu seed, BA NHOM
def fig_effect_vs_noise():
    """⛔ Ban truoc la tan xa log-log trai 13 bac. Tren thang do MOI diem deu nam sat duong
    cheo, nen hinh trong nhu "hieu ung luon bang nhieu", tuc noi NGUOC voi so trung vi 0,27
    va 0,70. Hai nhan cung chong len nhau thanh chu vo nghia.
    ⇒ Doi sang BA NHOM dem duoc, hien du 144 don vi, khong dai luong nao khong xac dinh:
       hieu ung < nhieu seed · hieu ung >= nhieu seed · nhieu seed = 0 (ca hai tat dinh).
    """
    fig, ax = plt.subplots(figsize=(2.22, 1.62))
    cats = ["effect $<$\nseed spread", "effect $\\geq$\nseed spread",
            "seed spread\n$=0$"]
    vals = {False: [0, 0, 0], True: [0, 0, 0]}
    for c in D["methods"]:
        k = (c["K"], c["gmax"], c["kappa"], c["instance"])
        want = MM.get(k)
        a, b = c["methods"]["qpso"], c["methods"]["restart-lbfgs"]
        sd = max(a["std"], b["std"])
        if sd <= 1e-12:
            vals[want][2] += 1
        elif abs(a["mean"] - b["mean"]) / sd < 1.0:
            vals[want][0] += 1
        else:
            vals[want][1] += 1
    x = np.arange(len(cats)); w = 0.38
    ax.bar(x - w / 2, vals[False], w, color="#d9d5cc", edgecolor="#444", linewidth=0.5,
           label="unimodal", hatch="")
    ax.bar(x + w / 2, vals[True], w, color=ACCENT, edgecolor="#444", linewidth=0.5,
           label="multimodal", hatch="//")
    for xi, (u, m) in enumerate(zip(vals[False], vals[True])):
        for off, v in ((-w / 2, u), (w / 2, m)):
            if v:
                ax.text(xi + off, v + 1.5, str(v), ha="center", fontsize=6.2)
    ax.set_xticks(x); ax.set_xticklabels(cats, fontsize=6.3)
    ax.set_ylabel("units", fontsize=7.2)
    ax.set_ylim(0, max(max(vals[False]), max(vals[True])) * 1.24)
    ax.legend(fontsize=6.2, frameon=False, loc="upper right")
    ax.grid(True, axis="y", linewidth=0.3, alpha=0.35)
    save_at(fig, os.path.join(OUT, "fig4-effect-vs-seed-noise.pdf"), TARGET["fig4-effect-vs-seed-noise.pdf"])
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
        # ⛔ KHONG dung dau cham ngan nghin trong bai TIENG ANH: "20.000" doc thanh hai muoi
        # phay khong. Dau cach mong `\,` la quy uoc Springer va doc dung o moi ngon ngu.
        # Cong check_language chi do KY TU tieng Viet nen no khong thay quy uoc SO.
        "numBudget": "{:,}".format(D["budget"]).replace(",", "\\,"),
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
    # ⭐ KET QUA DANG BI GIAU: bao nhieu o moi phuong phap TAT DINH tren toan bo seed.
    # Ban truoc chi im lang loai cac o nay khoi hinh hieu-ung-voi-nhieu.
    for n in ("qpso", "cmaes", "de", "restart-lbfgs"):
        z = sum(1 for c in D["methods"] if c["methods"][n]["std"] <= 1e-12)
        nums["numDet%s" % n.replace("-", "").capitalize()] = z
        nums["numDet%sPct" % n.replace("-", "").capitalize()] = "%.0f" % (
            100.0 * z / len(D["methods"]))
    nums["numDropZeroSd"] = sum(
        1 for c in D["methods"]
        if max(c["methods"]["qpso"]["std"], c["methods"]["restart-lbfgs"]["std"]) <= 1e-12)
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
    # ⛔ Ban truoc de wspace mac dinh nen nhan truc cua bang PHAI de len cot cua bang TRAI,
    # va o chu giai nam tren mot cot. Tach hai bang ra va dua chu giai xuong duoi.
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.0, 2.05),
                                   gridspec_kw={"wspace": 0.62})

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
    ax1.legend(fontsize=6.0, frameon=False, ncol=3,
               loc="upper center", bbox_to_anchor=(1.05, -0.30))
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
    save_at(fig, os.path.join(OUT, "fig5-underpowered.pdf"), TARGET["fig5-underpowered.pdf"])
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
    nums["numStudies"] = "{:,}".format(A2["n_studies"]).replace(",", "\\,")
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
    fig_knobs()
    fig_per_unit()
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
