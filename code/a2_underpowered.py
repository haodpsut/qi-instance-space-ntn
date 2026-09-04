"""A2 — MOT NGHIEN CUU CO THONG THUONG SE KET LUAN GI?

Day la phan tich, khong phai thi nghiem: no LAY MAU LAI tu results/e1_protocol.json chu khong
chay them luot nao. Vi the no nam o code/ rieng, khong nam trong bo sinh hinh, va ghi JSON rieng.

⭐ VI SAO. Bai co mot tuyen bo trung tam: "vi tri sang quyet dinh ket luan". Cach chung minh manh
nhat khong phai lap luan, ma la DUNG LAI mot nghien cuu co thong thuong roi dem xem no ket luan
gi. Ta co du lieu day du (48 o x 3 thuc the x 30 seed), nen co the rut ra hang nghin "nghien cuu
nho" tu chinh do va nhin phan bo ket luan cua chung.

Mot nghien cuu co thong thuong trong dong bai QI-cho-vo-tuyen thuong la:
    4 cau hinh · 1 thuc the moi cau hinh · 5 seed
Do dung la kich thuoc cua spike 28/07 va cua rat nhieu bai da dang.

⚠ BA DIEU PHAI CAN THAN, neu khong phan tich nay se noi qua:
  1. Lay mau lai KHONG tao ra thong tin moi. No chi cho biet mot thiet ke NHO se thay gi neu su
     that dung nhu du lieu day du cua ta. Do la mot phat bieu ve DO PHAN GIAI cua thiet ke, khong
     phai ve the gioi.
  2. Phai lay mau CA HAI muc: chon o (vi tri sang) VA chon seed (nhieu lap lai). Chi lay mau seed
     thi bo mat dung cai bai muon noi.
  3. Phai bao ca truong hop ket luan DUNG chieu, khong chi truong hop sai. Neu 100% nghien cuu nho
     deu ket luan dung thi tuyen bo cua bai sup, va phai noi ra.
"""

import io
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "results", "e1_protocol.json")
OUT = os.path.join(HERE, "..", "results", "a2_underpowered.json")

N_STUDIES = 5000
STUDY_CELLS = 4          # so cau hinh mot nghien cuu nho thuong dung
STUDY_SEEDS = 5          # so seed mot nghien cuu nho thuong dung
RIVALS = ("restart-lbfgs", "cmaes", "de")


def main():
    D = json.load(io.open(SRC, encoding="utf-8"))
    mm = {(c["K"], c["gmax"], c["kappa"], c["instance"]): c["multimodal"]
          for c in D["instance_space"]}
    units = [c for c in D["methods"] if len(c["methods"]) == 4]
    for c in units:
        c["_mm"] = mm[(c["K"], c["gmax"], c["kappa"], c["instance"])]
    cells = sorted({(c["K"], c["gmax"], c["kappa"]) for c in units})
    by_cell = {k: [c for c in units if (c["K"], c["gmax"], c["kappa"]) == k] for k in cells}
    rng = np.random.default_rng(20260904)

    print("  A2 — mot nghien cuu %d cau hinh x %d seed se ket luan gi?" % (STUDY_CELLS, STUDY_SEEDS))
    print("  %d nghien cuu dung lai tu %d don vi day du\n" % (N_STUDIES, len(units)))

    # ---- 1. Su that tren du lieu DAY DU, de doi chieu ----
    truth = {}
    for r in RIVALS:
        w = sum(1 for c in units if c["methods"]["qpso"]["mean"] > c["methods"][r]["mean"] + 1e-9)
        l = sum(1 for c in units if c["methods"]["qpso"]["mean"] < c["methods"][r]["mean"] - 1e-9)
        truth[r] = {"win": w, "loss": l, "n": len(units),
                    "verdict": "QI ahead" if w > l else ("QI behind" if l > w else "tie")}
        print("  su that (30 seed, 144 don vi): QI vs %-14s thang %3d thua %3d  => %s"
              % (r, w, l, truth[r]["verdict"]))

    # ---- 2. Dung lai cac nghien cuu nho ----
    out = {r: {"QI ahead": 0, "QI behind": 0, "tie": 0} for r in RIVALS}
    region_mix = {"toan don cuc tri": 0, "toan da cuc tri": 0, "hon hop": 0}
    verdict_by_mix = {k: {"QI ahead": 0, "QI behind": 0, "tie": 0} for k in region_mix}

    for _ in range(N_STUDIES):
        pick = rng.choice(len(cells), size=STUDY_CELLS, replace=False)
        chosen = []
        for i in pick:
            grp = by_cell[cells[i]]
            chosen.append(grp[rng.integers(len(grp))])          # mot thuc the moi cau hinh
        n_mm = sum(1 for c in chosen if c["_mm"])
        mix = ("toan da cuc tri" if n_mm == len(chosen) else
               "toan don cuc tri" if n_mm == 0 else "hon hop")
        region_mix[mix] += 1
        for r in RIVALS:
            w = l = 0
            for c in chosen:
                idx = rng.choice(D["seeds"], size=STUDY_SEEDS, replace=False)
                a = float(np.mean([c["methods"]["qpso"]["vals"][i] for i in idx]))
                b = float(np.mean([c["methods"][r]["vals"][i] for i in idx]))
                w += a > b + 1e-9
                l += a < b - 1e-9
            v = "QI ahead" if w > l else ("QI behind" if l > w else "tie")
            out[r][v] += 1
            if r == "restart-lbfgs":
                verdict_by_mix[mix][v] += 1

    print("\n  Phan bo ket luan cua %d nghien cuu nho:" % N_STUDIES)
    print("  %-16s %11s %11s %8s" % ("doi thu", "QI ahead", "QI behind", "tie"))
    for r in RIVALS:
        t = sum(out[r].values())
        print("  %-16s %10.1f%% %10.1f%% %7.1f%%"
              % (r, 100 * out[r]["QI ahead"] / t, 100 * out[r]["QI behind"] / t,
                 100 * out[r]["tie"] / t))

    print("\n  ⭐ Ket luan phu thuoc VI TRI SANG (doi thu = restart-lbfgs):")
    print("  %-20s %7s %11s %11s %8s" % ("4 o roi vao", "so lan", "QI ahead", "QI behind", "tie"))
    for mix, n in region_mix.items():
        if not n:
            continue
        v = verdict_by_mix[mix]
        t = sum(v.values())
        print("  %-20s %7d %10.1f%% %10.1f%% %7.1f%%"
              % (mix, n, 100 * v["QI ahead"] / t, 100 * v["QI behind"] / t, 100 * v["tie"] / t))

    doc = {"n_studies": N_STUDIES, "study_cells": STUDY_CELLS, "study_seeds": STUDY_SEEDS,
           "full_data_units": len(units), "full_data_seeds": D["seeds"],
           "truth": truth, "small_study_verdicts": out,
           "region_mix": region_mix, "verdict_by_mix": verdict_by_mix}
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(doc, indent=1, ensure_ascii=False))
    print("\n  da ghi %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
