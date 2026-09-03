"""E1 — chay CA HAI ARM duoi MOT giao thuc, cho bai QAI-SAGIN @ AICON 2026.

VI SAO CO TEP NAY. Hai spike cu tra loi hai cau hoi roi nhau, o hai do phan giai khac nhau:

    spike_multimodal_sweep.py     48 o, 30 diem xuat phat, 3 thuc the  -> 24/48 o da cuc tri
    spike_qi_on_multimodal.py     CHI 4 cau hinh, CHI 5 seed           -> QI thua restart-LBFGS 12/12

Bai bao khong dung duoc o dang do, vi ba ly do:

  1. **5 seed la duoi chuan cua chinh nhom.** Bai `qi-insight` cua cung nhom dung **30 seed**. Bao
     mot con so voi 5 seed trong khi cong trinh truoc dung 30 la ha chuan cua chinh minh. Nang len 30.

  2. **4 cau hinh khong phai mot ban do.** Dong gop trung tam cua bai la INSTANCE SPACE: phan quyet
     ve mot phuong phap doi theo vi tri trong khong gian thuc the. Chi so sanh o 4 o thi khong ve
     duoc ban do, va lai lap dung loi ma bai nay di phe binh: ket luan tu MOT vung.

  3. **Chua bao gio in hieu ung so voi PHUONG SAI SEED.** Chenh lech tuyet doi giua hai phuong phap
     khong doc duoc neu khong biet cung do lech do bao nhieu chi vi doi seed.

⇒ Tep nay chay ARM A tren ca 48 o va ARM B tren ca 48 o, 30 seed, cung ngan sach 20.000 lan goi ham
  DEM TRONG HAM, roi ghi mot JSON duy nhat.

⚠ KHONG dinh nghia lai bai toan. Ham muc tieu, bo sinh thuc the va bon phuong phap duoc NHAP LAI tu
  `spike_qi_on_multimodal.py`. Chep tay lai se sinh ra hai dinh nghia cho cung mot dai luong, dung
  lop loi da ghi trong so.

⚠ DIEU KIEN DK2 cua to khai: KHONG duoc them ham chuan tong hop (Rastrigin, LeadingOnes...) vao day.
  Ngay khi them la bai nay thanh ban rut gon cua `qi-insight`.
"""

import io
import itertools
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# NHAP LAI, khong chep. Mot dinh nghia bai toan duy nhat.
import spike_qi_on_multimodal as S           # noqa: E402

S.BUDGET = int(os.environ.get("QIB_BUDGET", "20000"))

SEEDS = int(os.environ.get("QIB_SEEDS", "30"))       # khop chuan 30 seed cua qi-insight
N_INST = 3
N_STARTS = 30                                        # giong spike_multimodal_sweep
MIN_SPREAD = 1.0                                     # % sum-rate; duoi nguong nay la MOT luu vuc
WORKERS = int(os.environ.get("QIB_WORKERS", "40"))
OUT = os.path.join(HERE, "..", "results", "e1_protocol.json")

KS = (4, 8, 16, 32)
GMAXS = (0.10, 0.30, 0.60, 0.90)
# ⛔ PHAI GIU DUNG LUOI GOC (0,0 · 0,05 · 0,5) cua spike_multimodal_sweep.py. Ban dau toi doi
# thanh (0,0 · 0,25 · 0,50) va nhu the DA BO MAT dung gia tri kappa=0,05 ma spike 28/07 su dung,
# tuc bo mat O TRUNG TAM cua ca cau chuyen. Doi luoi cung lam so o da cuc tri lech khoi con so
# 24/48 da ghi trong so, va hai nguon noi khac nhau ve cung dai luong la mot lop loi rieng.
KAPPAS = (0.0, 0.05, 0.50)
CELLS = [(K, g, k) for K, g, k in itertools.product(KS, GMAXS, KAPPAS)]

LBFGS = {"maxiter": 20000, "maxfun": 200000, "ftol": 1e-14, "gtol": 1e-12}


