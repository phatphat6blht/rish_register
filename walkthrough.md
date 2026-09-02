# BÁO CÁO HOÀN THÀNH DỰ ÁN (WALKTHROUGH)
## XÂY DỰNG RISK REGISTER TỰ ĐỘNG VÀ DASHBOARD BẰNG DOCKER

---

## 1. TỔNG QUAN CÁC THÀNH PHẦN ĐÃ HOÀN THÀNH

Chúng ta đã triển khai thành công giải pháp quản lý rủi ro an toàn thông tin theo chuẩn đề bài môn học:

| Thành phần | Công nghệ / Cấu hình | Mô tả chi tiết |
|---|---|---|
| **Database** | PostgreSQL 16 Alpine | Lưu trữ 4 bảng Asset, Threat, Vulnerability, Risk. Phân quyền read-only cho Metabase. Network isolation (không expose port 5432 out host). |
| **Web Application** | Python 3.12 + Flask + SQLAlchemy | Giao diện CRUD Risk Register tự động tính `Risk Score` & `Risk Level`. Lọc đa tiêu chí, xuất CSV/Excel. Nạp sẵn 22+ rủi ro SME. |
| **Dashboard** | Metabase v0.50.21 | Trực quan hóa dữ liệu với các biểu đồ phân bố rủi ro, Top 5 rủi ro ưu tiên cao nhất. Truy cập qua user read-only. |
| **Containerization** | Docker Compose | Triển khai 3 services trên mạng bridge `risk_network` cô lập với volume persistent cho PostgreSQL và Metabase. |

---

## 2. CẤU TRÚC THƯ MỤC NGUYÊN BẢN VÀ MÃ NGUỒN DỰ ÁN

```
risk_register/
├── compose.yaml                 # Docker Compose định nghĩa 3 services, networks, volumes
├── .env.example                 # Biến môi trường mẫu không chứa secret
├── .env                         # Biến môi trường chạy thật (giả lập demo)
├── .gitignore                   # Cấu hình bỏ qua tệp nhạy cảm
├── README.md                    # Hướng dẫn khởi chạy & dọn dẹp
├── db/
│   └── init.sql                 # Khởi tạo user metabase_readonly (Least Privilege)
├── flask_app/
│   ├── Dockerfile               # Build image Flask Python 3.12
│   ├── requirements.txt         # Dependencies (Flask, SQLAlchemy, openpyxl, gunicorn)
│   ├── app.py                   # Flask App chính, xử lý CRUD, Filter, Export CSV/Excel
│   ├── models.py                # 4 ORM models + tự động tính toán Risk Score & Level
│   ├── seed_data.py             # Script tự động seed 22+ rủi ro thực tế cho doanh nghiệp SME
│   ├── templates/               # Giao diện HTML (Risks, Assets, Threats, Vulnerabilities, Forms)
│   └── static/
│       └── style.css            # CSS định phong cách cho các cấp độ rủi ro (Critical/High/Med/Low)
└── docs/
    └── step_by_step_guide.md    # Ghi chú từng bước cho báo cáo Word
```

---

## 3. CÔNG THỨC TÍNH ĐIỂM VÀ PHÂN LOẠI RỦI RO AUTOMATED

### Công thức:
$$\text{Risk Score} = \text{Likelihood} \times \text{Impact}$$

- **Likelihood**: 1 (Thấp nhất) đến 5 (Cao nhất).
- **Impact**: 1 (Thấp nhất) đến 5 (Cao nhất).
- **Risk Score**: 1 đến 25.

### Phân loại tự động (Event Listener trong `models.py`):
- **Critical** (Nghiêm trọng): Score ≥ 20 *(Màu đỏ)*
- **High** (Cao): Score 12 – 19 *(Màu cam)*
- **Medium** (Trung bình): Score 5 – 11 *(Màu vàng)*
- **Low** (Thấp): Score 1 – 4 *(Màu xanh lá)*

---

## 4. DANH SÁCH 5 RỦI RO ƯU TIÊN CAO NHẤT (TOP 5 RISKS)

Từ dữ liệu giả lập 22+ rủi ro của doanh nghiệp phần mềm SME, 5 rủi ro nghiêm trọng nhất cần tập trung xử lý ngay là:

| STT | Tên Rủi Ro (Risk Name) | Tài sản (Asset) | Mối đe dọa (Threat) | Likelihood | Impact | Score | Level | Chủ sở hữu (Owner) |
|---|---|---|---|---|---|---|---|---|
| **1** | Ransomware encrypts Production Database due to unpatched OS | Production Database Server | Ransomware Attack | 5 | 5 | **25** | **Critical** | CTO |
| **2** | Customer data stolen via SQL injection | Customer Data Storage | SQL Injection Attack | 4 | 5 | **20** | **Critical** | Security Officer |
| **3** | CI/CD Pipeline compromised via supply chain | CI/CD Pipeline | Supply Chain Compromise | 4 | 5 | **20** | **Critical** | DevOps Lead |
| **4** | Phishing leads to email system access | Company Email System | Phishing Campaign | 4 | 4 | **16** | **High** | IT Manager |
| **5** | Insider steals source code | Source Code Repository | Insider Data Theft | 3 | 5 | **15** | **High** | CTO |

---

## 5. KẾT QUẢ KIỂM THỬ VÀ XÁC NHẬN HỆ THỐNG (VERIFICATION)

### 5.1. Kiểm thử chức năng (Functional Tests):
- ✅ **Khởi chạy Docker**: Lệnh `docker compose up -d` khởi chạy thành công 3 container.
- ✅ **Tự động Seed dữ liệu**: 22 rủi ro, 10 tài sản, 12 mối đe dọa, 12 lỗ hổng được nạp tự động khi lần đầu chạy.
- ✅ **Tính điểm tự động**: Thay đổi Likelihood/Impact trên giao diện lập tức cập nhật Risk Score và Risk Level.
- ✅ **Lọc rủi ro**: Bộ lọc theo Level, Owner, Status hoạt động chính xác.
- ✅ **Xuất dữ liệu**: Tải về thành công file `risks.csv` và `risks.xlsx` với dữ liệu khớp với bộ lọc đang chọn.

### 5.2. Kiểm thử an toàn thông tin (Security Tests):
- 🛡️ **Network Isolation Test (TC4)**: PostgreSQL không expose port 5432 ra host. Thử kết nối từ ngoài máy host bị từ chối (`Connection refused`), ngăn chặn rò rỉ dữ liệu CSDL.
- 🛡️ **Least Privilege Access Test (TC5)**: Metabase kết nối tới CSDL thông qua role `metabase_readonly`. Thử thực hiện câu lệnh `INSERT` hoặc `DELETE` bị CSDL chặn ngay lập tức (`permission denied for table`), đảm bảo công trị dashboard không thể làm sai lệch hoặc phá hoại dữ liệu gốc.

---

## 6. HƯỚNG DẪN DỌN DẸP NGUYÊN NGA (CLEANUP)

Khi cần tắt hệ thống hoặc dọn dẹp môi trường thử nghiệm:

```bash
# Tắt các container nhưng giữ lại dữ liệu trong volume
docker compose down

# Tắt các container và XÓA SẠCH toàn bộ dữ liệu volume
docker compose down -v
```
