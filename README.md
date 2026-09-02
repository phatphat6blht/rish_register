# Risk Register & Security Dashboard bằng Docker

## Đặt vấn đề

Hãy tưởng tượng bạn là nhân viên an toàn thông tin của một công ty phần mềm nhỏ. Sếp giao cho bạn nhiệm vụ:

> "Liệt kê hết tất cả rủi ro bảo mật mà công ty ta có thể gặp phải, đánh giá mức độ nguy hiểm, và theo dõi xem mình đã xử lý đến đâu."

Hệ thống **Risk Register (Sổ đăng ký rủi ro)** tự động và **Metabase Security Dashboard** triển khai bằng Docker Compose cho bài tập / báo cáo môn An toàn thông tin.

## 🚀 TỔNG QUAN KIẾN TRÚC

Hệ thống bao gồm 3 dịch vụ chính được cô lập trong Docker Network (`risk_network`):

1. **`postgres`**: CSDL PostgreSQL 16 Alpine lưu trữ toàn bộ mô hình dữ liệu (Asset, Threat, Vulnerability, Risk). CSDL được cô lập hoàn toàn, không expose cổng ra máy host.
2. **`flask_app`**: Ứng dụng Web Python Flask quản lý rủi ro, tự động tính Risk Score ($Score = Likelihood \times Impact$) & tự phân loại Risk Level (Critical, High, Medium, Low). Hỗ trợ lọc nâng cao và xuất báo cáo CSV/Excel.
3. **`metabase`**: Công cụ Metabase Dashboard trực quan hóa dữ liệu rủi ro. Kết nối tới CSDL thông qua tài khoản read-only (`metabase_readonly`) tuân thủ nguyên tắc Phân quyền tối thiểu (Least Privilege).

---

## 🛠️ HƯỚNG DẪN KHỞI CHẠY (QUICK START)

### 1. Tiền đề
- Đã cài đặt [Docker Desktop](https://www.docker.com/products/docker-desktop/) và đang chạy.

### 2. Khởi chạy hệ thống

Mở terminal tại thư mục dự án và chạy duy nhất lệnh sau:

```bash
docker compose up -d --build
```

### 3. Truy cập các ứng dụng

- **Ứng dụng Risk Register**: [http://localhost:5000](http://localhost:5000)
- **Metabase Security Dashboard**: [http://localhost:3000](http://localhost:3000)

---

## 📊 MÔ HÌNH DỮ LIỆU VÀ CÔNG THỨC TÍNH ĐIỂM

$$\text{Risk Score} = \text{Likelihood (1-5)} \times \text{Impact (1-5)}$$

| Mức Rủi Ro (Risk Level) | Khoảng Điểm (Risk Score) | Màu sắc hiển thị |
|---|---|---|
| **Critical** | $20 - 25$ | Đỏ |
| **High** | $12 - 19$ | Cam |
| **Medium** | $5 - 11$ | Vàng |
| **Low** | $1 - 4$ | Xanh lá |

---

## 🔒 KIỂM THỬ BẢO MẬT & NETWORK ISOLATION

1. **Network Boundary Isolation**: Thử kết nối từ máy Host vào CSDL qua port 5432 sẽ bị chặn (vì không expose port out host):
   ```bash
   psql -h localhost -p 5432 -U risk_user -d risk_db
   # Kết quả: Connection refused (Thành công chặn)
   ```
2. **Least Privilege for Metabase**: User `metabase_readonly` chỉ có quyền `SELECT`, không thể `INSERT/UPDATE/DELETE` dữ liệu.

---

## 🧹 DỌN DẸP HỆ THỐNG (CLEANUP)

Khi cần dừng hệ thống:
```bash
docker compose down
```

Nếu muốn xóa sạch toàn bộ dữ liệu volume:
```bash
docker compose down -v
```
