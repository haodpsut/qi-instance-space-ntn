# E1 — kết quả, 03/09/2026

Chạy trên VPS sol1, 40 tiến trình, `OMP_NUM_THREADS=1`.
**48 ô · 3 thực thể · 30 seed · ngân sách 20.000 lần gọi hàm đếm TRONG hàm · 0 lượt lỗi.**

Dữ liệu: `qi-beam-power/results/e1_protocol.json` · mã: `qi-beam-power/code/e1_protocol.py`

## ARM A — bản đồ instance space

- **24/48 ô** có ít nhất một thực thể đa cực trị (65/144 cặp ô × thực thể)
- ⭐ **Ô mà spike 28/07 đã chọn (K=8, gmax=0,30, kappa=0,05): ĐƠN cực trị cả 3/3 thực thể**

Tái lập chính xác cả hai con số cũ: 24/48 của bản quét, và 0/3 của spike.

## ARM B — so sánh ngân sách khớp, 30 seed

restart-L-BFGS tốt nhất ở **144/144** đơn vị. QPSO **không thắng nổi một đơn vị nào**.

## ⭐⭐ Phép giao: vị trí trong instance space DỰ ĐOÁN ĐƯỢC phán quyết

| nhóm ô | đơn vị | QPSO thắng | hoà | thua | hiệu ứng / độ lệch seed |
|---|---|---|---|---|---|
| **đơn cực trị** | 79 | 0 | **64** (81%) | 15 | 0,27 |
| **đa cực trị** | 65 | 0 | **1** (1,5%) | **64** (98%) | 0,70 |

**Đọc kết quả này cho đúng, vì nó ngược trực giác:**

Lập luận bán hàng của phương pháp quần thể là *"đa dạng giúp ích trên cảnh quan đa cực trị"*.
Dữ liệu nói **ngược**: đúng trên các ô đa cực trị thì QPSO **thua 98%**, còn trên các ô đơn cực
trị thì nó **hoà 81%**. Lý do hợp lý: đa cực trị là chỗ **khởi động lại** phát huy, vì nó lấy mẫu
nhiều lưu vực với chi phí rẻ, còn quần thể thì tiêu ngân sách vào việc duy trì đa dạng.

## Ba hệ quả cho bài

1. **Phán quyết phụ thuộc VỊ TRÍ SÀNG.** Spike 28/07 sàng đúng một ô, ô đó đơn cực trị, và kết
   luận "lớp bài toán này đơn cực trị" từ một điểm. Bản đồ nói 24/48 ô đa cực trị.
2. **Kết luận giết hướng vẫn ĐÚNG, nhưng vì lý do khác và mạnh hơn.** Không phải "không có gì để
   tìm", mà là **restart-L-BFGS tốt hơn hoặc bằng ở mọi ô, 144/144**.
3. **Mọi hiệu ứng đều NHỎ HƠN nhiễu seed** (tỉ số 0,27 và 0,70, đều dưới 1). Nhưng **chiều thì
   nhất quán tuyệt đối**: 0/144 lần QPSO thắng. ⇒ Nghiên cứu một seed trên lớp bài toán này
   **không phân giải được**, dù thứ tự là xác định.

Điểm 3 là luận cứ mạnh nhất cho một bài về giao thức đánh giá: hiệu ứng nhỏ hơn nhiễu **không có
nghĩa là không có hiệu ứng**, nó có nghĩa là **thiết kế thí nghiệm phải đủ mạnh để thấy**.