# ---------------------------------------------------------------- ARM A: ban do instance space
def cell_multimodality(job):
    """Mot o cua ban do. Tra ve so luu vuc RIENG BIET tim duoc, va ba trang thai dem rieng.

    ⚠ BA THU KHONG duoc tinh la da cuc tri, vi moi thu deu che tao ra no:
      - luot co muc tieu KHONG huu han: bo giai dung o dau do, khong phai cuc tri dia phuong
      - luot KHONG hoi tu (cham tran lap): khong phai cuc tri dia phuong
      - hai nghiem cach nhau duoi MIN_SPREAD: do la nhieu hoi tu, khong phai luu vuc khac
    """
    K, gmax, kappa, inst = job
    P_tot = float(K)
    G = S.make_instance(100 + inst, K, gmax)
    f = S.Objective(G, P_tot, kappa)
    rng = np.random.default_rng(7000 + inst)
    vals, n_nonfinite, n_noconv = [], 0, 0
    for _ in range(N_STARTS):
        x0 = rng.uniform(0, P_tot / K * 2, size=K)
        r = minimize(lambda p: -f(p), x0, method="L-BFGS-B",
                     bounds=[(0, P_tot)] * K, options=LBFGS)
        v = -float(r.fun)
        if not np.isfinite(v):
            n_nonfinite += 1
            continue
        if not r.success:
            n_noconv += 1
            continue
        vals.append(v)
    basins = 0
    spread_pct = 0.0
    if vals:
        s = sorted(vals, reverse=True)
        best = s[0]
        keep = [best]
        for x in s[1:]:
            if all(abs(x - y) > MIN_SPREAD / 100.0 * abs(best) for y in keep):
                keep.append(x)
        basins = len(keep)
        spread_pct = 100.0 * (s[0] - s[-1]) / abs(s[0]) if abs(s[0]) > 0 else 0.0
    return {"K": K, "gmax": gmax, "kappa": kappa, "instance": inst,
            "basins": basins, "spread_pct": round(spread_pct, 3),
            "scored": len(vals), "nonfinite": n_nonfinite, "noconv": n_noconv,
            "multimodal": basins > 1}


# ---------------------------------------------------------------- ARM B: so sanh ngan sach khop
def cell_methods(job):
    """Mot o: chay ca bon phuong phap, SEEDS seed moi phuong phap, cung ngan sach goi ham."""
    K, gmax, kappa, inst = job
    P_tot = float(K)
    G = S.make_instance(100 + inst, K, gmax)
    out = {"K": K, "gmax": gmax, "kappa": kappa, "instance": inst,
           "unit_of_analysis": "cau-hinh-x-thuc-the", "methods": {}, "errors": 0}
    for name, fn in S.METHODS:
        vals = []
        for s in range(SEEDS):
            try:
                f = S.Objective(G, P_tot, kappa)
                vals.append(float(fn(f, K, P_tot, 1000 + s)))
            except Exception:                                    # noqa: BLE001
                out["errors"] += 1
        if vals:
            out["methods"][name] = {
                "mean": float(np.mean(vals)), "std": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
                "min": float(np.min(vals)), "max": float(np.max(vals)),
                "n": len(vals), "vals": [round(v, 6) for v in vals]}
    return out


def run(label, fn, jobs):
    t0 = time.time()
    print("  [%s] %d o x %d thuc the ..." % (label, len(CELLS), N_INST), flush=True)
    with Pool(WORKERS) as pool:
        res = pool.map(fn, jobs)
    print("     xong sau %.1f phut" % ((time.time() - t0) / 60.0), flush=True)
    return res


