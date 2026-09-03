# Bai 1 @ QAI-SAGIN, AICON 2026
# Khai 03/09/2026, TRUOC khi chay thi nghiem. Ban 2 sau occupied-check.
#
# ⛔ BAN 1 DA BO. No khai bon dong gop kieu "chung toi de xuat ba phep sang", va occupied-check
# cho thay CA BA phep deu da co nguoi hinh thuc hoa:
#   - baseline khoi dong lai, ngan sach khop  -> arXiv 2509.08986, "Time-Fair Benchmarking for
#     Metaheuristics: A Restart-Fair Protocol" (2025), da hinh thuc hoa dung dieu do
#   - sang mot cau hinh la khong du            -> Instance Space Analysis (Smith-Miles), ca mot
#     phuong phap luan, va da ap len QAOA o arXiv 2401.08142
#   - thuoc phuong sai seed                    -> ca mot dong van lieu tai lap ML
# ⇒ Viet nhu "chung toi de xuat" la TU CHUOC LAY mot phan quyet dung. Ban nay doi sang dung cai
#   con trong: AP DUNG bo cong cu da co vao mot bai toan NTN that, va BAO CAO chuyen gi xay ra.
#   Tim kiem khong thay ai ap Instance Space Analysis vao toi uu hoa vien thong.

CLAIM: khi ap cac quy uoc danh gia da duoc hinh thuc hoa san (restart-fair benchmarking, instance
  space analysis, bao hieu ung so voi phuong sai seed) vao mot bai toan phan bo tai nguyen NTN
  that, phan quyet ve mot phuong phap quantum-inspired DAO CHIEU so voi cach danh gia dang duoc
  dung pho bien trong dong bai QI-cho-vo-tuyen

MEASUREMENT: bai toan cong suat beam nhieu nguoi dung. (1) instance space: quet 48 o (K 4..32,
  nhieu xuyen kenh 0,10..0,90, meo 0..0,5), 30 diem xuat phat, 3 thuc the moi o, hai nghiem tinh
  la khac o khi lech > 1% sum-rate. (2) restart-fair: ngan sach goi ham khop 20.000, dem TRONG
  ham, doi voi L-BFGS-B khoi dong lai, 5 seed, don vi phan tich la (cau hinh, thuc the). (3) bao
  hieu ung phuong phap nhu ti le cua hieu ung seed

IF NULL: neu phan quyet KHONG dao chieu, tuc QI van thang sau khi ap day du ba quy uoc, thi day
  la ket qua duong dau tien co giao thuc chat cho dong bai do, va bai van dung voi dung bo do va
  dung bo ma. Neu instance space cho ket qua dong deu tren moi o thi phan "mot cau hinh la khong
  du" mat hieu luc, nhung ban do instance space cua bai toan nay van la hien vat chua ai co

SURVIVES: yes

CONTRIBUTIONS:
  - [independent] LAN DAU ap Instance Space Analysis vao mot bai toan toi uu hoa vien thong;
    tim kiem 03/09/2026 khong thay ung dung nao trong vien thong, du ISA da duoc ap cho
    classification, regression, job shop, knapsack, max flow va QAOA
  - [independent] ban do instance space cua bai toan cong suat beam: hien vat dung lai duoc,
    cho biet vung nao da cuc tri va vung nao khong
  - [independent] bo ma chay lai duoc kem bai, phuc vu O3 cua workshop va lam hat giong cho
    artefact cong dong ma O4 da hua
  - [independent] mot ca ghi lai duoc ve viec sang o MOT diem van hanh dan toi ket luan nguoc:
    0/3 da cuc tri o mot cau hinh, 24/48 khi quet ca dai
  - [dependent] chieu cua ket qua: QI thang CMA-ES va DE nhung thua L-BFGS-B khoi dong lai 12/12

# =====================================================================
# OCCUPIED-CHECK BAI NHA, 03/09/2026 — quet 559 tep .tex trong hao-paper-2026
# =====================================================================
#
# ⛔ VA CHAM THAT, va la lan thu NAM: thu muc `qi-insight`.
#
#   qi-insight la mot bai HOAN CHINH (10 trang, IEEE TEVC full, DONE 30/07), da REJECT o TEVC va
#   nam trong nhom ba ban -revise da BO HAN. Abstract cua no:
#     - CHUNG MINH toan tu tim kiem QI chinh la EDA/ES o mot tham so hoa khac
#     - benchmark ngan sach tham so khop, 30 SEED
#     - ket qua: lich hoc cua QEA la co ich, nhung phan "luong tu" thuan tuy thi CO HAI
#     - doi voi CMA-ES co BIPOP, tuc da co baseline KHOI DONG LAI
#     - kho da phat hanh: github.com/haodpsut/qi-deflation-benchmark
#
# ⇒ Trung o: "QI doi voi co dien, ngan sach khop, nhieu seed, co restart". KHONG trung o: bai
#   toan (qi-insight dung HAM CHUAN tong hop LeadingOnes/Rastrigin; bai nay dung bai toan CONG
#   SUAT BEAM that), va khong trung o dong gop (qi-insight ban mot DINH LY tuong duong; bai nay
#   ban mot UNG DUNG cua instance space analysis).
#
# ✅ PHAN QUYET: TACH DUOC, nhung PHAI giu ba dieu kien duoi. Bo mot dieu kien la thanh tu dao
#    van chinh minh, hoac lap lai dung that bai da lam TEVC reject qi-insight.
#
#   DK1. Bai nay KHONG duoc nhac lai tuyen bo ly thuyet cua qi-insight ("QI la EDA"). Do la
#        tuyen bo da bi Platel-TEVC-2009 chiem truoc 17 nam va da giet qi-insight mot lan.
#   DK2. Bai nay phai chay tren BAI TOAN NTN THAT, khong duoc them ham chuan tong hop nao. Ngay
#        khi them Rastrigin vao la no thanh ban rut gon cua qi-insight.
#   DK3. Phai TRICH kho da phat hanh `qi-deflation-benchmark` nhu cong trinh truoc do cua nhom,
#        chu khong im lang. Kho do CONG KHAI tren GitHub nen phan bien tim ra duoc.
#
# ⚠ Chuan seed: qi-insight dung 30 seed, bo do beam-power hien chi co 5. Neu bai nay bao phuong
#   sai seed thi phai nang len cho khop chuan cao hon cua chinh nhom, khong duoc thap hon.
#
# Cac bai khac quet ra deu KHONG va cham: iotj-uav-charging-aoi (restart la tu khac nghia),
# qml-ntn-deflation (da bo), kan-wireless-research, csf-interp-trust-ids, qkd-industrial-sla.