def main():
    jobs = [(K, g, k, i) for (K, g, k) in CELLS for i in range(N_INST)]
    print("  E1 — giao thuc thong nhat")
    print("  %d o · %d thuc the · %d seed · ngan sach %d lan goi ham · %d tien trinh\n"
          % (len(CELLS), N_INST, SEEDS, S.BUDGET, WORKERS))

    arm_a = run("ARM A · ban do instance space", cell_multimodality, jobs)
    arm_b = run("ARM B · so sanh ngan sach khop", cell_methods, jobs)

    # ⛔ CHAN: o loi khong duoc tinh la o hong. Xem feedback-cong-cu-hong-khong-phai-ket-qua-am.
    errs = sum(c["errors"] for c in arm_b)
    if errs:
        print("\n  ⛔ DUNG LAI: %d luot chay bi LOI. Khong ket luan tren du lieu nay." % errs)
        return 3

    # ---- A: ban do ----
    mm = [c for c in arm_a if c["multimodal"]]
    print("\n  ══ ARM A: ban do instance space ══")
    print("     %d/%d (o x thuc the) DA CUC TRI" % (len(mm), len(arm_a)))
    by_cell = {}
    for c in arm_a:
        by_cell.setdefault((c["K"], c["gmax"], c["kappa"]), []).append(c["multimodal"])
    cells_mm = sum(1 for v in by_cell.values() if any(v))
    print("     %d/%d O co it nhat mot thuc the da cuc tri" % (cells_mm, len(by_cell)))

    # ⭐ Ca trung tam cua bai: o ma spike 28/07 da chon, doi voi toan bo ban do
    # ⭐ O MA SPIKE 28/07 DA CHON. Day la ca trung tam cua bai: neu o nay don cuc tri trong khi
    # phan lon ban do da cuc tri, thi ket luan "giet huong" hoi 28/07 la mot tao tac cua VI TRI
    # sang, khong phai mot tinh chat cua lop bai toan.
    print("     ⭐ o spike 28/07 da chon: K=8, gmax=0,30, kappa=0,05")
    for c in sorted([c for c in arm_a if c["K"] == 8 and c["gmax"] == 0.30 and c["kappa"] == 0.05],
                    key=lambda x: x["instance"]):
        print("        thuc the #%d -> %d luu vuc, %s"
              % (c["instance"], c["basins"], "DA CUC TRI" if c["multimodal"] else "DON cuc tri"))

    # ---- B: so sanh, va hieu ung so voi PHUONG SAI SEED ----
    print("\n  ══ ARM B: so sanh ngan sach khop, %d seed ══" % SEEDS)
    names = [n for n, _ in S.METHODS]
    wins = {n: 0 for n in names}
    units = 0
    for c in arm_b:
        if len(c["methods"]) != len(names):
            continue
        units += 1
        best = max(c["methods"][n]["mean"] for n in names)
        for n in names:
            if c["methods"][n]["mean"] >= best - 1e-9:
                wins[n] += 1
    print("     don vi tot nhat: " + " · ".join("%s %d/%d" % (n, wins[n], units) for n in names))

    print("\n     QPSO doi voi tung doi thu (don vi = cau hinh x thuc the):")
    summary = {}
    for rival in [n for n in names if n != "qpso"]:
        d, ratio = [], []
        for c in arm_b:
            if "qpso" not in c["methods"] or rival not in c["methods"]:
                continue
            dm = c["methods"]["qpso"]["mean"] - c["methods"][rival]["mean"]
            d.append(dm)
            # ⭐ THUOC PHUONG SAI SEED: hieu ung phuong phap bang bao nhieu phan do lech do doi seed
            sd = max(c["methods"]["qpso"]["std"], c["methods"][rival]["std"])
            if sd > 1e-12:
                ratio.append(abs(dm) / sd)
        w = sum(1 for x in d if x > 1e-9)
        l = sum(1 for x in d if x < -1e-9)
        med_ratio = float(np.median(ratio)) if ratio else float("nan")
        summary[rival] = {"win": w, "tie": len(d) - w - l, "loss": l,
                          "mean_diff": float(np.mean(d)),
                          "median_effect_over_seed_sd": med_ratio}
        print("       vs %-14s thang %3d · hoa %3d · thua %3d   |  hieu ung / do lech seed = %.2f"
              % (rival, w, len(d) - w - l, l, med_ratio))

    doc = {"budget": S.BUDGET, "seeds": SEEDS, "n_inst": N_INST, "n_starts": N_STARTS,
           "min_spread_pct": MIN_SPREAD,
           "note": "ham muc tieu / thuc the / phuong phap NHAP LAI tu spike_qi_on_multimodal.py",
           "instance_space": arm_a, "methods": arm_b, "summary": summary,
           "cells_multimodal": cells_mm, "cells_total": len(by_cell)}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(doc, indent=1, ensure_ascii=False))
    print("\n  da ghi %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
